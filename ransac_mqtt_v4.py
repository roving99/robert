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

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
RED = (255, 0, 0)
PINK = (64, 0, 0)
BLUE = (0, 0, 255)

HOSTNAME = config.MQTTIP
TOPICNAME = "sense/output/lidar"


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


'''
#########################################################################
'''
if __name__=="__main__":
    print 'RANSAC Hackery v4.0'
    print '=========+========='
    print 'Using data from mqtt topic', TOPICNAME    
    print
    cloud = False 
    
    client = mqtt.Client()
    client.on_connect = mqttOnConnect
    client.on_message = mqttOnMessage
    client.subscribe(TOPICNAME)

    client.connect(HOSTNAME, 1883, 60)

    client.loop_start()

    pygame.init()
    size = (1000,1000)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('RANSAC/MQTT hackery')

    done = False
    clock = pygame.time.Clock()

    startAngle = 15
    endAngle = 35
    wStart, wEnd = None, None

    displayZoom = .10
    displayRotate = 0
    threshold = 0.100

    showCloud = True
    showWalls = True

    myGraph = graph.Graph((1000, 1000), origin=(500,500), scale=displayZoom, robot=True)

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
                if event.key == pygame.K_w:
                    showWalls = not showWalls
                if event.key == pygame.K_c:
                    showCloud = not showCloud
                        
                if event.key == pygame.K_q:
                    done = True 
        if cloud:
            clouds.draw_background(myGraph)
            if showCloud:
                clouds.draw_cloud(myGraph, cloud)

            walls = clouds.findWalls(cloud, startAngle,endAngle)                     
            longWalls = clouds.pruneByLength(walls,200)
            corners = clouds.findCorners(walls)
            cofg = clouds.CofG(clouds.splitXY(cloud,0,360))
            coff = clouds.CofF(clouds.splitXY(cloud,0,360))
            force = clouds.forcePush(cloud)
            forceResultant = clouds.CofG(clouds.splitXY(force,0,360))
            if showWalls:
                for wall in walls:
                    myGraph.draw_Line(RED, wall, 1)  # draw the wall                    
                for wall in longWalls:
                    myGraph.draw_Line(GREEN, wall, 2)  # draw the wall                    
            for corner in corners:
                myGraph.draw_circle(BLUE, corner, 4)
            clouds.draw_force(myGraph, force)

            myGraph.draw_circle(GRAY, cofg, 10)     # centre of point cloud.

            myGraph.draw_circle(RED, (forceResultant[0]*100, forceResultant[1]*100), 10)  # 'push' from obsticles.

        myGraph.draw_circle(WHITE,(0,0), int(150*displayZoom))  # Robert (approx 30cm diameter)
        myGraph.draw_empty_circle(GRAY, (0, 0), int(2000*displayZoom), 1)   # Force zone

        screen.blit(myGraph.surface, (0,0))
        pygame.display.flip()

        clock.tick(10)  # limit to 10 fps (plenty fast enough)

    client.loop_stop()
    pygame.quit()
