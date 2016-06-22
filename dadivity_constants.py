
# constants used in test_flags[]
QUEUE_DAILY_EMAIL_IMMEDIATELY = 100      # send_daily_email_summary
JUST_PRINT_MESSAGE = 101                 # send_daily_email_summary
USE_MOCK_MAILMAN = 102                   # send_daily_email_summary, button_email
DAILY_EMAIL_EVERY_5_SECONDS = 103        # daily_event_generator_thread
DISPLAY_ACTIVITY = 104                   # dadivity
RETRY_TEST = 105                         # email_retry_manager
MOCK_ERROR = 106                         # send_daily_email_summary, button_email
FAST_MODE = 107                          # daily_event_generator_thread, email_retry_manager
PRINT_MONITOR = 108
PRINT_WEB_SERVER_ACTIVITY = 109

#
#  dadivity ---> send_daily_email_summary --->   daily_event_generator_thread
#            |                             |
#            |                             | --> email_retry_manager
#            |                             |
#            |                             | --> dadivity_send
#            |
#            |--> button_email  ---> email_retry_manager
#            |
#            ---> motion_sensor

#constants used in display update
DAILY_EMAIL_SENT = 1001
MOTION_SENSOR_TRIPPED = 1002
BUTTON_EMAIL_SENT = 1003
EMAIL_RETRY = 1004
