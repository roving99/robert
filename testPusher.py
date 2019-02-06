#!/usr/bin/python
# Test 'pusher' maths..

import pusher
import math

#         
#		 	x
#			^
#			|
#			|		Theta counterclockwise from x axis.
#	y <-----+  
#

p = pusher.Pusher()

p.setPose(50.0, 50.0, 0.0)  # Origin, straight ahead

p.setTarget(100.0, 100.0, math.pi/4) # 45degrees to right

print '   Pose: '+str(p.getPose())
print
print ' Target: '+str(p.getTarget())
print 'Bearing: '+str(p.getBearing())
print
p.setTarget(0,100,0)
print ' Target: '+str(p.getTarget())
print 'Bearing: '+str(p.getBearing())
print
p.setTarget(100,0,0)
print ' Target: '+str(p.getTarget())
print 'Bearing: '+str(p.getBearing())
print
p.setTarget(-100,50,0)
print ' Target: '+str(p.getTarget())
print 'Bearing: '+str(p.getBearing())
print
p.setTarget(-100,-50,0)
print ' Target: '+str(p.getTarget())
print 'Bearing: '+str(p.getBearing())
print
p.setTarget(50,-100,0)
print ' Target: '+str(p.getTarget())
print 'Bearing: '+str(p.getBearing())
print

