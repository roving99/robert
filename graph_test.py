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
import graph

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)


def draw_background(screen, rotate=0, zoom=0.25):
    screen.fill(GRAY)

print 'GRAPH TEST 1.0'
print '====+========='
print
print 'RED line - X axis positive. 500 long arrow'
print 'GREEN line - Y axis positive. 500 long arrow'
print 'BLUE line - m=0.5, b=100 y = mx+b.'
print 'Circle centre at 100,100, r=100'

pygame.init()

size = (1200,1200)
screen = pygame.display.set_mode(size)
pygame.display.set_caption('GRAPH hackery')

done = False
clock = pygame.time.Clock()

displayZoom = 1
myGraph = graph.Graph((1200,1200), origin=(600,600), scale=displayZoom, robot=True)

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                displayZoom = displayZoom-.05
            if event.key == pygame.K_DOWN:
                displayZoom = displayZoom+.05
            if event.key == pygame.K_q:
                done = True 
    
    draw_background(screen)
    myGraph.draw()
    myGraph.draw_line(GREEN, (0,0),(0,500), 3) # Y axis
    myGraph.draw_line(GREEN, (0,500),(-30,500-60), 3) # Y axis
    myGraph.draw_line(GREEN, (0,500),(30,500-60), 3) # Y axis

    myGraph.draw_line(RED, (0,0),(500,0), 3) # X axis
    myGraph.draw_line(RED, (500,0),(500-60,30), 3) # X axis
    myGraph.draw_line(RED, (500,0),(500-60,-30), 3) # X axis

    myGraph.draw_line_mb(BLUE, 0.5, 100, 3) # y = 0.5x+100

    myGraph.draw_circle(WHITE, (100,100), 100)

    screen.blit(myGraph.surface, (0,0))
    pygame.display.flip()

    clock.tick(1)  # limit to 1 fps (plenty fast enough)

pygame.quit()
