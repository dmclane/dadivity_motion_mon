""" A mock GPIO module, to test code when not on the Pi.
"""

BCM = 0
PUD_UP = 0
FALLING = 0
RISING = 0
IN = 0
OUT = 0

def setmode(mode):
    pass

def setup(pin, in_out, **kwargs):
    pass

def add_event_detect(pin, edge, **kwargs):
    pass

def cleanup():
    pass

def output(a, b):
    pass

