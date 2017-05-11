#! /usr/bin/python

"""Detect when a button is pressed.

When a button is pressed, put reference to yourself in a queue.  On
callback, return a message.  Installs interrupt handler.
"""

"""
Copyright 2016 Don McLane

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import queue
from datetime import datetime as dt
import datetime
import logging
from dadivity_constants import *
from pi_resources import *

try:
    import RPi.GPIO as GPIO
except ImportError:
    import mock_GPIO as GPIO     # to test code when not on a Pi

ONE_YEAR_TIMEOUT = 365 * 24 * 60 * 60
BLOCK = True

class Button_Sensor(object):
    def __init__(self, event_queue, test_flags=[]):
        self._event_queue = event_queue
        self._test_flags = test_flags
        self._last_time = dt.now() - datetime.timedelta(hours=2)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(BEEPER_PIN_1, GPIO.OUT)
        GPIO.setup(BEEPER_PIN_2, GPIO.OUT)
        GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=self.button_press, bouncetime=500)

    def button_press(self, pin):
        """ Our interrupt handler. """
        self._event_queue.put(self)

    def callback(self):
        return {"event":BUTTON_PRESSED}

########################################################################
#
# The rest is testing stuff
#
########################################################################

if __name__ == "__main__":

#    from pudb import set_trace; set_trace()
    logging.basicConfig(level=logging.DEBUG)

    event_queue = queue.Queue()
    bs = Button_Sensor(event_queue, test_flags=[USE_MOCK_MAILMAN])

    try:

        while 1:
            event = event_queue.get(BLOCK, ONE_YEAR_TIMEOUT)  # needs some timeout to respond to keyboard interrupt
            update = event.callback()
            print(update)

    except KeyboardInterrupt: pass

    finally:
        GPIO.cleanup()

