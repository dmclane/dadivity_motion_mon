#! /usr/bin/python3

""" send_email.py -- send email

Originally from my course automation software, which is why it has options for different email
servers.
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

import smtplib
import getpass
import sys
import dadivity_config
from dadivity_constants import *
import logging

test_dest = dadivity_config.email_recipients[0]
default_from_addr = dadivity_config.gmail_from_address

def mailman_factory(**kwargs):

    mailman = None
    if 'use_mailman' in kwargs:
        if kwargs['use_mailman'] == 'mock':
            from_address = kwargs.get('override_default_from_addr', dadivity_config.gmail_from_address)
            mailman = MockMailman(from_address)
        elif kwargs['use_mailman'] == 'null':
            from_address = kwargs.get('override_default_from_addr', default_from_addr)
            mailman = NullMailman(from_address)
        elif kwargs['use_mailman'] == 'gmail':
            from_address = kwargs.get('override_default_from_addr', dadivity_config.gmail_from_address)
            mailman = GmailMailman(from_address, smtp_debug_level=kwargs.get('smtp_debug_level', 0))
        elif kwargs['use_mailman'] == 'localhost':
            from_address = kwargs.get('override_default_from_addr', default_from_addr)
            mailman = LocalhostMailman(from_address, smtp_debug_level=kwargs.get('smtp_debug_level', 0))
        else:
            logging.debug('Unknown mailman: %s' % (kwargs['use_mailman'],))

    return mailman

def send_a_message(subject, to_address, msg, **kwargs):
    mailman = None
    try:
        mailman = mailman_factory(**kwargs)
        if mailman != None:
            mailman.basic_send(subject, to_address, msg)
    finally:
        if mailman != None:
            mailman.quit()

def send_to_list(subject, msg, **kwargs):
    mailman = mailman_factory(**kwargs)
    if mailman != None:
        mailman.list_send(subject, msg, **kwargs)
        mailman.quit()

def dadivity_send(subject, destination_list, msg, test_flags=[]):

    if MOCK_ERROR in test_flags:
        email_error = "mock error"
    else:
        email_error = None

    if JUST_PRINT_MESSAGE in test_flags:
        logging.debug(msg)

    else:
        kwargs = {}
        if USE_MOCK_MAILMAN in test_flags:
            kwargs["use_mailman"] = "mock"
        else:
            kwargs["use_mailman"] = "gmail"

        mailman = None
        try:
            mailman = mailman_factory(**kwargs)
            if mailman != None:
                mailman.list_send(subject, msg, list_dest=destination_list)
        except smtplib.SMTPException as e:
            # we don't want the whole program to crash, if sending email fails
            email_error = str(e)
        finally:
            if mailman != None:
                mailman.quit()

    return email_error

class BasicMailman(smtplib.SMTP):
    """ An abstract base class

    Derived classes: MockMailman, LocalhostMailman, GmailMailman, UWMailman
    """

    def basic_send(self, subject, to_address, msg):
        s = []
        s.append("Subject: %s\r\nFrom: %s\r\nTo: %s\r\n\r\n"
               % (subject, self.from_address, to_address))
        s.append(msg)
        msg = "".join(s)
        self.sendmail(self.from_address, to_address, msg)
        return msg

    def list_send(self, subject, msg, **kwargs):
        if kwargs.get('use_test_dest', False):
           self.basic_send(subject, test_dest, msg)
        else:
            for i in kwargs.get('list_dest', []):
                self.basic_send(subject, i, msg)

class NullMailman(object):
    """ Doesn't do anything.
    """

    def __init__(self, from_address, email_server='default', account='default', smtp_debug_level=0):
        print("from_address =", from_address)
        print("email_server =", email_server)
        print("account = ", account)
        print("smtp_debug_level =", smtp_debug_level)

    def basic_send(self, subject, to_address, msg):
        print("basic_send(...)")

    def list_send(self, subject, msg, **kwargs):
        print("list_send(...)")

    def set_debuglevel(self, n):
        print("set_debugLevel(...)")

    def sendmail(self, fromaddr, toaddr, msg):
        print("sendmail(...)")

    def quit(self): pass

class MockMailman(BasicMailman):
    """A class that looks like SMTP, or the derived classes,
       but doesn't do anything, except print out the message.
    """

    pw = None

    def __init__(self, from_address, email_server=dadivity_config.gmail_outgoing_smtp_server,
                 account=dadivity_config.gmail_account, smtp_debug_level=0):
        # we do not call super inits
        self.from_address = from_address
        if MockMailman.pw == None:
            MockMailman.pw = getpass.getpass('Password for MockMailman: ')
            logging.debug('pw = %s', MockMailman.pw)
            logging.debug('email_server = %s', email_server)
            logging.debug('account = %s', account)
            logging.debug('from_address = %s', from_address)

    def set_debuglevel(self, n): pass

    def sendmail(self, fromaddr, toaddr, msg):
        logging.debug('From MockMailman:')
        logging.debug('msg =  %s', msg)

    def quit(self): pass

class LocalhostMailman(BasicMailman):
    """ Let a local server relay mail. """
    local_hostname = 'localhost'
    timeout = 10

    def __init__(self, from_address, smtp_debug_level=0):
        # Call super class constructor, if any.
        for base in self.__class__.__bases__:
            if hasattr(base, '__init'):
                base.__init__(self)
        self.from_address = from_address
        self.connect('localhost')
        self.set_debuglevel(smtp_debug_level)

    def send_email(self, msg):
        self.sendmail(self.from_address, toaddr, msg)

class GmailMailman(BasicMailman):
    """ Send to gmail account. """
    local_hostname = 'localhost'
    timeout = 10
    default_port = 25
    pw = dadivity_config.gmail_passwd

    def __init__(self, from_address,
                 email_server=dadivity_config.gmail_outgoing_smtp_server,
                 account=dadivity_config.gmail_account,
                 smtp_debug_level=0):
#        super().__init__(host="smtp.gmail.com", port=587)
        super().__init__(host=email_server)
        self.from_address = from_address
        if GmailMailman.pw == None:
            GmailMailman.pw = getpass.getpass('Password for ' + account
                                                  + '@' + email_server + ': ')

        logging.debug("email_server = " + email_server)
        self.set_debuglevel(smtp_debug_level)
        self.starttls()
        self.login(account, GmailMailman.pw)



test_subject = 'next meeting'
test_msg = 'Does the 28th work for you?'

if __name__ == '__main__':

    # from pudb import set_trace; set_trace()  # start debugger, normally commented out
    logging.basicConfig(level=logging.DEBUG)

    destination_list = dadivity_config.email_recipients

    if 'null' in sys.argv:
        send_a_message('test_sub', test_dest, 'this is a test', use_mailman='null')

    if 'mock' in sys.argv:
        send_a_message('test_sub', test_dest, 'this is a test', use_mailman='mock')

    if 'gmail' in sys.argv:
        send_a_message(test_subject, test_dest, test_msg, use_mailman='gmail')

    if 'gmail1' in sys.argv:
        send_a_message(test_subject, test_dest, test_msg, use_mailman='gmail', smtp_debug_level=2)

    if 'dad' in sys.argv:
        email_error = dadivity_send(test_subject, destination_list, test_msg)
        print("email_error =", email_error)

    if 'dad1' in sys.argv:
        email_error = dadivity_send(test_subject,
                                    destination_list,
                                    test_msg,
                                    test_flags=[USE_MOCK_MAILMAN, MOCK_ERROR])
        print("email_error =", email_error)

