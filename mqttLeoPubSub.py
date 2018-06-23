#!/usr/bin/python
import sys
import pygame
import math
import os
import paho.mqtt.client as mqtt
import time
import json
import leo
import robotBase
'''
drive/input/steer  {"data": [<translate>, <rotate>], } cms-1, degrees-1
drive/input/motors {"data": [<motor left speed>, <motor right speed>], }   cms-1, cms-1
drive/input/leds   {"data": [led0, led1, led2, ..], }  n
drive/input/lidar  {"data": [0|1], }   n
drive/input/raw    {"data": [<string>], }  raw command to controlling arduino
        
drive/output/count {"data": [<motor left count>, <motor right count>], }   
drive/output/battery   {"data": [<volts>], }   volts

sense/output/sonar {"data": { <angle>: <distance>, <angle>:<distance>, ...}, } degree, cm
sense/output/touch {"data": [ <touch0>, <touch1>, ...], }  0/1
sense/output/cliff {"data": [ <cliff0>, <cliff1>, ...], }  0/1
sense/output/compass   {"data": <bearing>, }   degree
        
odometry/output/pose   {"data": [ <x>, <y>, <theta>], }    cm, cm, degree
odometry/output/rate   {"data": [ <dx>, <dy>, <dtheta>], } cms-1, cms-1, degrees-1

odometry/input/pose   {"data": [ <x>, <y>, <theta>], }    cm, cm, degree

00<c> LED colour, 01<f><d> Tone, 03<1><2> set Speed, 04 - reset counters, 05<1><2> - set goal count, 06<xx> - set PWM to motor, 
10 get LED colour, 11 - get Time, 12 - get battery, 13 - get Speed, 14 - get Counters, 15 - get Target, 16 - Get IRx4, 17 - get Compass, 18 - Get Amps, 
FD - test signals, FE - echo args, FF help."

'''

HOSTNAME = "localhost"

def doSteer(payload):
    print 'doSteer called'
    pass

def doMotors(payload):
    print 'doMotors called'
    print payload
    m1 = int(128+(payload[u'data'][0]/0.78125))    # convert cms-1 to power (0-255)
    m2 = int(128+(payload[u'data'][1]/0.78125))
    command = '03'+toHex(m1)+toHex(m2)
    print command
    print myLeo.send(command)
    
def doLeds(payload):
    print 'doLeds called'
    pass
    
def doLidar(payload):
    print 'doLidar called'
    if payload[u'data'][0]>0:
        command = '061F'
    else:
        command = '0600'
    print command
    print myLeo.send(command)
    pass
    
def doRaw(payload):
    global myLeo
    print 'doRaw called'
    print myLeo.send(payload[u'data'][0])

def doPose(payload):
    print 'doPose called'
    myLeo.send('038080')    # stop
    myLeo.send('04')        # reset counters on md25
    md25Base.reset()        # reset pose.

TOPICNAMES = [
    ['drive/input/steer',  doSteer],
    ['drive/input/motors', doMotors],
    ['drive/input/leds',   doLeds],
    ['drive/input/lidar',  doLidar],
    ['drive/input/raw',    doRaw],
    ['odometry/input/pose', doPose],
    ]

def toHex(i):
    result = hex(i)
    if i<16: result = '0'+result[-1:]
    else: result = result[-2:]
    return result

def toSignedHex(i):     # (-1) -> 'ff' (1) -> '01'
    if i>=0:
        return toHex(i)
    else:
        return toHex(256+i)

def hexToSigned(s, bits=32):    # 'FF',bits=8 -> -1 
    i = int(s, 16)
    if i >= 2**(bits-1):
        i -= 2**bits
    return i

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
    print 'Leo to MQTT'
    print '=====+====='
    print

    portName = sys.argv[1]
    myLeo = leo.Leo(portName, 19200)

    if myLeo.isOpen():
        print 'Synchronizing..'
        if myLeo.sync():
            print 'sucess'
        else:
            print 'FAILED to synchronize'
            myLeo.close()
            sys.exit()
    else:
        print 'FAILED to open port'
        myLeo.close()
        sys.exit()
    
    client = mqtt.Client()
    client.on_connect = mqttOnConnect
    client.on_message = mqttOnMessage
    client.connect(HOSTNAME, 1883, 60)

    md25Base = robotBase.RobotBase(30, 31.4159, 360)    # axle = 30cm(???), wheels 10cm diameter, 360 pulses per revolution
    md25Base.reset()

    running = True
    while running:
        client.loop()
        battery = myLeo.send('12')  # battery level
        battery = int(battery,16)/10.0
        counters = myLeo.send('14')
        counter1 = hexToSigned(counters[0:8])
        counter2 = hexToSigned(counters[8:16])
        md25Base.update(counter1, counter2)

        data = {"time":time.time(), "type":"battery", "data":[battery]}
        client.publish(topic='drive/output/battery', payload=json.dumps(data))

        data = {"time":time.time(), "type":"counters", "data":[counter1, counter2]}
        client.publish(topic='drive/output/counters', payload=json.dumps(data))

        data = {"time":time.time(), "type":"pose", "data":[md25Base.x, md25Base.y, md25Base.theta]}
        client.publish(topic='odometry/output/pose', payload=json.dumps(data))

    myLeo.close()
    client.close()
