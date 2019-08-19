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

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
RED = (255, 0, 0)
PINK = (64, 0, 0)
BLUE = (0, 0, 255)

HOSTNAME = "localhost"
HOSTNAME = "robert.local"
#HOSTNAME = "192.168.0.10"
TOPICNAME = "sense/output/lidar"

def draw_background(gr):
    gr.draw_background()

def draw_lidar(gr, readings):
    for data in readings.keys():
        angle = math.radians(data)
        distance = readings[data][0]
        strength = readings[data][1]
#        pos = (int(math.cos(angle)*distance), int(math.sin(angle)*distance)) 
        pos = (int(math.sin(angle)*distance), int(math.cos(angle)*distance)) 
        radius = 1
        gr.draw_circle(GREEN, pos, radius) 
        gr.draw_line(GRAY, (0, 0), pos, 1)
#        if data==180 or data==160:
#        if data>=startAngle and data<=endAngle:
#           gr.draw_line(WHITE, (0, 0), pos, 1)
            
def draw_cloud(gr, cloud):
    for data in cloud.keys():
        x = cloud[data][0]
        y = cloud[data][1]
        strength = cloud[data][2]
        pos = (int(x), int(y))
#        pos = (int(y), int(x))
        radius = 1
        gr.draw_circle(PURPLE, pos, radius) 
        if wStart:
            if data>=wStart and data<=wEnd:
                gr.draw_line(RED, (0, 0), pos, 1)
        if data>=startAngle and data<=endAngle:
            gr.draw_line(WHITE, (0, 0), pos, 1)
            
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
            draw_background(myGraph)
            if showCloud:
                draw_cloud(myGraph, cloud)

            walls = clouds.findWalls(cloud, startAngle,endAngle)                     
            longWalls = clouds.pruneByLength(walls,200)
            corners = clouds.findCorners(walls)
            cofg = clouds.CofG(clouds.splitXY(cloud,0,360))
            if showWalls:
                for wall in walls:
                    myGraph.draw_Line(RED, wall, 1)  # draw the wall                    
                for wall in longWalls:
                    myGraph.draw_Line(GREEN, wall, 2)  # draw the wall                    
                for corner in corners:
                    myGraph.draw_circle(BLUE, corner, 4)

            myGraph.draw_circle(GRAY, cofg, 10) 

        myGraph.draw_circle(WHITE,(0,0), 10)

        screen.blit(myGraph.surface, (0,0))
        pygame.display.flip()

        clock.tick(5)  # limit to 10 fps (plenty fast enough)

    client.loop_stop()
    pygame.quit()
