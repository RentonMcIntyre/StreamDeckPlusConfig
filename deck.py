#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#

# Example script showing some Stream Deck + specific functions

import asyncio
from contextlib import suppress
import os
import random
import signal
import threading
import io

from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices.StreamDeck import DialEventType, TouchscreenEventType

from dial_set import DialSet


# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")

# image for idle state
img = Image.new('RGB', (120, 120), color='black')
released_icon = Image.open(os.path.join(ASSETS_PATH, 'Released.png')).resize((80, 80))
img.paste(released_icon, (20, 20), released_icon)

img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_released_bytes = img_byte_arr.getvalue()

# image for pressed state
img = Image.new('RGB', (120, 120), color='black')
pressed_icon = Image.open(os.path.join(ASSETS_PATH, 'Pressed.png')).resize((80, 80))
img.paste(pressed_icon, (20, 20), pressed_icon)

img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_pressed_bytes = img_byte_arr.getvalue()

dialset = DialSet()

# callback when buttons are pressed or released
def key_change_callback(deck, key, key_state):
    print("Key: " + str(key) + " state: " + str(key_state))

    deck.set_key_image(key, img_pressed_bytes if key_state else img_released_bytes)


# callback when dials are pressed or released
def dial_change_callback(deck, dial, event, value):
    if event == DialEventType.PUSH:
        dialset.dials[dial].mute();
    elif event == DialEventType.TURN:
        dialset.dials[dial].step(value)


# callback when lcd is touched
def touchscreen_event_callback(deck, evt_type, value):
    if evt_type == TouchscreenEventType.SHORT:
        print("Short touch @ " + str(value['x']) + "," + str(value['y']))

    elif evt_type == TouchscreenEventType.LONG:

        print("Long touch @ " + str(value['x']) + "," + str(value['y']))

    elif evt_type == TouchscreenEventType.DRAG:

        print("Drag started @ " + str(value['x']) + "," + str(value['y']) + " ended @ " + str(value['x_out']) + "," + str(value['y_out']))


async def init():
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        # This example only works with devices that have screens.

        if deck.DECK_TYPE != 'Stream Deck +':
            print(deck.DECK_TYPE)
            print("Sorry, this example only works with Stream Deck +")
            continue

        deck.open()
        deck.reset()

        deck.set_key_callback(key_change_callback)
        deck.set_dial_callback(dial_change_callback)
        deck.set_touchscreen_callback(touchscreen_event_callback)

        print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))

        # Set initial screen brightness to 30%.
        deck.set_brightness(100)

        for key in range(0, deck.KEY_COUNT):
            deck.set_key_image(key, img_released_bytes)

        # build an image for the touch lcd
        img = Image.new('RGB', (800, 100), 'black')
        icon = Image.open(os.path.join(ASSETS_PATH, 'Exit.png')).resize((80, 80))
        img.paste(icon, (690, 10), icon)

        for dial in range(0, deck.DIAL_COUNT - 1):
            img.paste(released_icon, (30 + (dial * 220), 10), released_icon)

        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        touchscreen_image_bytes = img_bytes.getvalue()

        deck.set_touchscreen_image(touchscreen_image_bytes, 0, 0, 800, 100)



async def random_task():
    #sleep for 5 seconds and then print a random number
    while True:
        await asyncio.sleep(1)
        print(random.randint(0, 100))

async def main():
    init_task = asyncio.create_task(init())
    monitor_task = asyncio.create_task(dialset.monitor())    

    main_loop = asyncio.gather(init_task, monitor_task)

    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        loop.add_signal_handler(sig, main_loop.cancel)

    with suppress(asyncio.CancelledError):
        await main_loop

loop = asyncio.get_event_loop()
loop.run_until_complete(main())