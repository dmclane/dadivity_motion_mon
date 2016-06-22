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
from pi_resources import *
import send_email
import logging
import smtplib
from email_retry_manager import email_retry_manager

try:
    import RPi.GPIO as GPIO
except ImportError:
    import mock_GPIO as GPIO     # to test code when not on a Pi

class daily_event_generator_thread(threading.Thread):
    """ Once a day, put something in a queue.
    """
    def __init__(self, class_with_event_callback, event_queue, stop_event, test_flags=[]):
        threading.Thread.__init__(self)             # initialize our superclass
        self._class_with_event_callback = class_with_event_callback
        self._event_queue = event_queue
        self._stopevent = stop_event
        self._test_flags = test_flags
        self._daily_time = datetime.time(dadivity_config.send_email_hour)
        self._next_time = self.tomorrow_time()

    def run(self):
        while not self._stopevent.isSet():
            # instead of time.sleep(...), use the timeout of the
            # threading.Event.wait(...) function normally, it should
            # just time out at about the right time, but when we stop
            # the thread, by setting stopevent, it should immediately return.
            self._stopevent.wait(self.seconds_until_next_time(self._next_time))
            if not self._stopevent.isSet():
                self._event_queue.put(self._class_with_event_callback)
                self._next_time = self.tomorrow_time()

    def tomorrow_time(self):
        if DAILY_EMAIL_EVERY_5_SECONDS in self._test_flags:
            tomorrow_time = dt.now() + datetime.timedelta(seconds=5)
        elif FAST_MODE in self._test_flags:
            tomorrow_time = dt.now() + datetime.timedelta(minutes=10)
        else:
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            tomorrow_time = dt.combine(tomorrow, self._daily_time)
        return tomorrow_time

    def seconds_until_next_time(self, next_time):
        delta_to_next_time = next_time - dt.now()
        seconds_to_next_time = delta_to_next_time.total_seconds()
        return seconds_to_next_time

class send_daily_email_summary():
    """ Once a day, send email, with a summary activity detected by the
        motion sensor.
    """
    def __init__(self, event_queue, test_flags=[]):
        self._q = event_queue
        self._test_flags = test_flags
         # create an event to that will be used to kill daily event thread
        self._stopevent = threading.Event()
        self._event_gen = daily_event_generator_thread(self, self._q, self._stopevent, self._test_flags)
        self._event_gen.start()
        self._email_retry_manager = email_retry_manager(self._q, self._test_flags)

        if QUEUE_DAILY_EMAIL_IMMEDIATELY in self._test_flags:
            # put ourselves in queue, as though triggered
            self._q.put(self)

    def stop_the_inner_thread(self):
        self._stopevent.set()
        # it could have Timer threads running
        self._email_retry_manager.reset()

    def callback(self, per_hour_counters):
        email_message = self.compose_email_msg(per_hour_counters)
        email_subject = dadivity_config.daily_email_subject
        email_error = send_email.dadivity_send(email_subject,
                                               email_message,
                                               self._test_flags)

        for i in xrange(len(per_hour_counters)):
            per_hour_counters[i] = 0

        if email_error != None:
            self._email_retry_manager.start_retrying(email_subject, email_message)

        return {"event": DAILY_EMAIL_SENT, "email_error": email_error}

    def compose_email_msg(self, per_hour_counters):
        msg = []
        msg.append('Sent: ' + time.asctime() + '\n')
        hours = [12] + range(1, 12)
        hours *= 2
        for i in xrange(12):
            msg.append( '{:2d}'.format(hours[i]) + ' AM: ' + '{:4d}'.format(per_hour_counters[i]) + ' ')
            bar_length = min(per_hour_counters[i], 60)
            msg.append('*' * bar_length)
            msg.append('\n')
        for i in xrange(12, 24):
            msg.append( '{:2d}'.format(hours[i]) + ' PM: ' + '{:4d}'.format(per_hour_counters[i]) + ' ')
            bar_length = min(per_hour_counters[i], 60)
            msg.append('*' * bar_length)
            msg.append('\n')
        return "".join(msg)

########################################################################
#
# The rest is testing stuff
#
########################################################################

class mock_event_class:
    def __init__(self):
        pass

    def callback(self):
        pass

def test(flags):
#    per_hour_counters = [0] * 24
    per_hour_counters = range(24)
    event_queue = Queue.Queue()
    se = send_daily_email_summary(event_queue, test_flags=flags)

    try:
        for i in range(10):
            event = event_queue.get(timeout=10)
            action = event.callback(per_hour_counters)
            print repr(action)

    finally:
        se.stop_the_inner_thread()

def test6():
    event_queue = Queue.Queue()
    stop_event = threading.Event()
    degt = daily_event_generator_thread(mock_event_class(), event_queue, stop_event)
    # note we don't start the thread
    print "_daily_time =", degt._daily_time
    print "_next_time =", degt._next_time
    print "seconds in a day =", 24 * 60 * 60
    print "seconds_until_next_time(degt._next_time) =", degt.seconds_until_next_time(degt._next_time)
    print "seconds_until_next_time(dt.now() + datetime.timedelta(days=1)) =", degt.seconds_until_next_time(dt.now() + datetime.timedelta(days=1))

if __name__ == '__main__':

#    from pudb import set_trace; set_trace()
    logging.basicConfig(level=logging.DEBUG)

    if 'test1' in sys.argv:   # trigger immediately, will time out or cntrl-C to stop
        test([QUEUE_DAILY_EMAIL_IMMEDIATELY, JUST_PRINT_MESSAGE])

    if 'test2' in sys.argv:   # trigger immediately, will time out or cntrl-C to stop
        test([QUEUE_DAILY_EMAIL_IMMEDIATELY, USE_MOCK_MAILMAN])

    if 'test3' in sys.argv:   # trigger immediately, really send something, will time out, or cntrl-C to stop
        test([QUEUE_DAILY_EMAIL_IMMEDIATELY, RETRY_TEST])

    if 'test4' in sys.argv:   # trigger immediately, will time out, or cntrl-C to stop
        test([QUEUE_DAILY_EMAIL_IMMEDIATELY, USE_MOCK_MAILMAN, RETRY_TEST, MOCK_ERROR])

    if 'test5' in sys.argv:   # send every 5 seconds, 5 times, then time out
        test([DAILY_EMAIL_EVERY_5_SECONDS, JUST_PRINT_MESSAGE])

    if 'test6' in sys.argv:   # test the thread class that puts something in the queue every day
        test6()               # just testing some of the date, time calculations

    if 'test7' in sys.argv:
        x = range(24)
        x[13] = 100
        sd = send_daily_email_summary(Queue.Queue)
        print sd.compose_email_msg(x)
        sd.stop_the_inner_thread()
