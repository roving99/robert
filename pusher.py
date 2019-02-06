#!/usr/bin/python
#pusher.
# take current pose, and a target position (x,y) 

import time
import math
import paho.mqtt.client as mqtt
import os
import json

import config

class Pusher(object):

    def __init__(self):
        self.xPose=0
        self.yPose=0
        self.thetaPose=0
        self.xTarget=0
        self.yTarget=0
        self.thetaTarget=0
        self.bearing=0
        self.distance=0

    def updateBearing(self):
        dx = (self.xTarget-self.xPose)
        dy = (self.yTarget-self.yPose)
        self.distance = math.sqrt(dx*dx+dy*dy)
        
        if math.fabs(dy)<0.0000000001:
            dy = 0.000000001
        if math.fabs(dx)<0.0000000001:
            dx = 0.000000001
            
        #self.bearing = math.asin(dx/self.distance)
        self.bearing = math.atan(dy/dx)
        if (dx<0 and dy>0):
            self.bearing = math.pi+self.bearing
        if (dx<0 and dy<0):
            self.bearing = math.pi+self.bearing
        if (dx>0 and dy<0):
            self.bearing = 2.0*math.pi+self.bearing
            
    def getRelativeBearing(self):
        th = self.bearing-self.thetaPose
        return self.distance, math.degrees(th)

    def getBearing(self):
        return self.distance, math.degrees(self.bearing)
            
    def getPose(self):
        return self.xPose, self.yPose, math.degrees(self.thetaPose)

    def getTarget(self):
        return self.xTarget, self.yTarget, math.degrees(self.thetaTarget)

    def setPose(self, x, y, th):
        self.xPose = x
        self.yPose = y
        self.thetaPose = math.radians(th)
        self.updateBearing()

    def setTarget(self, x, y, th):
        print 'setTarget: '+str(x)+', '+str(y)+", "+str(th)
        self.xTarget = x
        self.yTarget = y
        self.thetaTarget = math.radians(th)
        self.updateBearing()
    
    def areWeThereYet(self):
        acceptable = 10.0 # cm
        return (self.distance<acceptable)

    def getSteering(self):
        acceptable = 5 # degrees
        relative = self.getRelativeBearing()[1] # degrees
        if self.areWeThereYet():
            return (0.0, 0.0) # cms-1, degrees-1 : stop
        if math.fabs(relative)<acceptable: # heading in the right direction?
            return (10.0, 0.0) # cms-1, degrees-1 : move forward
        if relative>180:
            relative = -(360-relative)
        rate = 0.5*relative
        if rate>20:
            rate = 20
        if rate<-20:
            rate = -20
        return (0.0,rate)    


def doTarget(payload):
    print 'doTarget called'
    print payload
    p.setTarget(payload[u'data'][0], payload[u'data'][1], payload[u'data'][2])

def doPose(payload):
#    print 'doPose called'
#    print payload
    p.setPose(payload[u'data'][0], payload[u'data'][1], payload[u'data'][2])


HOSTNAME = config.MQTTIP
# Subscribed topics :
TOPICNAMES = [
    ['navigation/input/target', doTarget],
    ['odometry/output/pose', doPose],
    ]

def mqttOnMessage(client, userdata, msg):
    topic = str(msg.topic)
    payload = str(msg.payload)
    #print 'received', topic, payload
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

    p = Pusher()
    client = mqtt.Client()
    client.on_connect = mqttOnConnect
    client.on_message = mqttOnMessage
    client.connect(HOSTNAME, 1883, 60)

    running = True
    lastTime = time.time()
    while running:
        client.loop()

        if (time.time()-lastTime)>1.0:
            data = {"time":time.time(), "type":"target", "data":p.getTarget()}
            client.publish(topic='navigation/output/target', payload=json.dumps(data))

            data = {"time":time.time(), "type":"steering", "data":p.getSteering()}
            client.publish(topic='navigation/output/steering', payload=json.dumps(data))
            print 'Steer: '+str(data['data'])

            data = {"time":time.time(), "type":"bearing", "data":p.getRelativeBearing()}
            client.publish(topic='navigation/output/bearing', payload=json.dumps(data))
            lastTime = time.time()

    client.close()
