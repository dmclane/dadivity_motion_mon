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

import time
from collections import deque
from dadivity_constants import *
from per_hour_counters import Per_Hour_Counters

class Event_Monitor:

    history_str = ''

    def __init__(self, counters, test_flags=[]):
        self.daily_email_history = deque('.....', maxlen=5)
        self.button_email_history = deque('.....', maxlen=5)
        self.retry_history = deque('.....', maxlen=5)
        self.test_flags = test_flags
        self.display(counters)

    def get_history_str(self):
        return self.history_str

    def update(self, event, counters):

        if event["event"] == MOTION_SENSOR_TRIPPED:
            self.display(counters)

        elif event["event"] == HOUR_TICK:
            self.display(counters)

        elif event["event"] == DAILY_EMAIL_SENT:
            if event["email_error"] == None:
                self.daily_email_history.appendleft('successful send, ' + time.asctime())
            else:
                self.daily_email_history.appendleft('send not successful, ' + time.asctime() + '\n' + event["email_error"])
            self.display(counters)

        elif event["event"] == BUTTON_EMAIL_SENT:
            if event["within_an_hour"]:
                self.button_email_history.appendleft('button pressed within an hour of last time, no email sent, ' + time.asctime())
            else:
                if event["email_error"] == None:
                    self.button_email_history.appendleft('email sent, ' + time.asctime())
                else:
                    self.button_email_history.appendleft('email attempted, ' + time.asctime() + '\n' + event["email_error"])
            self.display(counters)

        elif event["event"] == EMAIL_RETRY:
            retry_msg = ['retry number: ' + str(event['retry_counter']) + ', ' + time.asctime() + '\n']
            if event['email_error'] != None:
                retry_msg.append('unsuccessful; ' + event['email_error'])
            else:
                retry_msg.append('success')
            self.retry_history.appendleft("".join(retry_msg))
            self.display(counters)


    def display(self, counters):

        text = []
        text.append(counters.format_ascii_bar_chart())

        text.append('\nDaily email history:\n')
        for i in self.daily_email_history:
            text.append(i)
            text.append('\n')

        text.append('\nButton email history:\n')
        for i in self.button_email_history:
            text.append(i)
            text.append('\n')

        text.append('\nRetry email history:\n')
        for i in self.retry_history:
            text.append(i)
            text.append('\n')
        self.history_str = "".join(text)
        if PRINT_MONITOR in self.test_flags:
            print self.history_str

########################################################################
#
# The rest is testing stuff
#
########################################################################

if __name__ == "__main__":
    counters = Per_Hour_Counters()
    for i in xrange(24):
        counters.new_hour(i)
    em = Event_Monitor(counters, test_flags=[PRINT_MONITOR])
    em.update({"event":MOTION_SENSOR_TRIPPED, "hour":4, "counter":1}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":DAILY_EMAIL_SENT, "email_error":None}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":DAILY_EMAIL_SENT, "email_error":"error occured"}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":BUTTON_EMAIL_SENT, "within_an_hour":True, "email_error":None}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":BUTTON_EMAIL_SENT, "within_an_hour":False, "email_error":None}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":BUTTON_EMAIL_SENT, "within_an_hour":True, "email_error":"error occured"}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":BUTTON_EMAIL_SENT, "within_an_hour":False, "email_error":"error occured"}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":BUTTON_EMAIL_SENT, "within_an_hour":False, "email_error":"error occured"}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":BUTTON_EMAIL_SENT, "within_an_hour":False, "email_error":"error occured"}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":BUTTON_EMAIL_SENT, "within_an_hour":False, "email_error":"error occured"}, counters)
    print "--------------------------------------------------------------------------"
    em.update({"event":BUTTON_EMAIL_SENT, "within_an_hour":False, "email_error":"error occured"}, counters)
