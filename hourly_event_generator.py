#! /usr/bin/python

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

import time, sys
from datetime import datetime as dt
import datetime
import Queue
import threading
import dadivity_config
from dadivity_constants import *
from per_hour_counters import Per_Hour_Counters
import logging

BLOCK = True
ONE_YEAR_TIMEOUT = 365 * 24 * 60 * 60

class Hourly_Event_Generator_Thread(threading.Thread):
    """ Once an hour, put ourselves in the queue.
    """
    def __init__(self, event_queue, stop_event, test_flags=[]):
        threading.Thread.__init__(self)             # initialize our superclass
        self._event_queue = event_queue
        self._stopevent = stop_event
        self._test_flags = test_flags

        now = dt.now()
        self._current_hour = now.hour
        self._next_time = self.calc_next_time(now)
        self.start()

    def run(self):
        while not self._stopevent.isSet():
            # instead of time.sleep(...), use the timeout of the
            # threading.Event.wait(...) function, normally it should
            # just time out at about the right time, but when we stop
            # the thread, by setting stopevent, it should immediately return.
            self._stopevent.wait(self.seconds_until_next_time(self._next_time))
            if not self._stopevent.isSet():
                self._event_queue.put(self)
                now = dt.now()
                if FAST_MODE in self._test_flags:
                    self._current_hour = (self._current_hour + 1) % 24
                else:
                    self._current_hour = now.hour
                self._next_time = self.calc_next_time(now)

    def calc_next_time(self, now):
        next_time = now + datetime.timedelta(hours=1)
        next_time = next_time.replace(minute=0, second=0, microsecond=0)
        return next_time

    # This is called by a different thread.  Maybe we should put a lock
    # around _current_hour, but we know this is called after it's set.
    def callback(self):
        return {"event":HOUR_TICK, "current_hour":self._current_hour}

    def seconds_until_next_time(self, next_time):
        if FAST_MODE in self._test_flags:
            seconds_to_next_time = 5
        else:
            delta_to_next_time = next_time - dt.now()
            seconds_to_next_time = delta_to_next_time.total_seconds()
        return seconds_to_next_time

#######################################################################
#
# The rest is testing stuff
#
########################################################################
class mock_stop_event:
    def __init__(self):
        pass

    def wait(self, seconds):
        time.sleep(seconds)

    def isSet(self):
        return False

def dispatch(message):

    if message["event"] == HOUR_TICK:
        if message["current_hour"] in dadivity_config.send_email_hour:
            print "send email" 
        counters.new_hour(message["current_hour"])

    elif message["event"] == MOTION_SENSOR_TRIPPED:
        counters.motion_hit()

#    elif message["event"] == BUTTON_PRESSED:
#        pass


if __name__ == '__main__':

#    from pudb import set_trace; set_trace()
#    logging.basicConfig(level=logging.DEBUG)

    if 'test1' in sys.argv:
        hegt = Hourly_Event_Generator_Thread(Queue.Queue(), mock_stop_event())
        print dt.now()
        hegt.calc_next_time(dt.now())
        print hegt._next_time

    if 'test2' in sys.argv:
        print "starting", dt.now()
        event_queue = Queue.Queue()
        stop_event = threading.Event()
        hegt = Hourly_Event_Generator_Thread(event_queue, stop_event, test_flags=[FAST_MODE])
        hegt.start()
        counters = Per_Hour_Counters()
        try:
            # your basic event loop
            while True:
                # need some timeout for keyboard interrupt to work
                event_source = event_queue.get(BLOCK, ONE_YEAR_TIMEOUT)
                message = event_source.callback()
                event_queue.task_done()
                print dt.now()
                print message
                dispatch(message)
        except KeyboardInterrupt:
            pass
        finally:
            print counters.counters
            stop_event.set()



