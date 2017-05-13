#! /usr/bin/python3

""" Send email, not more often than once per hour, retry if necessary.

Content of email, address, etc. are configured in dadivity_config.py.
Email frequency is limited to once per hour.  A high frequency tone
confirms the button press.  Subsequent button presses within an hour
produce a low frequency tone.

"""

## @copyright 2016 Don McLane
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import sys
import queue
from datetime import datetime as dt
import datetime
import logging
import send_email
import dadivity_config
from dadivity_constants import *
from pi_resources import *
from email_retry_manager import Email_Retry_Manager
import per_hour_counters

try:
    import RPi.GPIO as GPIO
except ImportError:
    import mock_GPIO as GPIO     # to test code when not on a Pi

LOW_FREQUENCY = 800                     # Hz.
HIGH_FREQUENCY = 1220                   # Hz.
BEEP_LENGTH = .25                       # seconds
ONE_YEAR_TIMEOUT = 365 * 24 * 60 * 60   # seconds
BLOCK = True

class Button_Email(object):

    def __init__(self, queue, test_flags=[]):

        self._test_flags = test_flags
        self._email_retry_manager = Email_Retry_Manager(queue, test_flags=test_flags)
        self._last_time = dt.now() - datetime.timedelta(hours=2)

    def stop_any_pending_retries(self):

        # it could have Timer threads running
        self._email_retry_manager.reset()

    def send(self):

        # only allow one email per hour
        within_an_hour = (dt.now() - self._last_time) < datetime.timedelta(hours=1)

        email_error = None
        if within_an_hour:
            self.beep(LOW_FREQUENCY)
        else:
            self.beep(HIGH_FREQUENCY)

            email_error = send_email.dadivity_send(
                                      dadivity_config.button_subject,
                                      dadivity_config.button_message,
                                      self._test_flags)
            self._last_time = dt.now()

        if email_error != None:
            self._email_retry_manager.start_retrying(
                                     dadivity_config.button_subject,
                                     dadivity_config.button_message)

        return {"event" : BUTTON_EMAIL_SENT,
                "within_an_hour" : within_an_hour,
                "email_error" : email_error}

    def beep(self, freq):

        period = 1.0 / freq
        half_period = period / 2.0

        for i in range(int(BEEP_LENGTH * freq)):
            # toggle two IO pins for more volume
            GPIO.output(BEEPER_PIN_1, True)
            GPIO.output(BEEPER_PIN_2, False)
            time.sleep(half_period)
            GPIO.output(BEEPER_PIN_1, False)
            GPIO.output(BEEPER_PIN_2, True)
            time.sleep(half_period)

########################################################################
#
# The rest is testing stuff
#
########################################################################

def debug_main():
    logging.basicConfig(level=logging.DEBUG)

    counters = per_hour_counters.Per_Hour_Counters()
    per_hour_counters.make_some_interesting_data(counters)
    event_queue = queue.Queue()
    be = Button_Email(event_queue, test_flags=[JUST_PRINT_MESSAGE])
    send_result = be.send()
    print("send_result:", send_result)

#    try:

#        while 1:
##            event = event_queue.get(BLOCK, ONE_YEAR_TIMEOUT)  # needs some timeout to respond to keyboard interrupt
#            event = event_queue.get(BLOCK, 10)  # seconds
#            update = event.callback(per_hour_counters)
#            logging.debug(repr(update))

#    finally:
#        pass

if __name__ == "__main__":

#    from pudb import set_trace; set_trace()

    try:

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BEEPER_PIN_1, GPIO.OUT)
        GPIO.setup(BEEPER_PIN_2, GPIO.OUT)

        if 'beep1' in sys.argv:

            # test the low frequency tone
            Button_Email(queue.Queue()).beep(LOW_FREQUENCY)

        elif 'beep2' in sys.argv:

            #test the high frequency tone
            Button_Email(queue.Queue()).beep(HIGH_FREQUENCY)

        elif 'beep3' in sys.argv:

            # sweep tone frequency to determine which tones sound best
            be = Button_Email(queue.Queue())
            for i in range(400, 3000, 20):
                print(i)
                be.beep(i)

        else:

            debug_main()

    finally:

        GPIO.cleanup()

