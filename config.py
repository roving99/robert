# defaults for all processes.
"""Global configuration constants."""

IAMAROBOT  = True

if not IAMAROBOT:
	MQTTIP = 'robert.local'

else:
	MQTTIP = 'localhost'

LIDARTTY = '/dev/ttyUSB0'

LEOTTY = '/dev/ttyACM0'

