import math
import graph
import pygame

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (64, 64, 64)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
RED = (255, 0, 0)

'''
line segment library.
A line segment exists between two points.
It has a gradient and and length
'''

class Line(object):
	'''
	Line segment between two points.
	'''
	def __init__(self, pt1, pt2):
		'''
		Accepts two points.
		'''
		if pt2[0]>pt1[0]:
			self.x1 = pt1[0]
			self.y1 = pt1[1]
			self.x2 = pt2[0]
			self.y2 = pt2[1]
		else:
			self.x1 = pt2[0]
			self.y1 = pt2[1]
			self.x2 = pt1[0]
			self.y2 = pt1[1]

		self.update()

	def length(self):
		'''Length of line.'''
		return math.sqrt((self.x2-self.x1)*(self.x2-self.x1) + (self.y2-self.y1)*(self.y2-self.y1))

	def flipX(self): 
		'''Flip along X axis.'''
		t = self.y1
		self.y1 = self.y2
		self.y2 = t

	def gradient(self):
		'''Line gradient. Min=0.0000001'''
		dx = abs(self.x2-self.x1)
		if dx<0.0000001:
			dx = 0.0000001
		result = float(self.y2-self.y1)/dx
		return result

	def intersection(self):
		'''Axis intersection (b) of line.'''
		# y = mx+b, b = y-mx
		return self.y1-self.gradient()*self.x1

	def parallelDistance(self, l):
		'''Distance between this and another, parrallel line.'''
		return abs(self.intersection()-l.intersection())/math.sqrt(self.gradient()*self.gradient()+1.0)

	def angle(self):
		'''Angle of line (degrees).'''
		return math.degrees(math.atan(self.gradient()))

	def parallelTo(self, l, err=3):
		'''Is a line parrallel to this (within err degrees)?'''
		return abs(self.angleTo(l))<err

	def perpendicularTo(self, l, err=3):
		'''Is a line perpendicular to this (within err degrees)?'''
		return abs(self.angleTo(l)-90)<err

	def angleTo(self, l):
		'''Angle between this and line L.'''
		a = abs(self.angle()-l.angle())
		if a>180:
			a=a-180
		return a

	def intersect(self, l):
		'''Point where this and line L intersect.
		Returns (10000000,1000000) if parallel.'''
		a = self.gradient()
		b = l.gradient()
		c = self.intersection()
		d = l.intersection()

		if (a==b): # parallel
			return 100000000,1000000000
		else:
			return ((d-c)/(a-b)), ((a*d-b*c)/(a-b))

	def closestPoint(self, x, y):
		'''Point on line closest to (x,y).
		'''
		m = -1.0/self.gradient() # gradient of line perpendicular to line
		b = y - m*x # intersect of a line perpendicular to line
		x2 = 0
		y2 = b # point on axis
		line2 = Line((x,y), (x2,y2)) # line segment from origin to point
		return self.intersect(line2) # intersection of orignal line and our calculated line.

	def distance(self, l):
		shortest = (self.x1-l.x1)*(self.x1-l.x1) + (self.y1-l.y1)*(self.y1-l.y1)
		next = (self.x1-l.x2)*(self.x1-l.x2) + (self.y1-l.y2)*(self.y1-l.y2)
		if next<shortest:
			shortest=next
		next = (self.x2-l.x2)*(self.x2-l.x2) + (self.y2-l.y2)*(self.y2-l.y2)
		if next<shortest:
			shortest=next
		next = (self.x2-l.x1)*(self.x2-l.x1) + (self.y2-l.y1)*(self.y2-l.y1)
		if next<shortest:
			shortest=next
		return math.sqrt(shortest)		

	def asText(self):
		'''As pair of points.'''
		return 'line(('+str(self.x1)+', '+str(self.y1)+'),('+str(self.x2)+', '+str(self.y2)+'))'

	def update(self):
		pass


if __name__=="__main__":

	lines = [
		Line((5,2), (10,8)),
		Line((11,8), (6,2)),
		#Line((-5,2), (-10,8)),
		#Line((5,-2), (10,-8)),
		#Line((-5,-2), (-10,-8)),
		Line((0,0), (1,1)),
		Line((0,0,), (0,1)),
		Line((0,0,), (1,0)),
		]

	pygame.init()
	clock = pygame.time.Clock()

	size = (600,600)
	screen = pygame.display.set_mode(size)
	pygame.display.set_caption('Line class')
	displayZoom = 10
	myGraph = graph.Graph((300,300), origin=(150,150), scale=displayZoom)

	done = False

	for line in lines:
		print line.asText(), ' length:',line.length(), ' grad:', line.gradient(), ' angle:', line.angle()
	
	for line in lines:
		for line2 in lines:
			print line.asText(), line2.asText(), 'parr:', line.parallelTo(line2), ' perp:', line.perpendicularTo(line2), 'pdist:', line.parallelDistance(line2), 'int:', line.intersect(line2)

	print lines[0].distance(lines[1])

	while not done:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				done = True
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q:
					done = True

		screen.fill(PURPLE)
		myGraph.draw()

		for line in lines:
			myGraph.draw_line(WHITE, (line.x1, line.y1), (line.x2, line.y2), 1)

		screen.blit(myGraph.surface, (100,100))
		pygame.display.flip()

		clock.tick(10)  # limit to 10 fps (plenty fast enough)

	pygame.quit()