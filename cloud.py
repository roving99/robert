#!/usr/bin/python
import sys
import pygame
import math
import os
import importlib
import graph
import time
import json
import line
import neato    # need .toCloud(readings)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
RED = (255, 0, 0)
PINK = (64, 0, 0)
BLUE = (0,0,255)

def draw_background(gr):
    gr.draw_background()
            
def draw_cloud(gr, cloud):
    for data in cloud.keys():
        x = cloud[data][0]
        y = cloud[data][1]
        strength = cloud[data][2]
        pos = (int(x), int(y))
#        pos = (int(y), int(x))
        radius = 2
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

def CofG(data):
    '''
    Centre of gravity of the cloud data.
    '''
    x = data[0]
    y = data[1]
    n = len(x)
    tx = 0.0
    ty = 0.0
    for i in range(0,n):
        tx+=x[i]
        ty+=y[i]
    return tx/n, ty/n


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
    '''
    Bounding rectangle around given data. pt1 = bottom left, pt2 = top right
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

def findWalls(cloud, startAngle, endAngle):
    wStart, wEnd = startAngle, endAngle
    walls = []
    while wEnd<360:
        start, end = probableWall(cloud, wStart, wEnd, 15, 95) # look for wall
        if start: # found a wall..
            XY = splitXY(cloud, start, end)
            m, b = leastSquare(XY) # calculate gradient/intersection of wall

            farAway = 10000000
            pt1 = (-farAway, (-farAway*m)+b)
            pt2 = (farAway, farAway*m+b)
            longLine = line.Line(pt1, pt2) # long line best fit to data

            pt1, pt2 = bounds(XY) 
            # gradient of line between corners of the bound rectangle is always positive
            if m<0.0: # gradient is reversed
                myPt1 = longLine.closestPoint(pt2[0], pt1[1])
                myPt2 = longLine.closestPoint(pt1[0], pt2[1])
            else:
                myPt1 = longLine.closestPoint(pt1[0], pt1[1])
                myPt2 = longLine.closestPoint(pt2[0], pt2[1])
            myLine = line.Line(myPt1, myPt2)

            walls.append(myLine)

            wStart = start
            wEnd = end
        wStart = wEnd
        wStart = wStart+(wEnd-wStart)/2
        wEnd = wStart+5
    return walls

def pruneByLength(walls, l):
    result = []
    for wall in walls:
        if wall.length()>=l:
            result.append(wall)
    return result

def findCorners(walls):
    result = []
    for i in range(0,len(walls)-1):
        for j in range(i,len(walls)-1):
            if walls[i].perpendicularTo(walls[j], err=10) and walls[i].distance(walls[j])<300:
                result.append(walls[i].intersect(walls[j]))
    return result

'''
##############################################################################################################################
'''
if __name__=="__main__":
    print 'Cloud Module'
    print '=====+======'   
    print
    print 'Using readings from', sys.argv[1]
    testData = importlib.import_module(sys.argv[1])
    readings = testData.data
    print 'length:', len(readings)
    print readings
    prune(readings)
    print 'Pruned readings:'
    print 'length:', len(readings)
    cloud = neato.toCloud(readings)
    print 'Cloud:'
    print 'length:', len(cloud)
    print cloud 

    pygame.init()
    size = (1000,1000)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Cloud hackery')

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
                if event.key == pygame.K_LEFT:
                    startAngle+=5
                if event.key == pygame.K_RIGHT:
                    startAngle-=5
                                
                if event.key == pygame.K_q:
                    done = True 
        endAngle = startAngle+5
        
        if cloud:
            draw_background(myGraph)
            if showCloud:
                draw_cloud(myGraph, cloud)

            walls = findWalls(cloud, startAngle,endAngle)
            longWalls = pruneByLength(walls,200)
            corners = findCorners(walls)
            cofg = CofG(splitXY(cloud,0,360))
#            print 'walls:', len(walls), '  corners:', len(corners)
            if showWalls:
                for wall in walls:
                    myGraph.draw_Line(RED, wall, 1)  # draw the wall                    
                for wall in longWalls:
                    myGraph.draw_Line(GREEN, wall, 2)  # draw the wall                    
            for corner in corners:
                myGraph.draw_circle(BLUE, corner, 4)
            myGraph.draw_circle(GRAY, corner, 10) 

        myGraph.draw_circle(WHITE,(0,0), 10)

        screen.blit(myGraph.surface, (0,0))
        pygame.display.flip()

        clock.tick(5)  # limit to 10 fps (plenty fast enough)

    client.loop_stop()
    pygame.quit()
