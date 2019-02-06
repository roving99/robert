# defaults for all processes.
"""Global configuration constants."""

IAMAROBOT  = False

if IAMAROBOT:
	MQTTIP = 'robert.local'

else:
	MQTTIP = 'localhost'

LIDARTTY = '/dev/ttyUSB0'

LEOTTY = '/dev/ttyACM0'

