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
import Queue
import time
from datetime import datetime as dt
import logging
from dadivity_constants import *
from pi_resources import *


ONE_YEAR_TIMEOUT = 365 * 24 * 60 * 60
BLOCK = True

class motion_sensor():
    def __init__(self, event_queue):
        self.q = event_queue
        self.motion_sensor_pin = MOTION_SENSOR_PIN
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.motion_sensor_pin, GPIO.IN)
        GPIO.add_event_detect(self.motion_sensor_pin, GPIO.RISING, callback=self.motion_detected)

    def motion_detected(self, pin):   # our interrupt handler
        self.q.put(self)

    def callback(self, per_hour_counters):
        hour = time.localtime().tm_hour
        per_hour_counters[hour] += 1
        return {"event" : MOTION_SENSOR_TRIPPED, "hour" : hour, "counter" : per_hour_counters[hour]}

########################################################################
#
# The rest is testing stuff
#
########################################################################

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    per_hour_counters =  [0] * 24
    event_queue = Queue.Queue()

    try:
        ms = motion_sensor(event_queue)

        while 1:
            event = event_queue.get(BLOCK, ONE_YEAR_TIMEOUT)  # needs some timeout to respond to keyboard interrupt
            event.callback(per_hour_counters)
            logging.debug(repr(per_hour_counters))

    finally:
        GPIO.cleanup()


