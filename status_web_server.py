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

import SocketServer
import threading
import time
from dadivity_constants import *
import sys
import logging

# HOST = 'localhost'   # if 'localhost', only available locally, '' for everywhere
HOST = ''   # if 'localhost', only available locally, '' for everywhere
PORT = 8888

response_preamble = """\
HTTP/1.1 200 OK

<html>
<head>
<title> Dadivity Status </title>
<META HTTP-EQUIV="refresh" CONTENT="15">
</head>
<body>
<pre>
"""

# to refresh a page every 15 seconds
# <META HTTP-EQUIV="refresh" CONTENT="15">

response_postamble = """
</pre>
</body>
</html>
"""

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        data = self.request.recv(2048).strip()
        recieved_length = len(data)
        if PRINT_WEB_SERVER_ACTIVITY in self.server._test_flags:
            logging.debug("length recieved: " + str(recieved_length))
            logging.debug("{} wrote:".format(self.client_address[0]))
            logging.debug(data)
        if recieved_length > 0:   # on shutdown you come here with a length of 0.
            status = self.server.event_monitor.get_history_str() # atomic operation, strings are immutable
            response = "".join([response_preamble, status, response_postamble])
            self.request.sendall(response)

class Status_Web_Server(threading.Thread):

    def __init__(self, event_monitor, test_flags=[]):

        threading.Thread.__init__(self)
        self._test_flags = test_flags
        self.server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
        # The handler has a reference to the server.  So, to pass something
        # to the handler, we dynamically add it to the server:
        self.server.event_monitor = event_monitor
        self.server._test_flags = self._test_flags
        self.start()

    def run(self):
        self.server.serve_forever(poll_interval=0.5)

    def shutdown(self):
        logging.debug("shutdown called")
        self.server.shutdown()
        self.server.server_close()

########################################################################
#
# The rest is testing stuff
#
########################################################################

class dummy_event_monitor:

    def get_history_str(self):
        return time.asctime()

def main():
    sws = Status_Web_Server(dummy_event_monitor(), test_flags=[PRINT_WEB_SERVER_ACTIVITY])

    try:
        time.sleep(20)
        print "timed out"

    except KeyboardInterrupt: pass

    finally:
        try:
            sws.shutdown()
        except KeyboardInterrupt: pass


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    main()

