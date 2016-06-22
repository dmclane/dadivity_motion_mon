
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

import socket
import threading
import time
from dadivity_constants import *
import sys

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

class status_web_server(threading.Thread):

    def __init__(self, event_monitor, test_flags=[]):
        threading.Thread.__init__(self)
        self.event_monitor = event_monitor
        self.test_flags = test_flags
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind((HOST, PORT))
        self.listen_socket.listen(1)
        if PRINT_WEB_SERVER_ACTIVITY in self.test_flags:
            print 'Serving HTTP on port %s ...' % PORT

    def run(self):
        while True:
            client_connection, client_address = self.listen_socket.accept()
            request = client_connection.recv(2048)
            if PRINT_WEB_SERVER_ACTIVITY in self.test_flags:
                print request

            if request.startswith('GET / '):
                status = self.event_monitor.get_history_str() # atomic operation, strings are immutable
                response = "".join([response_preamble, status, response_postamble])
                client_connection.sendall(response)
            else:
                client_connection.sendall("HTTP/1.0 404 Not Found\r\n")
            client_connection.close()

    def shutdown(self):                 # called from different thread
        self.listen_socket.shutdown(socket.SHUT_RDWR)
        self.listen_socket.close()

########################################################################
#
# The rest is testing stuff
#
########################################################################

class dummy_event_monitor:

    def get_history_str(self):
        return time.asctime()

def main():
    sws = status_web_server(dummy_event_monitor(), test_flags=[PRINT_WEB_SERVER_ACTIVITY])
    sws.start()

    try:
        while 1:
            time.sleep(1)
    finally:
        sws.shutdown()

def test1():
    sws = status_web_server(dummy_event_monitor())
    sws.start()

    try:
        while 1:
            time.sleep(1)
    finally:
        sws.shutdown()


if __name__ == "__main__":

    if 'test1' in sys.argv:
        test1()
    else:
        main()
