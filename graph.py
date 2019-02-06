#!/usr/bin/python
"""Draw graphs in pygame window.

^ y
|
|
+----> x

"""

import sys
import pygame
import math
import os
import line

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
RED = (255, 0, 0)


class Graph(object):
    def __init__(self, size, origin=(10,10), scale =1.0):
        self.high = size[1] # pix
        self.wide = size[0] # pix
        self.ox = origin[0] # pix
        self.oy = origin[1] # pix
        self.scale = scale 
        self.surface = pygame.Surface((self.wide, self.high))

    def dpos(self, pos):
        '''
        return position in pixels on surface
        '''
        x = pos[0]
        y = pos[1]
#        px = x*self.scale+self.ox
#        py = self.high-(y*self.scale+self.oy)
        px = self.ox+x*self.scale
        py = self.oy-y*self.scale
        return int(px), int(py)

    def mouseToGraph(self, pos):
        # mouse pos is from top left in pixels.
        x = pos[0]
        y = pos[1]
        gx = (x-self.ox)/self.scale
        gy = -(y-self.oy)/self.scale
        return int(gx), int(gy)

    def draw_axis(self):
        pygame.draw.line(self.surface, GRAY, self.dpos((-20000,0)), self.dpos((20000,0)), 1)
        pygame.draw.line(self.surface, WHITE, self.dpos((0,-20000)), self.dpos((0,20000)), 1)
        #pygame.draw.circle(self.surface, WHITE, self.dpos((0,0)), 10)

    def draw_background(self):
        self.surface.fill(BLACK)

    def draw(self):
        self.draw_background()
        self.draw_axis()

    def draw_circle(self, colour, pos, radius):
        pygame.draw.circle(self.surface, colour, self.dpos(pos), radius)

    def draw_line(self, colour, pos1, pos2, thickness):
        pygame.draw.line(self.surface, colour, self.dpos(pos1), self.dpos(pos2), thickness)

    def draw_Line(self, colour, line, thickness, rh=False):
        if rh:
            pygame.draw.line(self.surface, colour, self.dpos((-line.y1, line.x1)), self.dpos((-line.y2, line.x2)), thickness)
        else:
            pygame.draw.line(self.surface, colour, self.dpos((line.x1, line.y1)), self.dpos((line.x2, line.y2)), thickness)

    def maxX(self):
        return (self.wide-self.ox)/self.scale
    
    def minX(self):
        return -(self.ox)/self.scale

    def draw_line_mb(self, colour, m, b, thickness):
        if m:
            self.draw_line(colour, (self.minX(), self.minX()*m+b), (self.maxX(), self.maxX()*m+b), thickness)

####################################################################################

if __name__=="__main__":
    def draw_background(screen, rotate=0, zoom=0.25):
        screen.fill(GRAY)

    def leastSquare(data):
        '''
        determine line (form y = mx+b) best fitting scatter data x,y
        '''
        x = data[0]
        y = data[1]
        n = len(x)
        meanX = sum(x)/n
        meanY = sum(y)/n
        top = 0.0
        bottom = 0.0
        for i in range(0,n):
            top = top+(x[i]-meanX)*(y[i]-meanY)
            bottom = bottom + (x[i]-meanX)**2
        m = top/bottom
        b = meanY - m*meanX
        return m, b


    print 'GRAPH v1.0'
    print '=========+========='
    print

    testX = (8,2,11,6,5,4,12,9,6,1, -10)
    testY = (3,10,3,6,8,12,1,4,9,14, -5)
    print testX
    print testY
    print leastSquare( (testX, testY) ), 'should be (-1.1, 14.0)'
    print


    pygame.init()
 
    size = (600,600)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('GRAPH hackery')

    done = False
    clock = pygame.time.Clock()

    displayZoom = 10
    myGraph = Graph((400,400), origin=(200,200), scale=displayZoom)

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    displayZoom = displayZoom-5
                if event.key == pygame.K_DOWN:
                    displayZoom = displayZoom+5
                if event.key == pygame.K_q:
                    done = True 
        
        draw_background(screen)
        myGraph.draw()
        n = len(testX)
        for i in range(0,n):
            myGraph.draw_circle(RED, (testX[i], testY[i]), 2)
        m, b = leastSquare((testX, testY))
        myGraph.draw_line_mb(WHITE, m, b, 1)
        screen.blit(myGraph.surface, (100,100))
        pygame.display.flip()

        clock.tick(10)  # limit to 10 fps (plenty fast enough)

    pygame.quit()
