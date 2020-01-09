# defaults for all processes.
"""Global configuration constants."""

IAMAROBOT  = False

#IAMAROBOT  = True

if not IAMAROBOT:
	MQTTIP = 'robert.local'

else:
	MQTTIP = 'localhost'

LIDARTTY = '/dev/ttyUSB0'

LEOTTY = '/dev/ttyACM0'

if (IAMAROBOT):
    print 'I AM A ROBOT!'
