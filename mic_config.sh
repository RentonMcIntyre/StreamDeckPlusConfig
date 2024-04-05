#!/bin/bash

pactl load-module module-null-sink sink_name=fx

pactl load-module module-null-sink sink_name=micfx

pactl load-module module-loopback source=alsa_input.usb-Focusrite_Scarlett_Solo_USB_Y7ECT3N191E8A1-00.analog-stereo \
    sink=micfx sink_name=micfxloop latency_msec=20

pactl load-module module-loopback source=fx.monitor sink=micfx sink_name=fxLoop latency_msec=20

pactl load-module module-loopback source=fx.monitor sink=alsa_input.usb-Focusrite_Scarlett_Solo_USB_Y7ECT3N191E8A1-00.analog-stereo latency_msec=1 \
    sink_name=dacLoop latency_msec=20