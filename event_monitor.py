#! /usr/bin/python3
""" Keeps a record of recent activity.

Provides data for status_web_server.
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

import time
from collections import deque
from dadivity_constants import *
from per_hour_counters import Per_Hour_Counters, make_some_interesting_data

class Event_Monitor(object):
    """ Maintains a string with info about recent activity.

    Info consists of motion counts for each of the last 24 hours, the last
    several times that motion report email was sent, the last several times
    button initiated email was sent, and the last several times email was
    retried due to an error while trying to send email.
    """

    def __init__(self, counters, test_flags=[]):
        self._daily_email_history = deque('.....', maxlen=5)
        self._button_email_history = deque('.....', maxlen=5)
        self._retry_history = deque('.....', maxlen=5)
        self._test_flags = test_flags
        self._history_str = ""
        self._create_history_str(counters)

    def get_history_str(self):
        """ Returns history string.

        Called by another thread (status_web_server), but since strings are
        immutable, it shouldn't be a problem.
        """
        return self._history_str

    def update(self, message, counters):
        """ Update the history string.

        Args:
            message: a dictionary with at least on entry called "event".
            counter: an instance of Per_Hour_Counters
        """

        if message["event"] == MOTION_SENSOR_TRIPPED:
            self._create_history_str(counters)

        elif message["event"] == HOUR_TICK:
            self._create_history_str(counters)

        elif message["event"] == MOTION_REPORT_SENT:
            if message["email_error"] == None:
                self._daily_email_history.appendleft('successful send, '
                                                     + time.asctime())
            else:
                self._daily_email_history.appendleft('send not successful, '
                                                     + time.asctime() + '\n'
                                                     + message["email_error"])
            self._create_history_str(counters)

        elif message["event"] == BUTTON_EMAIL_SENT:
            if message["within_an_hour"]:
                self._button_email_history.appendleft(
                    'button pressed within an hour of last time, no email sent, '
                    + time.asctime())
            else:
                if message["email_error"] == None:
                    self._button_email_history.appendleft('email sent, '
                                                          + time.asctime())
                else:
                    self._button_email_history.appendleft('email attempted, '
                                                          + time.asctime()
                                                          + '\n'
                                                          + message["email_error"])
            self._create_history_str(counters)

        elif message["event"] == EMAIL_RETRY:
            retry_msg = ['retry number: ' + str(message['retry_counter'])
                         + ', ' + time.asctime() + '\n']
            if message['email_error'] != None:
                retry_msg.append('unsuccessful; ' + message['email_error'])
            else:
                retry_msg.append('success')
            self._retry_history.appendleft("".join(retry_msg))
            self._create_history_str(counters)


    def _create_history_str(self, counters):

        text = []
        text.append(counters.format_ascii_bar_chart())

        text.append('\nDaily email history:\n')
        for i in self._daily_email_history:
            text.append(i)
            text.append('\n')

        text.append('\nButton email history:\n')
        for i in self._button_email_history:
            text.append(i)
            text.append('\n')

        text.append('\nRetry email history:\n')
        for i in self._retry_history:
            text.append(i)
            text.append('\n')
        self._history_str = "".join(text)
        if PRINT_MONITOR in self._test_flags:
            print(self._history_str)

########################################################################
#
# The rest is testing stuff
#
########################################################################

if __name__ == "__main__":
    counters = Per_Hour_Counters()
    make_some_interesting_data(counters)

#    em = Event_Monitor(counters, test_flags=[PRINT_MONITOR])
    em = Event_Monitor(counters)

    em.update({"event":MOTION_SENSOR_TRIPPED},                                                        counters)
    em.update({"event":MOTION_REPORT_SENT,                            "email_error":None},            counters)
    em.update({"event":MOTION_REPORT_SENT,                            "email_error":"error occured"}, counters)
    em.update({"event":BUTTON_EMAIL_SENT,     "within_an_hour":True,  "email_error":None},            counters)
    em.update({"event":BUTTON_EMAIL_SENT,     "within_an_hour":False, "email_error":None},            counters)
    em.update({"event":BUTTON_EMAIL_SENT,     "within_an_hour":True,  "email_error":"error occured"}, counters)
    em.update({"event":BUTTON_EMAIL_SENT,     "within_an_hour":False, "email_error":"error occured"}, counters)
    em.update({"event":BUTTON_EMAIL_SENT,     "within_an_hour":False, "email_error":"error occured"}, counters)
    em.update({"event":BUTTON_EMAIL_SENT,     "within_an_hour":False, "email_error":"error occured"}, counters)
    em.update({"event":BUTTON_EMAIL_SENT,     "within_an_hour":False, "email_error":"error occured"}, counters)
    em.update({"event":BUTTON_EMAIL_SENT,     "within_an_hour":False, "email_error":"error occured"}, counters)
    em.update({"event":EMAIL_RETRY,           "retry_counter":1,      "email_error":"error occured"}, counters)
    em.update({"event":EMAIL_RETRY,           "retry_counter":2,      "email_error":None}, counters)

    print(em.get_history_str())

