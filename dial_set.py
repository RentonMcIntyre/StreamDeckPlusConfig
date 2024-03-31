import threading
from typing import List
import pulsectl

from dial import Dial

PULSE = pulsectl.Pulse('streamdeck_control')

class DialSet:
    def __init__(self):
        """
        Initializes the class with a list of dials. Sets the dials attribute with the provided list. 
        Sets the PULSE event mask to "sink_input" and sets the event callback to self.monitor. 
        Starts listening for PULSE events.
        """
        apps = PULSE.sink_input_list()

        browserApps = Dial("Browser", apps, PULSE)
        musicApps = Dial("Music", apps, PULSE)
        gamesApps = Dial("Games", apps, PULSE)
        chatApps = Dial("Chat", apps, PULSE)
        dials = [browserApps, musicApps, gamesApps, chatApps]

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
