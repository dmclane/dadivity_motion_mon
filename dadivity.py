#!/usr/bin/python2
""" dad activity monitor

Monitors the activity as detected by a motion sensor.  Keeps track of the activity for each hour of a day.
Emails a daily summary of activity.

There is also a button on the device to send an email message immediately.

Configuration is done in the file dadivity_config.py
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

import sys
import Queue
import RPi.GPIO as GPIO
import dadivity_config
from dadivity_constants import *
from daily_email import send_daily_email_summary
from motion_sensor import motion_sensor
from button_email import button_email
from event_monitor import event_monitor
from status_web_server import status_web_server
import datetime
import time

# debugging stuff, normally commented out.
#from pudb import set_trace; set_trace()
import logging
logging.basicConfig(level=logging.DEBUG)

BLOCK = True
ONE_YEAR_TIMEOUT = 365 * 24 * 60 * 60

########################################################################
#
# Main program
#
########################################################################

def dadivity(test_flags=[]):
    per_hour_counters = [0] * 24

    # check to see if time is reasonable.  NTP may not have set the time
    # yet.  Don't wait forever though.
    for i in xrange(30):
        if datetime.datetime.now() > datetime.datetime(2015, 1, 1):
            break
        time.sleep(1)    # seconds

    event_queue = Queue.Queue()
    emailer = send_daily_email_summary(event_queue, test_flags)
    motion_sense = motion_sensor(event_queue)
    button_send = button_email(event_queue, test_flags)
    event_mon = event_monitor(per_hour_counters)
    web_stats = status_web_server(event_mon)
    web_stats.start()

    try:
        # your basic event loop
        while True:
            # need some timeout for keyboard interrupt to work
            event = event_queue.get(BLOCK, ONE_YEAR_TIMEOUT)
            update = event.callback(per_hour_counters)
            event_queue.task_done()
#            if DISPLAY_ACTIVITY in test_flags:
            event_mon.update(update, per_hour_counters)
    finally:
        emailer.stop_the_inner_thread()
        button_send.stop_the_inner_thread()
        web_stats.shutdown()
        GPIO.cleanup()

if __name__ == '__main__':

    if 'test1' in sys.argv:
        # remember to import logging and set level=logging.DEBUG
        print 'test1'            # you'll probably want to kill with cntrl-C
        dadivity(test_flags=[QUEUE_DAILY_EMAIL_IMMEDIATELY, USE_MOCK_MAILMAN])

#    elif 'test2' in sys.argv:    # prints out stuff in a convenient format.
#        dadivity(test_flags=[DISPLAY_ACTIVITY])

    elif 'test3' in sys.argv:
        dadivity(test_flags=[DISPLAY_ACTIVITY, FAST_MODE,
                             USE_MOCK_MAILMAN, MOCK_ERROR])

    else:
        dadivity()
