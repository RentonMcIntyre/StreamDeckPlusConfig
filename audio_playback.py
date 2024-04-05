import re
from time import sleep
import pulsectl
import os

PULSE = pulsectl.Pulse('audio_playback')

def add_sounds():
    for file in os.listdir('Assets/Sounds'):
        if str.endswith(file, '.wav'):
            os.system(f"pactl upload-sample Assets/Sounds/{file} {file.split('.')[0]}")

def play_sample(sample, blocking=False, volume=100):
    sinkFx = next((sink for sink in PULSE.sink_list() if sink.name == 'fx'), None)
    if not sinkFx:
        print('Mic FX sink not setup, skipping')
    sinkMicFx = next((sink for sink in PULSE.sink_list() if sink.name == 'micfx'), None)
    if not sinkMicFx:
        print('Mic FX sink not setup, skipping')
    # this is very specifically targetting discord right now and probably is not specific enough to avoid overlap elsewhere
    client = next((client for client in PULSE.source_output_list() if client.name == 'recStream'), None)
    if not client:
        print('FX client not setup, skipping')
    os.system(f'pactl move-source-output {client.index} {sinkMicFx.index}')

    try:
        if blocking:
            # mute mic while playing, won't do well with a mic that is not the default source
            os.system('pactl set-source-mute @DEFAULT_SOURCE@ 1')
        PULSE.volume_set_all_chans(sinkFx, volume / 100.0)
        PULSE.play_sample(sample, sinkFx.index)
        sleep(30)
    except:
        print('Failed to play sample, does it exist in Assets/Sounds?')
    
    if blocking:
        os.system('pactl set-source-mute @DEFAULT_SOURCE@ 0')

if __name__ == '__main__':
    add_sounds()
    play_sample('bleep4', blocking=True, volume=50)