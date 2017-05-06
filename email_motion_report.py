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
import dadivity_config
from dadivity_constants import *
import send_email
from email_retry_manager import Email_Retry_Manager

# imports for testing part
import logging
import per_hour_counters
import Queue

class Email_Motion_Report():
    """ Send email, with a summary of activity detected by the
        motion sensor.
    """
    def __init__(self, queue, test_flags=[]):
        self._test_flags = test_flags
        self._email_retry_manager = Email_Retry_Manager(queue, test_flags=test_flags)

    def send(self, ascii_bar_chart):
        email_message = self.compose_email_msg(ascii_bar_chart)
        email_subject = dadivity_config.daily_email_subject
        email_error = send_email.dadivity_send(email_subject,
                                               email_message,
                                               self._test_flags)

        if email_error != None:
            self._email_retry_manager.start_retrying(email_subject, email_message)

        return {"event": MOTION_REPORT_SENT, "email_error": email_error}

    def compose_email_msg(self, ascii_bar_chart):
        msg = []
        msg.append('Sent: ' + time.asctime() + '\n')
        msg.append(ascii_bar_chart)
        return "".join(msg)

    def retry(self):
        return self._email_retry_manager.motion_email_retry()

    def stop_any_pending_retries(self):
        # it could have Timer threads running
        self._email_retry_manager.reset()

########################################################################
#
# The rest is testing stuff
#
########################################################################

#__test__ = { }

def test(flags):
    counters = per_hour_counters.Per_Hour_Counters()
    per_hour_counters.make_some_interesting_data(counters)
    emr = Email_Motion_Report(Queue.Queue(),
                              test_flags=flags)
    send_result = emr.send(counters.format_ascii_bar_chart())
    print "send_result:", send_result

if __name__ == '__main__':

#    from pudb import set_trace; set_trace()
    logging.basicConfig(level=logging.DEBUG)

    if 'test1' in sys.argv:
        test([JUST_PRINT_MESSAGE])

    if 'test2' in sys.argv:
        test([USE_MOCK_MAILMAN])

    if 'test3' in sys.argv:
        test([FAST_RETRY])

    if 'test4' in sys.argv:
        test([USE_MOCK_MAILMAN, FAST_RETRY, MOCK_ERROR])

    if 'test5' in sys.argv:
        test([])

