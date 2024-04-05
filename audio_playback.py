import threading
import pulsectl
import os
import pygame

PULSE = pulsectl.Pulse('audio_playback')


def init_playback_devices():
    os.system('pactl load-module module-null-sink sink_name=fx')
    os.system('pactl load-module module-null-sink sink_name=micfx')
    os.system('pactl load-module module-loopback source=alsa_input.usb-Focusrite_Scarlett_Solo_USB_Y7ECT3N191E8A1-00.analog-stereo sink=micfx sink_name=micfxloop latency_msec=20')
    os.system('pactl load-module module-loopback source=fx.monitor sink=micfx sink_name=fxLoop latency_msec=20')
    os.system('pactl load-module module-loopback source=fx.monitor sink=alsa_input.usb-Focusrite_Scarlett_Solo_USB_Y7ECT3N191E8A1-00.analog-stereo latency_msec=1 sink_name=dacLoop latency_msec=20')

def ready_playback_devices():
    sinkFx = next((sink for sink in PULSE.sink_list() if sink.name == 'fx'), None)
    sinkMicFx = next((sink for sink in PULSE.sink_list() if sink.name == 'micfx'), None)
    if not sinkFx or not sinkMicFx:
        init_playback_devices()
        sinkFx = next((sink for sink in PULSE.sink_list() if sink.name == 'fx'), None)
        sinkMicFx = next((sink for sink in PULSE.sink_list() if sink.name == 'micfx'), None)

    # this is very specifically targetting discord right now and probably is not specific enough to avoid overlap elsewhere
    client = next((client for client in PULSE.source_output_list() if client.name == 'recStream'), None)
    if not client:
        print('FX client not setup, skipping')
        return
    os.system(f'pactl move-source-output {client.index} {sinkMicFx.index}')

    return sinkFx

def play_sample(sample, sinkFx, continuous=False):
    """
    A function that plays a sample sound with optional continuous playback.

    Parameters:
    - sample: a string representing the name of the sample sound file
    - sinkFx: the sink effect to use for the mixer initialization
    - continuous: a boolean indicating whether to play the sample continuously (default is False)
    """

    pygame.init()
    pygame.mixer.init(devicename=sinkFx.description)
    pygame.mixer.music.load('Assets/Sounds/' + sample + '.wav')
    play_count = -1 if continuous else 0
    pygame.mixer.music.play(play_count)


def init_play(sample, volume=100, continuous=False):
    """
    Readies the playback devices and plays the sample.
    Parameters:
        sample (str): The sample to be played.
        volume (int): The volume level for playback (default is 100).
    Returns:
        None
    """
    sinkFx = ready_playback_devices()
    if not sinkFx:
        return

    try:
        # mute mic while playing, won't do well with a mic that is not the default source
        if continuous:
            os.system('pactl set-source-mute @DEFAULT_SOURCE@ 1')

        PULSE.volume_set_all_chans(sinkFx, volume / 100.0)
        thread = threading.Thread(target=play_sample, args=(sample, sinkFx, continuous))
        thread.start();
        
    except Exception as e:
        print(e)
        print('Failed to play sample, does it exist in Assets/Sounds?')

def stop_continuous_sample():
    """
    A function to stop playing the sample with pygame and OS.
    """
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
    os.system('pactl set-source-mute @DEFAULT_SOURCE@ 0')

def mic_mute_toggle():
    """
    Toggles the mute state of the microphone.
    """
    os.system('pactl set-source-mute @DEFAULT_SOURCE@ toggle')
    

