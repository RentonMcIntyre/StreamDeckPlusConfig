import threading
from typing import List
import pulsectl
import json

PULSE = pulsectl.Pulse('stremdeck_control')
STEP_SIZE = 1

import json

def update_volume_in_json(app_type, new_volume):
    """
    A function to update the volume for a specific app type in a JSON file.

    Parameters:
    app_type (str): The type of the app to update.
    new_volume (float): The new volume value to set.

    Returns:
    None
    """
    with open('app_list.json', 'r+') as file:
        data = json.load(file)
        data[app_type]["Volume"] = new_volume
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()


class Dial:
    def __init__(self, name, apps, all_app_names, volume, muted):
        """
        Initialize the object with the provided parameters.

        Parameters:
            name (str): The name of the object.
            apps (list): A list of apps associated with the object.
            all_app_names (list): A list of all app names.
            volume (int): The volume level of the object.
            muted (bool): A boolean indicating if the object is muted.
        """
        self.name = name
        self.apps = apps
        self.all_app_names = all_app_names
        self.volume = volume
        self.muted = muted
        self.volume_set(self.volume, True)
        self.set_muted(self.muted, True)
        self.print_status()

    def get_volume(self):
        """
        Returns the current volume of the object.

        :return: An integer representing the current volume.
        """
        return self.volume

    def step(self, steps: int):
        """
        A function to update the volume by a specified number of steps.
        
        Args:
            steps (int): The number of steps to update the volume by.

        Returns:
            None
        """
        new_volume = self.volume + (STEP_SIZE * steps)
        self.volume_set(new_volume)

    def volume_set(self, new_volume: int, is_silent: bool = False):
        """
        Sets the volume of the audio player to the specified new volume level.

        Parameters:
            new_volume (int): The new volume level to set. It should be an integer between 0 and 100.

        Returns:
            None

        Raises:
            None

        Side Effects:
            - Updates the volume level of all the apps in the audio player.
            - Updates the volume level in the JSON file associated with the audio player.

        """
        self.volume = new_volume
        set_volume = max(0.0, min(1.5, new_volume / 100.0))
        for app in self.apps:
            PULSE.volume_set_all_chans(app, set_volume)
        update_volume_in_json(self.name, self.volume)

        if not is_silent:
            self.print_status()

    def set_muted(self, muted, is_silent: bool = False):
        """
        Set the muted status of the object.

        Parameters:
            muted (bool): The muted status to be set.

        Returns:
            None
        """
        self.muted = muted
        for app in self.apps:
            PULSE.mute(app, self.muted)
        if not is_silent:
            self.print_status()

    def mute(self):
        """
        Toggles the mute state of the application and updates the mute state of all associated apps.

        This function toggles the mute state of the application by inverting the value of the `muted` attribute. It then iterates over all the apps associated with the application and calls the `mute` method of the `PULSE` class, passing in the app and the updated mute state.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        self.muted = not self.muted
        for app in self.apps:
            PULSE.mute(app, self.muted)
        self.print_status()
    
    def print_status(self):
        print("Dial: " + self.name + " volume: " + str(self.volume) + " muted: " + str(self.muted))
        print("\tApps: " + str([app.proplist['application.name'] for app in self.apps]))

    def add_apps(self, running_apps):
        """
        Adds new apps to the list of running apps if they are not already present.
        
        Args:
            running_apps: A list of running apps to check and add.
        
        Returns:
            None
        """
        if len(self.apps) == len(self.all_app_names):
            return

        matching_apps = [sink_input for app_name in self.all_app_names for sink_input in running_apps if app_name == sink_input.proplist['application.name']]
        loaded_apps = [sink_input.proplist['application.name'] for sink_input in self.apps]

        not_loaded_apps = [app_name for app_name in self.all_app_names if app_name not in loaded_apps]
        to_add = [sink_input for app_name in not_loaded_apps for sink_input in running_apps if app_name == sink_input.proplist['application.name']]

        if len(to_add) > 0:
            self.apps.extend(to_add)   
            self.print_status()
    
    def remove_apps(self, running_apps):
        """
        Removes applications from the list of loaded applications if they are not currently running.

        Parameters:
            running_apps (list): A list of running applications.

        Returns:
            None
        """
        if len(self.apps) == 0:
            return

        running_app_names = [sink_input.proplist['application.name'] for app_name in self.all_app_names for sink_input in running_apps if app_name == sink_input.proplist['application.name']]
        loaded_apps = [sink_input.proplist['application.name'] for sink_input in self.apps]

        to_remove = [app_name for app_name in loaded_apps if app_name not in running_app_names]
        
        if len(to_remove) > 0:
            self.apps = [app for app in self.apps if app.proplist['application.name'] not in to_remove]
            self.print_status()

class DialSet:
    def __init__(self, dials: List[Dial]):
        """
        Initializes the class with a list of dials. Sets the dials attribute with the provided list. 
        Sets the PULSE event mask to "sink_input" and sets the event callback to self.monitor. 
        Starts listening for PULSE events.
        """
        self.dials = dials
        self.callback = None
        self.stopped = False
        self.monitor_thread = threading.Thread(target=self.monitor)
        self.monitor_thread.start()

    def __del__(self):
        """
        Destructor method for the class. Stops event listening.
        """
        PULSE.event_listen_stop()
    
    def monitor(self):
        while True:
            self.stopped = False
            PULSE.event_mask_set("all")
            PULSE.event_callback_set(self.check_event)
            PULSE.event_listen()
            self.callback()         

    def add_apps(self):
        for dial in self.dials:
            dial.add_apps(PULSE.sink_input_list())

    def remove_apps(self):
        for dial in self.dials:
            dial.remove_apps(PULSE.sink_input_list())

    def step(self, steps: int, dial: int):
        self.callback = lambda: self.dials[dial].step(steps)
        self.stopped = True
    
    def mute(self, dial: int):
        self.callback = lambda: self.dials[dial].mute()
        self.stopped = True

    def check_event(self, e: pulsectl.PulseEventInfo): 
        """
        Monitors the given PulseEventInfo object and performs actions based on the event type.
        
        Args:
            e (pulsectl.PulseEventInfo): The PulseEventInfo object to monitor.
        
        Returns:
            None
        
        If the event type is "new, it tells all dials to check for new apps.
        If the event type is "remove, it tells all dials to check for removed apps.
        """
        if self.stopped:
            raise pulsectl.PulseLoopStop
        
        if e.t == 'new':
            self.callback = self.add_apps
            raise pulsectl.PulseLoopStop

        if e.t == 'remove':
            self.callback = self.remove_apps
            raise pulsectl.PulseLoopStop

with open('app_list.json') as json_file:
    data = json.load(json_file)

def init_dial(app_type, running_apps) -> Dial:
    """
    Initializes a Dial object based on the provided app type and running apps.

    Args:
        app_type (str): The type of the app.
        running_apps (List[SinkInput]): A list of running apps.

    Returns:
        Dial: The initialized Dial object.

    Raises:
        KeyError: If the app type is not found in the data dictionary.

    Notes:
        - The function searches for matching apps in the running apps list based on the app names specified in the data dictionary.
        - The matching apps are filtered using a list comprehension.
        - The Dial object is created with the app type, matching apps, app names from the data dictionary, volume, and muted status from the data dictionary.
    """
    matching_apps = [sink_input for app_name in data[app_type]['Apps'] for sink_input in running_apps if app_name == sink_input.proplist['application.name']]
    return Dial(app_type, 
                matching_apps, 
                data[app_type]['Apps'],
                data[app_type]['Volume'], 
                data[app_type]['Muted'])


def get_dials() -> DialSet:
    """
    Get the list of applications, initialize different dials for Browser, Music, Games, and Chat categories, and return a DialSet object containing all the initialized dials.
    """
    apps = PULSE.sink_input_list()

    browserApps = init_dial("Browser", apps)
    musicApps = init_dial("Music", apps)
    gamesApps = init_dial("Games", apps)
    chatApps = init_dial("Chat", apps)
    dials = [browserApps, musicApps, gamesApps, chatApps]

    return DialSet(dials) 

def get_dial(index) -> Dial | None:
    """
    Retrieves a Dial object based on the given index.

    Parameters:
        index (int): The index of the dial to retrieve.

    Returns:
        Dial | None: The Dial object corresponding to the given index, or None if the index is invalid.
    """
    print("getting dial: " + str(index))
    apps = PULSE.sink_input_list()
    print("got apps: " + str(apps))

    if index == 0:
            print("browser")
            return init_dial("Browser", apps)
    if index == 1:
            print("music")
            return init_dial("Music", apps)
    if index == 2:
            print("games")
            return init_dial("Games", apps)
    if index == 3:
            print("chat")
            return init_dial("Chat", apps)

    return None

if __name__ == "__main__":
    dials = get_dials()
    print(PULSE.event_masks)
