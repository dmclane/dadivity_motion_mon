""" Dadivity configuration file.

Copy this to dadivity_config.py, and edit with desired data.  Updating the
software from git repository could overwrite config_template.py, but won't
overwrite dadivity_config.py.
"""

# hour(s) on which to send email
send_email_hour = [0, 22]   # integer(s) 0 to 23

daily_email_subject = "Motion report"

button_subject = "Button message"
button_message = "Call me, next time you get a chance."

# use a list, in case we want multiple recipients (especially when testing)
#email_recipients = ['alice@example.com', 'bob@example.com']
email_recipients = ['alice@example.com']

gmail_account = 'example'
gmail_from_address = 'example@example.com'
gmail_passwd = 'password'
gmail_outgoing_smtp_server = 'smtp.gmail.com:587'    # TLS supposedly

web_server_port = 8888


