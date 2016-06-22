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
import dadivity_config
from dadivity_constants import *
import send_email
import time

MAX_RETRIES = 4
RESET_FLAG = -1
HOUR = 60 * 60

class email_retry_manager:

    def __init__(self, event_queue, test_flags=[]):
        self._q = event_queue
        self._retry_counter = RESET_FLAG
        self._retry_timer = None
        self._test_flags = test_flags
        if RETRY_TEST in self._test_flags:
            self._base_wait = 1                # seconds
        elif FAST_MODE in self._test_flags:
            self._base_wait = 10
        else:
            self._base_wait = HOUR

    def start_retrying(self, subject, msg):
        """ Call this the first time to start the retry process.  After that, retries are handled here.
        """
        self._msg = msg
        self._subject = subject
        if self._retry_timer != None:
            self._retry_timer.cancel()
        self._retry_timer = threading.Timer(self._base_wait, self._q.put, [self])
        self._retry_timer.start()
        self._retry_counter = 1

    def retry_again(self):
        if self._retry_counter < MAX_RETRIES:
            wait_multiplier = 2 ** self._retry_counter         # 2, 4, 8
            self._retry_timer = threading.Timer(self._base_wait * wait_multiplier,  self._q.put, [self])
            self._retry_timer.start()
            self._retry_counter += 1
        else:
            self._retry_counter = RESET_FLAG

    def reset(self):
        self._retry_counter = RESET_FLAG
        if self._retry_timer != None:
            self._retry_timer.cancel()

    def callback(self, per_hour_counters):

        email_error = None
        current_retry_counter = self._retry_counter      # save current value because it's incremented in retry_again()
        if self._retry_counter != RESET_FLAG:
            message = "retry # " + str(self.retry_counter) + "\n" + self._msg
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
    import logging
    logging.basicConfig(level=logging.DEBUG)
    #from pudb import set_trace; set_trace()

    ONE_YEAR_TIMEOUT = 365 * 24 * 60 *60

    per_hour_counters = [0] * 24
    event_queue = Queue.Queue()
    erm = email_retry_manager(event_queue, test_flags=[RETRY_TEST])
    erm.start_retrying("test phrase")

    for i in xrange(10):
        event = event_queue.get(timeout=ONE_YEAR_TIMEOUT)
        action = event.callback(per_hour_counters)
        print repr(action)
        print time.asctime()
        print "\n*********************************************\n"
        # if i == 2:
        #     erm.reset()
        #     print "\n---------- reset ---------\n"
