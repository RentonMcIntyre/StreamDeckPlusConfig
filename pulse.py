from typing import List
import pulsectl
import json

PULSE = pulsectl.Pulse('stremdeck_control')
STEP_SIZE = 1

import json

def update_volume_in_json(app_type, new_volume):
    with open('app_list.json', 'r+') as file:
        data = json.load(file)
        data[app_type]["Volume"] = new_volume
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

class Dial:
    def __init__(self, name, apps, volume):
        self.name = name
        self.apps = apps
        self.volume = volume
        self.volume_set(self.volume)
    

    def step(self, steps: int):
        new_volume = self.volume + (STEP_SIZE * steps)
        print(new_volume)
        print(steps)
        self.volume_set(new_volume)
        print('stepping')
    def volume_set(self, new_volume: int):
        self.volume = new_volume
        new_volume = max(0, min(1, new_volume / 100))
        for app in self.apps:
            PULSE.volume_set_all_chans(app, new_volume)
        update_volume_in_json(self.name, self.volume)

with open('app_list.json') as json_file:
    data = json.load(json_file)

def init_dial(app_type, running_apps) -> Dial:
    matching_apps = [sink_input for app_name in data[app_type]['Apps'] for sink_input in running_apps if app_name == sink_input.proplist['application.name']]
    return Dial(app_type, matching_apps, data[app_type]['Volume'])

def set_dial(dial, volume):
    dial.volume_set(volume)

def get_dials() -> List[Dial]:
    apps = PULSE.sink_input_list()

    browserApps = init_dial("Browser", apps)
    musicApps = init_dial("Music", apps)
    gamesApps = init_dial("Games", apps)
    chatApps = init_dial("Chat", apps)

    return [browserApps, musicApps, gamesApps, chatApps]

def get_dial(index) -> Dial:
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
    dials[0].step(1)