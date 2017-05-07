#!/usr/bin/python2

""" An activity monitor.

Monitors the activity as detected by a motion sensor.  Keeps track of the
activity for each hour of a day.  Emails a summary of activity.

There is also a button on the device to send an email message immediately.

Serves a web page which displays recent activity.

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
import threading
import Queue
import dadivity_config
from dadivity_constants import *
from motion_sensor import Motion_Sensor
from button_sensor import Button_Sensor
from button_email import Button_Email
from event_monitor import Event_Monitor
from status_web_server import Status_Web_Server
import datetime
import time
from per_hour_counters import Per_Hour_Counters
from hourly_event_generator import Hourly_Event_Generator_Thread
from email_motion_report import Email_Motion_Report
try:
    import RPi.GPIO as GPIO
except ImportError:
    import mock_GPIO as GPIO     # to test code when not on a Pi

import logging
# debugging stuff, normally commented out.
#from pudb import set_trace; set_trace()

BLOCK = True
ONE_YEAR_TIMEOUT = 365 * 24 * 60 * 60

class Dadivity():

    """ The main (root) class for the activity monitor. """

    def __init__(self, test_flags=[]):
        self.test_flags    = test_flags
        self.event_queue   = Queue.Queue()
        self.counters      = Per_Hour_Counters()

        self.stop_hourly_tick_event = threading.Event()
        self.hourly_tick   = Hourly_Event_Generator_Thread(self.event_queue,
                                                           self.stop_hourly_tick_event,
                                                           test_flags=self.test_flags)
        self.motion_mailer = Email_Motion_Report(self.event_queue, test_flags=self.test_flags)
        self.motion_sense  = Motion_Sensor(self.event_queue)
        self.button_sense  = Button_Sensor(self.event_queue, test_flags=self.test_flags)
        self.button_email  = Button_Email(self.event_queue, test_flags=self.test_flags)
        self.event_monitor = Event_Monitor(self.counters, test_flags=self.test_flags)
        self.web_stats     = Status_Web_Server(self.event_monitor)

        # check to see if time is reasonable.  NTP may not have set the time
        # yet.  Don't wait forever though.
        for i in xrange(30):
            if datetime.datetime.now() > datetime.datetime(2015, 1, 1):
                break
            time.sleep(1)    # seconds

########################################################################
#
#              main()
#
########################################################################

    def main(self):

        """ Call this to start the program.
        
        Program is designed to run indefinately, so stop with control-c
        (or kill -9 ...).

        """

        try:

            # your basic event loop
            while True:

                # need some timeout value for the keyboard interrupt to work
                event = self.event_queue.get(BLOCK, ONE_YEAR_TIMEOUT)
                message = event.callback()
                self.event_queue.task_done()
                self.dispatch(message)

        except KeyboardInterrupt: pass

        finally:

            self.stop_hourly_tick_event.set()
            self.button_email.stop_any_pending_retries()
            self.motion_mailer.stop_any_pending_retries()
            self.web_stats.shutdown()
            GPIO.cleanup()

########################################################################
#
#                       dispatch(...)
#
########################################################################

    def dispatch(self, message):
        """ Deal with messages that came out of the queue.
        
        Args:
            message: a dictionary which has at least an entry for "event".
        """

        if DISPLAY_ACTIVITY in self.test_flags:

            print "dispatch, message:", dadivity_event_name[message["event"]]

        if message["event"] == HOUR_TICK:

            # first, is it time to send a motion summary email?
            if message["current_hour"] in dadivity_config.send_email_hour:
                update_msg = self.motion_mailer.send(self.counters.format_ascii_bar_chart())
                if DISPLAY_ACTIVITY in self.test_flags:
                    print "update message:", dadivity_event_name[message["event"]]
                logging.debug("update_msg: " + repr(update_msg))
                self.event_monitor.update(update_msg, self.counters)
            self.counters.new_hour(message["current_hour"])
            self.event_monitor.update(message, self.counters)

        elif message["event"] == RETRY_MOTION_EMAIL:

            update_msg = self.motion_mailer.retry()
            if DISPLAY_ACTIVITY in self.test_flags:
                print "update message:", dadivity_event_name[update_msg["event"]]
            logging.debug("update_msg: " + repr(update_msg))
            self.event_monitor.update(update_msg, self.counters)

        elif message["event"] == MOTION_SENSOR_TRIPPED:

            self.counters.motion_hit()
            self.event_monitor.update(message, self.counters)

        elif message["event"] == BUTTON_PRESSED:

            update_msg = self.button_email.send()
            if DISPLAY_ACTIVITY in self.test_flags:
                print "update message:", dadivity_event_name[update_msg["event"]]
            self.event_monitor.update(update_msg, self.counters)

########################################################################
#
# End of class Dadivity
#
########################################################################

if __name__ == '__main__':

    if 'test1' in sys.argv:
        logging.basicConfig(level=logging.DEBUG)
        Dadivity(test_flags=[FAST_MODE, DISPLAY_ACTIVITY, JUST_PRINT_MESSAGE]).main()

    elif 'test2' in sys.argv:
        logging.basicConfig(level=logging.DEBUG)
        Dadivity(test_flags=[DISPLAY_ACTIVITY, FAST_MODE, USE_MOCK_MAILMAN, FAST_RETRY, MOCK_ERROR]).main()

    elif 'test3' in sys.argv:
        logging.basicConfig(level=logging.DEBUG)
        Dadivity(test_flags=[DISPLAY_ACTIVITY]).main()

    else:
        Dadivity().main()

