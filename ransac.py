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

import config

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
RED = (255, 0, 0)
PINK = (64, 0, 0)

HOSTNAME  = config.MQTTIP
#HOSTNAME = "robert.local"
#HOSTNAME = "127.0.0.1"
TOPICNAME = "sense/output/lidar"

def draw_background(gr):
    gr.draw_background()
    gr.draw_axis()

def draw_cloud(gr, cloud):
    for data in cloud.keys():
        x = cloud[data][0]
        y = cloud[data][1]
        strength = cloud[data][2]
        """
        Zero degrees = up. Theta is counterclockwise.
        """
        pos = (-int(y), int(x))
        radius = 1
        gr.draw_circle(GRAY, pos, radius) 
        if data>350 or data<10:
            gr.draw_circle(WHITE, pos, radius) 
        if data>(90-10) and data<(90+10):
            gr.draw_circle(RED, pos, radius) 
        if data>(270-10) and data<(270+10):
            gr.draw_circle(GREEN, pos, radius) 

def prune(readings):    # remove erroneous readings from scan data
    keys = readings.keys()
    for key in keys:
        if readings[key][0]>16000 or readings[key][0]<15:
            del readings[key]
    return readings

def leastSquare(data):
    '''
    determine line (form y = mx+b) best fitting scatter data x,y
    '''
    x = data[0]
    y = data[1]
    n = len(x)
    if n==0:
        return None, None
    meanX = sum(x)/n
    meanY = sum(y)/n
    top = 0.0
    bottom = 0.0
    for i in range(0,n):
        top = top+(x[i]-meanX)*(y[i]-meanY)
        bottom = bottom + (x[i]-meanX)**2
    if abs(bottom)<0.0000001:
        bottom = 0.0000001
    m = top/bottom
    b = meanY - m*meanX
    return m, b

def distance(x, y, m , b):
    '''
    distance of a point (x, y) from line y = mx + b
    '''
    return abs(b + m*x - y)/math.sqrt(1 + m**2)

def percentageFit(data, m, b, d, tail=1000):
    '''
    percentage of points in data (x,y) set that are within d of line y=mx+b
    '''
    n = 0
    x = data[0]
    y = data[1]
    #start = 0
    #if len(data)-tail>0:
    #    start = len(data)-tail
    for i in range(0,len(data[0])):
        if distance(x[i], y[i], m, b) <= d:
            n=n+1
    return (100*n)/len(data[0])    

def bounds(data):
    '''Bounding rectangle
    '''
    x = data[0]
    y = data[1]
    minX = 100000
    maxX = -100000
    minY = 100000
    maxY = -100000
    
    for i in range(0,len(data[0])):
        if x[i]>maxX:
            maxX = x[i]
        if x[i]<minX:
            minX = x[i]
        if y[i]>maxY:
            maxY = y[i]
        if y[i]<minY:
            minY=y[i]
    return (minX, minY), (maxX, maxY)

def splitXY(cloud, start, end):
    '''
    return seperate lists of x and y coords of cloud samples between given angles
    '''
    keys = cloud.keys()
    x = []
    y = []
    for i in range(start, end):
        if i in keys:
            x.append(cloud[i][0])
            y.append(cloud[i][1])
    return x,y
    

def probableWall(cloud, start, end, d, f):
    '''
    does cloud between start and end look like a wall (f percent of points within d of least square line)?
    If so, extend angles as points remain in d of y=mx+b
    '''
    data = splitXY(cloud, start, end)
    m, b = leastSquare(data)
    if not m:
        return None, None   # No good line
    if percentageFit(data, m, b, d)<f:
        return None, None   # Too many points too far away from line.
    fit = percentageFit(data, m, b, d)
    while fit>f and end<360:
        end = end+1
        if end in cloud:
            data[0].append(cloud[end][0])
            data[1].append(cloud[end][1])
            #print fit, 'added point. Cloud length=', len(data[0])
        #print start, end
        fit = percentageFit(data, m, b, d, tail=3)
    return start, end

def findWalls(cloud):
    walls=[]
    wStart, wEnd = 0, 5     # Start looking at a 5degree section
    while wEnd<360:
        start, end = probableWall(cloud, wStart, wEnd, 15, 85) # look for wall
        if start: # found a probable wall..
            m, b = leastSquare(splitXY(cloud, start,end)) # calculate gradient/intersection of wall
            pt1, pt2 = bounds(splitXY(cloud, start, end)) # NEED A BETTER WAY!    
            myLine = line.Line(pt1, pt2)
            if m<0:
                myLine.flipX()
            walls.append(myLine)
            wStart = start
            wEnd = end
        wStart = wEnd
        wEnd = wStart+5
    return walls


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
##############################################################################################################################
'''
if __name__=="__main__":
    print 'RANSAC Hackery v1.0'
    print '=========+========='
    print 'Using data from mqtt topic', TOPICNAME    
    print
    print 'Up/down: zoom'
    print 'Q: Quit'
    print 'W: show walls'
    print 'C: show cloud'
    print 'P: print details'
    print
    cloud = False 
    
    client = mqtt.Client()
    client.on_connect = mqttOnConnect
    client.on_message = mqttOnMessage
    client.subscribe(TOPICNAME)

    client.connect(HOSTNAME, 1883, 60)

    client.loop_start()

    pygame.init()
    size = (400,400)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('RANSAC/MQTT hackery')

    done = False
    clock = pygame.time.Clock()

    startAngle = 15
    endAngle = 25
    wStart, wEnd = None, None

    displayZoom = .10
    displayRotate = 0
    threshold = 0.100

    showCloud = True
    showWalls = True

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
                if event.key == pygame.K_w:
                    showWalls = not showWalls
                if event.key == pygame.K_c:
                    showCloud = not showCloud
                if event.key == pygame.K_p:
                    print 'Walls'
                    print '====='
                    for wall in allWalls:
                        print wall.asText()
                    print
                        
                if event.key == pygame.K_q:
                    done = True 
        if cloud:
            draw_background(myGraph)
            allWalls = findWalls(cloud)
            if showCloud:
                draw_cloud(myGraph, cloud)
            if showWalls:
                for wall in allWalls:
                    #myGraph.draw_line_mb(PINK, m, b, 1)  # draw the extended wall
                    myGraph.draw_Line(RED, wall, 2, rh=True)  # draw the wall                    

        screen.blit(myGraph.surface, (0,0))
        pygame.display.flip()

        clock.tick(5)  # limit to 10 fps (plenty fast enough)

    client.loop_stop()
    pygame.quit()
