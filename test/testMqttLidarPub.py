
#!/usr/bin/python

import paho.mqtt.client as mqtt
import time
import sys
import pygame
import math
import os
import importlib
import json

sys.path.append(r'..')

import neato
import graph

#MQTT_SERVER = "192.168.0.8"
MQTT_SERVER = "127.0.0.1"

TOPICNAME = "sense/output/lidar"

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
RED = (255, 0, 0)

def draw_background(gr):
    gr.draw_background()

def draw_cloud(gr, cloud):
    for data in cloud.keys():
        x = cloud[data][0]
        y = cloud[data][1]
        strength = cloud[data][2]
        pos = (int(x), int(y))
        radius = 1
        gr.draw_circle(PURPLE, pos, radius) 

def prune(readings):    # remove erroneous readings from scan data
    keys = readings.keys()
    for key in keys:
        if readings[key][0]>16000 or readings[key][0]<10 or (int(key)>8 and int(key)<55): # remove robot body shadow (10-40degrees) also.
            del readings[key]
    return readings

def mqttOnConnect(client, userdata, rc, tmp):
    print("Connected with result code "+str(rc))

def mqttOnMessage(client, userdata, msg):
    print 'received', str(msg.topic), str(msg.payload)


if __name__=="__main__":
    print 'TEST LIDAR MQTT Publisher'
    print '============+============'
    print

    if os.path.isfile(sys.argv[1]+'.py'):
        updating = False
        myNeato = None
        test = importlib.import_module(sys.argv[1])
        readings = test.data
        print 'Using test data set', sys.argv[1]
        print 'data=',readings
    else:
        print 'Usage : testMqttLidarPub.py <test_data_file>'
        sys.exit()
        
    client = mqtt.Client()
    client.on_connect = mqttOnConnect
    client.on_message = mqttOnMessage

    client.connect(MQTT_SERVER, 1883, 60)

    pygame.init()
    size = (400,400)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('LIDAR data on '+TOPICNAME)

    done = False
    clock = pygame.time.Clock()

    prune(readings)
    cloud = neato.toCloud(readings)

    displayZoom = .10
    displayRotate = 0
    threshold = 0.100

    myGraph = graph.Graph((400, 400), origin=(200,200), scale=displayZoom)

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    displayZoom = displayZoom-0.02
                    myGraph.scale=displayZoom
                if event.key == pygame.K_DOWN:
                    displayZoom = displayZoom+0.02
                    myGraph.scale=displayZoom
                if event.key == pygame.K_q:
                    done = True 

        if updating:
            readings = myNeato.getScan()
            rpm = myNeato.getRPM()
            prune(readings)
            cloud = neato.toCloud(readings)
        
        draw_background(myGraph)
        draw_cloud(myGraph, cloud)

        screen.blit(myGraph.surface, (0,0))
        pygame.display.flip()

        data = {"time":time.time(), "type":"lidar", "data":cloud}
        client.publish(topic=TOPICNAME, payload=json.dumps(data))

        clock.tick(10)  # limit to 10 fps (plenty fast enough)

    pygame.quit()
