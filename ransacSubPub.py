#!/usr/bin/python
import neato
import sys
import pygame
import math
import os
import importlib
import graph
import paho.mqtt.client as mqtt
import time
import json
import line
import cloud as clouds 
import config

HOSTNAME = config.MQTTIP
TOPICNAME = "sense/output/lidar"
'''
publish to:
ransac/output/walls
ransac/output/corners
ransac/output/forces
'''

def mqttOnMessage(client, userdata, msg):
    global cloud
  #  print 'received', str(msg.topic), str(msg.payload)
    payload = json.loads(msg.payload)
    uCloud = payload['data'] # unicode keys
    cloud = {}
    for key in uCloud.keys(): # json converts int keys to unicode. change back to ints..
       cloud[int(key)]=uCloud[key]

def mqttOnConnect(client, userdata, flags, rc):  # added 'flags' on work version of library?
    print("Connected with result code "+str(rc))
    # re subscribe here?
    client.subscribe(TOPICNAME)    


cloud = False 
done = False
    
client = mqtt.Client()
client.on_connect = mqttOnConnect
client.on_message = mqttOnMessage
client.subscribe(TOPICNAME)

client.connect(HOSTNAME, 1883, 60)

client.loop_start()


startAngle = 5
endAngle = 20

while not done:
    if cloud:
        timeNow = time.time()
        print timeNow, 'Received sense/output/lidar'
        
        walls = clouds.findWalls(cloud, startAngle,endAngle)                     
        longWalls = clouds.pruneByLength(walls,200)
        corners = clouds.findCorners(walls)
        force = clouds.forcePush(cloud)
        forceResultant = clouds.CofG(clouds.splitXY(force,0,360))

        print time.time(), 'Publishing ransac/ walls, corners, force.'
        longWallsAsLists = []
        for wall in longWalls:
            longWallsAsLists.append(wall.asList())      # convert wall objects to lists (x1,y1, x2,y2)
        data = {"time":timeNow, "type":"walls", "data":longWallsAsLists}
        client.publish(topic="ransac/output/walls", payload=json.dumps(data))

        data = {"time":timeNow, "type":"corners", "data":corners} # corner points are already lists (x,y)  
        client.publish(topic="ransac/output/corners", payload=json.dumps(data))

        data = {"time":timeNow, "type":"force", "data":force}   # force points are lists (x, y, percent)
        client.publish(topic="ransac/output/force", payload=json.dumps(data))
        
        print time.time(), 'Took',time.time()-timeNow, 's.'
    
    cloud = False
client.loop_stop()
