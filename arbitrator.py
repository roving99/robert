#!/usr/bin/python

import os
import paho.mqtt.client as mqtt
import time
import json
import sys

import config

def doNavigationOutputSteering(payload):
    print 'passing steering to drive/input/steer: '+str(payload)
    #data = {"time":time.time(), "type":"", "data":[1]} 
    data = payload # pass steering data unaltered.
    client.publish(topic='drive/input/lidar', payload=json.dumps(data))

def doNavigationInputTarget(payload):
    print 'New target pose set: '+str(payload)

TOPICNAMES = { 'navigation/output/steering':doNavigationOutputSteering,
               'navigation/input/target':doNavigationInputTarget,
                }

def mqttOnMessage(client, userdata, msg):
    topic = str(msg.topic)
    print 'topic: '+topic
    payload = str(msg.payload)
    payload = json.loads(payload)
    if topic in TOPICNAMES and TOPICNAMES[topic]:
        #print 'GO!'
        TOPICNAMES[topic](payload)

def mqttOnConnect(client, userdata, flags, rc):  # added 'flags' on work version of library?
    print("Connected with result code "+str(rc))
    # re subscribe here?
    for t in TOPICNAMES.keys():
    	print 'subscribed to '+t
        client.subscribe(t)


if __name__ == '__main__':

    client = mqtt.Client()
    client.on_connect = mqttOnConnect
    client.on_message = mqttOnMessage
    
    ip = config.MQTTIP

    client.connect(ip, 1883, 60)

    client.loop_start()

    print 'MQTT Arbitrator'
    print '==============='
    print
    print 'Server: '+ip

    running = True
    
    while(running):
    	pass
    print 'stopping mqtt client..'
    client.loop_stop()
