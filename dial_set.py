"""
A class representing a collection of Dial objects, each managing
a specific category of apps and their volume/mute settings.
"""
from contextlib import suppress
import pulsectl_asyncio
import pulsectl

from dial import Dial

PULSE = pulsectl.Pulse('streamdeck_control')

class DialSet:
    """
    A class representing a collection of Dial objects, each managing
    a specific category of apps and their volume/mute settings.
    """
    def __init__(self):
        """
        Initializes the DialSet class.

        :return: None
        """
        apps = PULSE.sink_input_list()

        browserApps = Dial("Browser", apps, PULSE)
        musicApps = Dial("Music", apps, PULSE)
        gamesApps = Dial("Games", apps, PULSE)
        chatApps = Dial("Chat", apps, PULSE)
        dials = [browserApps, musicApps, gamesApps, chatApps]

        self.dials = dials

    async def monitor(self):
        """
        Asynchronously monitors for events related to sink input devices
        (e.g. new apps added, removed). When an event is detected, adds or
        removes apps from each Dial object in the DialSet accordingly.

        :return: None
        """
        async with pulsectl_asyncio.PulseAsync('event-printer') as pulse:
            async for event in pulse.subscribe_events('sink_input'):
               print(event)
               if event.facility == 'sink_input' and event.t == 'new':
                   self.add_apps()
               elif event.facility == 'sink_input' and event.t == 'remove':
                   self.remove_apps()

    def add_apps(self):
        """
        Adds apps to each Dial object in the DialSet.

        :return: None
        """
        for dial in self.dials:
            dial.add_apps(PULSE.sink_input_list())

    def remove_apps(self):
        """
        Removes apps from each Dial object in the DialSet.

        :return: None
        """
        for dial in self.dials:
            dial.remove_apps(PULSE.sink_input_list())

