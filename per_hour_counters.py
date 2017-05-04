#! /usr/bin/python

import sys, time
import collections
import copy
from datetime import datetime as dt

HOUR = 0
COUNT = 1

class Per_Hour_Counters:

    def __init__(self):
        self.counters = collections.deque(maxlen=24)
        self.counters.appendleft([dt.now().hour, 0])

    def new_hour(self, hour):
        self.counters.appendleft([hour, 0])    # count starts at 0

    def motion_hit(self):
       self.counters[0][COUNT] = self.counters[0][COUNT] + 1 

    def get_copy_of_counters(self):
        return copy.deepcopy(self.counters)

    def format_ascii_bar_chart(self):
        msg = []
        for hour,count in self.counters:
            if hour == 0:
                msg.append( '{:2d}'.format(12))
                msg.append(' AM: ')
            else:
                if hour < 13:
                    msg.append( '{:2d}'.format(hour))
                else:
                    msg.append( '{:2d}'.format(hour - 12))

                if hour < 12:
                    msg.append(' AM: ')
                else:
                    msg.append(' PM: ')
            msg.append('{:4d}'.format(count) + ' ')
            bar_length = min(count, 60)
            msg.append('*' * bar_length)
            msg.append('\n')
        return "".join(msg)

#######################################################################
#
# The rest is testing stuff
#
########################################################################

def make_some_interesting_data(counters):
        for i in range(24):
            counters.new_hour(i)
            for j in xrange(i * 3):
                counters.motion_hit()
 

if __name__ == "__main__":

    if "test1" in sys.argv:
        hc = Per_Hour_Counters()
        print hc.counters
        for i in range(24):
            hc.new_hour(i)
            hc.motion_hit()
        print hc.counters
        dup = hc.get_copy_of_counters()
        for i in range(4):
            hc.new_hour(i)
            hc.motion_hit()
            hc.motion_hit()
        print hc.counters
        print "copy ="
        print dup

    if "test2" in sys.argv:
        hc = Per_Hour_Counters()
        make_some_interesting_data(hc)
        print hc.format_ascii_bar_chart()

