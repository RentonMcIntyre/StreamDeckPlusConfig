import json


STEP_SIZE = 1


with open('app_list.json') as json_file:
    data = json.load(json_file)

class Dial:
    def __init__(self, name, running_apps, pulse_client):
        """
        Initialize the object with the provided parameters.

        Parameters:
            name (str): The name of the object.
            apps (list): A list of apps associated with the object.
            all_app_names (list): A list of all app names.
            volume (int): The volume level of the object.
            muted (bool): A boolean indicating if the object is muted.
        """
        self.pulse_client = pulse_client
        self.name = name
        self.apps = [sink_input for app_name in data[self.name]['Apps'] for sink_input in running_apps if app_name == sink_input.proplist['application.name']]
        self.all_app_names = data[self.name]['Apps']
        self.volume = data[self.name]['Volume']
        self.muted = data[self.name]['Muted']

        self.volume_set(self.volume, True)
        self.set_muted(self.muted, True)
        self.pulse_client
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
            self.pulse_client.volume_set_all_chans(app, set_volume)
        self.update_volume_in_json()

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
            self.pulse_client.mute(app, self.muted)
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
            self.pulse_client.mute(app, self.muted)
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

    def update_volume_in_json(self):
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
            data[self.name]["Volume"] = self.volume
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()

