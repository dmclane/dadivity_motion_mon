#! /bin/python

"""
If we get an error, when sending email, try again a few times.

wait one hour and try again, if that doesn't succeed;
wait two hours and try again, if that doesn't succeed;
wait four hours and try again, if that doesn't succeed;
wait 8 hours and try again, if that doesn't succeed;
give up
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

import Queue
import threading
from dadivity_constants import *
import send_email
import time
import logging

MAX_RETRIES = 4
RESET_FLAG = -1
HOUR = 60 * 60

class Email_Retry_Manager(object):
    """ Retry sending email after an error.

    Interval between retries becomes progressivly longer if attempts
    continue to fail.
    """

    def __init__(self, event_queue, test_flags=[]):
        self._q = event_queue
        self._retry_counter = RESET_FLAG
        self._retry_timer = None
        self._test_flags = test_flags
        self._msg = ""
        self._subject = ""
        if FAST_RETRY in self._test_flags:
            self._base_wait = 1                # seconds
        elif FAST_MODE in self._test_flags:
            self._base_wait = 10
        else:
            self._base_wait = HOUR

    def start_retrying(self, subject, msg):
        """ Call this the first time to start the retry process.

        After the first time, retries are handled in motion_email_retry.
        """
        self._msg = msg
        self._subject = subject
        if self._retry_timer != None:
            self._retry_timer.cancel()
        self._retry_timer = threading.Timer(self._base_wait, self._q.put, [self])
        self._retry_timer.start()
        self._retry_counter = 1

    def retry_again(self):
        """ Schedule another retry."""
        if self._retry_counter < MAX_RETRIES:
            wait_multiplier = 2 ** self._retry_counter         # 2, 4, 8
            self._retry_timer = threading.Timer(self._base_wait * wait_multiplier,
                                                self._q.put, [self])
            self._retry_timer.start()
            self._retry_counter += 1
        else:
            self._retry_counter = RESET_FLAG

    def reset(self):
        self._retry_counter = RESET_FLAG
        if self._retry_timer != None:
            self._retry_timer.cancel()

    def callback(self):
        return {"event":RETRY_MOTION_EMAIL}

    def motion_email_retry(self):
        """ Try to send again.

        Called after timer puts instance of self in queue and callback returns
        a message which is dispatched as a call to this method.
        """
        email_error = None
        current_retry_counter = self._retry_counter
        # save current value because it's incremented in retry_again()
        logging.debug("current_retry_counter = " + str(current_retry_counter))
        if self._retry_counter != RESET_FLAG:
            message = "retry # " + str(self._retry_counter) + "\n" + self._msg
            email_error = send_email.dadivity_send(self._subject,
                                                   message,
                                                   self._test_flags)
            if email_error != None:
                self.retry_again()

        return {"event":EMAIL_RETRY, "email_error":email_error, "retry_counter":current_retry_counter}

########################################################################
#
# The rest is testing stuff
#
########################################################################

if __name__ == "__main__":

    # debugging stuff, normally commented out.
    #from pudb import set_trace; set_trace()
    logging.basicConfig(level=logging.DEBUG)

    ONE_YEAR_TIMEOUT = 365 * 24 * 60 *60

    per_hour_counters = [0] * 24
    event_queue = Queue.Queue()
    erm = Email_Retry_Manager(event_queue, test_flags=[FAST_RETRY, MOCK_ERROR, JUST_PRINT_MESSAGE])
    erm.start_retrying("test subject", "test message")

    try:

        for i in xrange(10):
            event = event_queue.get(timeout=ONE_YEAR_TIMEOUT)
            message = event.callback()
            print repr(message)
            if message["event"] == RETRY_MOTION_EMAIL:
                erm.motion_email_retry()
            print time.asctime()
            print "\n*********************************************\n"
            # if i == 2:
            #     erm.reset()
            #     print "\n---------- reset ---------\n"

    except KeyboardInterrupt: pass

