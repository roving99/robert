import time
import math

class RobotBase():

    def __init__(self, axleLength, wheelCircumference, countsPerWheel):
        """
        Two wheeled robot base.
        x is forward of Robot.
        y is leftward.
        theta is counterclockwise.
        """
        self.wheel_spacing= axleLength
        self.wheel_circumference=wheelCircumference	# cm	
        self.wheel_counts_per_rev = countsPerWheel 

        self.cm_per_tick = (self.wheel_circumference/self.wheel_counts_per_rev)  # distance moved in a step
        self.full_circle =  self.wheel_counts_per_rev*((self.wheel_spacing*math.pi)/self.wheel_circumference) # ticks to turn base 360 degrees

        self._lastTranslate = 0.0
        self._lastRotate = 0.0
        self.last_encoder1 = 0
        self.last_encoder2 = 0
        self.encoder1 = 0
        self.encoder2 = 0
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.reset()

    def reset(self):
        """
        reset robot. zero location.
        """
        self._lastTranslate = 0
        self._lastRotate = 0
        self.last_encoder1 = 0
        self.last_encoder2 = 0
        self.encoder1 = 0
        self.encoder2 = 0
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

    def update(self, encoder1, encoder2):       # calculate new X, Y, Theta 
        self.encoder1 = encoder1
        self.encoder2 = encoder2

        left_ticks   = self.encoder1 - self.last_encoder1
        #right_ticks  = -(self.encoder2 - self.last_encoder2)
        right_ticks  = (self.encoder2 - self.last_encoder2)
        # NON INVERTED #
        self.last_encoder1 = self.encoder1
        self.last_encoder2 = self.encoder2
        
        dist_left   = float(left_ticks) * self.cm_per_tick;
        dist_right  = float(right_ticks) * self.cm_per_tick;
        if (dist_left!=0 or dist_right!=0): # did we move?
            cos_current = math.cos(self.theta);
            sin_current = math.sin(self.theta);
            right_minus_left = float(dist_right-dist_left);
                
            if (left_ticks == right_ticks):            # Moving in a straight line 
                self.x += dist_left*cos_current
                self.y += dist_left*sin_current
            else:                                      # Moving in an arc 
                expr1 = self.wheel_spacing * float(dist_right + dist_left) / 2.0 / float(dist_right - dist_left);
                right_minus_left = dist_right - dist_left
                self.x     += expr1 * (math.sin(right_minus_left/self.wheel_spacing + self.theta) - sin_current)
                self.y     -= expr1 * (math.cos(right_minus_left/self.wheel_spacing + self.theta) - cos_current)
                self.theta += right_minus_left / self.wheel_spacing
                
            if (self.theta<0.0):     
                self.theta = (2*math.pi)+self.theta
            if (self.theta>=(2*math.pi)):
                self.theta = self.theta-(2*math.pi)
        
    def getTranslate(self):
        return self._lastTranslate

    def getRotate(self):
        return self._lastRotate

    def translateCmToSteps(self,cm):
        return [int(cm/self.cm_per_tick), -int(cm/self.cm_per_tick)]

    def rotateRadiansToSteps(self, radians):
        arc = int((radians/(2.0*math.pi))*self.full_circle)
        return [-arc, -arc]
