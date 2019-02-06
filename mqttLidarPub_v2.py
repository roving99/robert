#!/usr/bin/python

import paho.mqtt.client as mqtt
import time
import neato
import sys
import math
import os
import importlib
import json

import config

#MQTT_SERVER = "192.168.0.8"
#MQTT_SERVER = "127.0.0.1"

TOPICNAME = "sense/output/lidar"


def prune(readings):    # remove erroneous readings from scan data
    keys = readings.keys()
    for key in keys:
        if readings[key][0]>16000 or readings[key][0]<10:
            del readings[key]
    return readings

def mqttOnConnect(client, userdata, rc, tmp):
    print("Connected with result code "+str(rc))

def mqttOnMessage(client, userdata, msg):
    print 'received', str(msg.topic), str(msg.payload)


if __name__=="__main__":
    print 'LIDAR MQTT Publisher'
    print '==========+========='
    print

    if not config.IAMAROBOT:
        print 'I am not a robot!'
        sys.exit()

    portname = config.LIDARTTY
    updating = True
    print 'Using data from LIDAR on port',portname
    myNeato = neato.Neato(portname, 115200)
    if myNeato.isOpen():
        print 'Port opened.'
    else:
        print 'ARSE'
        sys.exit()
    readings = myNeato.getScan()

    client = mqtt.Client()
    client.on_connect = mqttOnConnect
    client.on_message = mqttOnMessage

    client.connect(config.MQTTIP, 1883, 60)

    print 'Publishing LIDAR data on',TOPICNAME

    done = False

    prune(readings)
    cloud = neato.toCloud(readings)

    i=0
    last = time.time()
    while not done:
        if updating:
            readings = myNeato.getScan()
            rpm = myNeato.getRPM()
            prune(readings)
            cloud = neato.toCloud(readings)
        
        data = {"time":time.time(), "type":"lidar", "data":cloud}
        client.publish(topic=TOPICNAME, payload=json.dumps(data))
        time.sleep(.1)
    
        i=i+1
        if i>9:
            i=0
            print TOPICNAME, 'Freq:', 10/(time.time()-last), 'Hz'
            last = time.time()

    if myNeato:
        myNeato.close()
