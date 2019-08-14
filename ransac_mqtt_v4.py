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

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
RED = (255, 0, 0)
PINK = (64, 0, 0)

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
            

def prune(readings):    # remove erroneous readings from scan data
    keys = readings.keys()
    for key in keys:
        if readings[key][0]>16000 or readings[key][0]<10:
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

def spread(data): 
    '''
    Average distance between points
    '''
    x = data[0]
    y = data[1]
    n = len(x)
    total = 0.0
    for i in range(1,n):
        dx = x[i]-x[i-1]
        dy = y[i]-y[i-1]
        total = total + math.sqrt(dx*dx + dy*dy)
    return total/n

def pointDistance(p1, p2):
    '''
    distance between two points
    '''
    dx = p2[0]-p1[0]
    dy = p2[1]-p1[1]
    return math.sqrt(dx*dx + dy*dy)

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
    

def probableWall(cloud, start, end, d, f):
    '''
    does cloud between start and end look like a wall (f percent of points within d of least square line)?
    If so, extend angles as points remain in d of y=mx+b
    '''

    data = splitXY(cloud, start, end)
    m, b = leastSquare(data)

    if not m:
        return None, None   # No good line

    if len(data[0])<2:
        return None, None   # Too few points to make a reasonable guess

    fit = percentageFit(data, m, b, d)
    aveDistance = spread(data)      # average distance between points.

#    if aveDistance>50.0:            # points are too spread out for a good match
#        return None, None

    if fit<f:
        return None, None   # Too many points too far away from line in first sample.

    while fit>f and end<360:
        end = end+1
        if end in cloud:
            lastPoint = (data[0][-1:][0], data[1][-1:][0])
            newPoint = (cloud[end][0], cloud[end][1])
            if pointDistance(lastPoint, newPoint)>aveDistance*3.0:
                return start, end-1                     # if next point is toooo far away, exit
            data[0].append(cloud[end][0])
            data[1].append(cloud[end][1])
            aveDistance = spread(data)
            fit = percentageFit(data, m, b, d, tail=3)

    return start, end

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
    endAngle = 25
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
            print len(cloud)
            draw_background(myGraph)
#            draw_lidar(myGraph, readings)
            if showCloud:
                draw_cloud(myGraph, cloud)

            wStart, wEnd = 0, 20
            while wEnd<360:
                start, end = probableWall(cloud, wStart, wEnd, 15, 85) # look for wall
                if start: # found a wall..
                    m, b = leastSquare(splitXY(cloud, start,end)) # calculate gradient/intersection of wall
                    pt1, pt2 = bounds(splitXY(cloud, start, end))    
                    myLine = line.Line(pt1, pt2)
                    if m<0:
                        myLine.flipX()
                    if showWalls:
#                        myGraph.draw_line_mb(PINK, m, b, 1)  # draw the extended wall
                        myGraph.draw_Line(RED, myLine, 2)  # draw the wall                    
                    wStart = start
                    wEnd = end
                wStart = wEnd
                wEnd = wStart+5

        myGraph.draw_circle(WHITE,(0,0), 10)

        screen.blit(myGraph.surface, (0,0))
        pygame.display.flip()

        clock.tick(5)  # limit to 10 fps (plenty fast enough)

    client.loop_stop()
    pygame.quit()
