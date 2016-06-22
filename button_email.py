
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

import RPi.GPIO as GPIO
import time
import sys
import Queue
from datetime import datetime as dt
import datetime
import logging
import send_email
import dadivity_config
from dadivity_constants import *
from pi_resources import *
from email_retry_manager import email_retry_manager

LOW_FREQUENCY = 800
HIGH_FREQUENCY = 1220
ONE_YEAR_TIMEOUT = 365 * 24 * 60 * 60
BLOCK = True

class button_email():
    def __init__(self, event_queue, test_flags=[]):
        self._event_queue = event_queue
        self._test_flags = test_flags
        self._last_time = dt.now() - datetime.timedelta(hours=2)
        self._email_retry_manager = email_retry_manager(self._event_queue, self._test_flags)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(BEEPER_PIN_1, GPIO.OUT)
        GPIO.setup(BEEPER_PIN_2, GPIO.OUT)
        GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=self.button_press, bouncetime=500)

    def button_press(self, pin):   # our interrupt handler
        self._event_queue.put(self)

    def stop_the_inner_thread(self):
        # it could have Timer threads running
        self._email_retry_manager.reset()

    def callback(self, per_hour_counters):
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

        for i in xrange(freq):
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

    per_hour_counters =  [0] * 24
    event_queue = Queue.Queue()

    try:
        be = button_email(event_queue, test_flags=[USE_MOCK_MAILMAN])

        while 1:
#            event = event_queue.get(BLOCK, ONE_YEAR_TIMEOUT)  # needs some timeout to respond to keyboard interrupt
            event = event_queue.get(BLOCK, 10)  # seconds
            update = event.callback(per_hour_counters)
            logging.debug(repr(update))

    finally:
        pass

if __name__ == "__main__":

#    from pudb import set_trace; set_trace()
    try:
        if 'beep1' in sys.argv:
            button_email(Queue.Queue()).beep(LOW_FREQUENCY)
        elif 'beep2' in sys.argv:
            button_email(Queue.Queue()).beep(HIGH_FREQUENCY)
        elif 'beep3' in sys.argv:
            be = button_email(Queue.Queue())
            for i in xrange(400, 3000, 20):
                print i
                be.beep(i)
        else:
            debug_main()
    finally:
        GPIO.cleanup()

