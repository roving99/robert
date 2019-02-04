#pusher.
# take current pose, and a target position (x,y) 

import time
import math
import paho.mqtt.client as mqtt
import os
import json

class Pusher(object):
	pass

def doTarget(payload):
    print 'doTarget called'
    print payload
    if payload:
        xTarget = payload[u'data'][0]
        yTarget = payload[u'data'][1]
        thetaTarget = payload[u'data'][2]
    else:
        xTarget=None
        yTarget=None
        thetaTarget=None

HOSTNAME = "localhost"

TOPICNAMES = [
    ['odometry/input/target', doTarget],
    ]

def mqttOnMessage(client, userdata, msg):
    topic = str(msg.topic)
    payload = str(msg.payload)
    print 'received', topic, payload
    payload = json.loads(payload)
    for t in TOPICNAMES:
        if t[0]==topic:
            t[1](payload)

def mqttOnConnect(client, userdata, flags, rc):  # added 'flags' on work version of library?
    print("Connected with result code "+str(rc))
    # re subscribe here?
    for t in TOPICNAMES:
        client.subscribe(t[0])


if __name__=="__main__":
    print 'Pusher'
    print '==+==='
    print

    client = mqtt.Client()
    client.on_connect = mqttOnConnect
    client.on_message = mqttOnMessage
    client.connect(HOSTNAME, 1883, 60)

    xTarget = None
    yTarget = None
    thetaTarget = None

    running = True
    while running:
        client.loop()

        data = {"time":time.time(), "type":"target", "data":[xTarget, yTarget, thetaTarget]}
        client.publish(topic='odometry/output/target', payload=json.dumps(data))

    client.close()
