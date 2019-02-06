#!/usr/bin/python

import sys
import time
import math
import select
import serial

class Neato():
    """
    Object to read output of Neato Lidar attached by serial.
    Outputs a scan (radial data) or point cloud.
    Dimensions are degrees and mm.
        import sys
        import time
        import math
        import select
        import serial
    """
    def __init__(self, portName, baud, offset=267):
        """
        Opens a serial port.
        offset accounts for Lidar data not being aligned with Robert x axis (0degree not pointing forward).
        """
        self.portName = portName
        self.baud = baud
        self.port = None
        self.offset = 0
        self.scan = {}
        self.cloud = {}

        try:
            self.port = serial.Serial(portName, baud, timeout=1)
#            print self.port
        except:
            self.port = None

    def isOpen(self):
        """
        Is serial port open?
        """
        if self.port:
            return True
        else:
            return False

    def send(self, command):
        """
        Send a command string to Neato. Unused.
        """
        self.port.write(command+'\r\n')         # write IS blocking.
        text = self.port.readline()
        return text

    def close(self):
        """
        Close serial port.
        """
        try:
            self.port.close()
        except:
            pass
        self.port = None

    def read(self):     # BLOCKING!!
        """
        Read a byte from the port.
        """
        byte = self.port.read()
        while byte=='':
            byte = self.port.read()
        return byte

    def dump(self, length):
        """
        Dump <length> bytes from Neato to stdio. Used for debugging.
        """
        count = 0
        byte = self.read()
        while count<length:
            print(byte.encode('hex')),
            count = count+1
            byte = self.read()

    def getRPM(self):
        """
        Waits for a packet, and returns reported RPM.
        """
        state = 0 # waiting
        while state==0:
            byte = self.read()
            if ord(byte)==0xFA:
                state = 1 # start of packet
        index = self.read()
        rpm = ord(self.read())
        rpm = (rpm + 256*ord(self.read()))/64
        return rpm

    def getHeader(self):
        """
        Wait for start of header.
        Return index of packet and RPM.
        """
        state = 0 # waiting
        while state==0:
            byte = self.read()
            if ord(byte)==0xFA:
                state = 1 # start of packet
        index = ord(self.read())-0xA0
        rpm = ord(self.read())
        rpm = (rpm + 256*ord(self.read()))/64
        return index, rpm

    def getData(self):
        """
        read data from packet.
        Return distance and strength.
        """
        distance = ord(self.read())
        r = ord(self.read())
        distance = distance + 256*(r&0b00111111)
        if (r&0b11000000):  # error of some kind - set distance to 0
            distance = 0
        strength = ord(self.read())
        strength = strength + 256*ord(self.read())
        return distance, strength

    def getChecksum(self):
        """
        Read checksum from end of packet.
        """
        checksum = ord(self.read())
        checksum = checksum + 256*ord(self.read())
        return checksum

    def getPacket(self):
        """
        Wait for and read next packet.
        Return ((index, rpm), (dist, str), (dist, str), (dist, str), (dist, str), chksum)
        """
        h = self.getHeader()
        d1 = self.getData()
        d2 = self.getData()
        d3 = self.getData()
        d4 = self.getData()
        c  = self.getChecksum()
        return h, d1, d2, d3, d4, c
#       ((index, rpm), (dist, str), (dist, str), (dist, str), (dist, str), chk)

    def getScan(self):
        """
        Scan - hash of angles (degree) and (distance, strength).
        stored in object.
        """
        count = 0
        while count<100:
            packet = self.getPacket()
            """
            0degrees points to front of Robert, and angles run counterclockwise
            """
            angle = (packet[0][0]*4+self.offset)%360

            if packet[1][0]<32000:      # if distance is >2**13 there was a error - invalid data or poor strength
                self.scan[angle] = packet[1]
            if packet[2][0]<32000:
                self.scan[angle+1] = packet[2]
            if packet[3][0]<32000:
                self.scan[angle+2] = packet[3]
            if packet[4][0]<32000:
                self.scan[angle+3] = packet[4]
            count = count+1
        return self.scan

    def scan(self):
        """
        last captured scan.
        """
        return self.scan

    def cloud(self):
        """
        last calculated point-cloud.
        """
        return self.cloud

    def getCloud(self):
        """
        calculate point cloud from last captured scan data.
        """
        self.cloud = self.toCloud(self.scan)
        return self.cloud
    
    def toCloud(scan):
        """
        Calculate point cloud from a scan hash.
        x is forward of Robert.
        y is leftward.
        theta is counterclockwise.
        """
        cloud = {}
        for index in scan.keys():
            angle = index # degrees
            distance = float(scan[index][0])
            strength = scan[index][1]
            y = distance * math.cos(math.radians(angle))
            x = distance * math.sin(math.radians(angle))
            cloud[index] = (x, y, strength)
        return cloud

def toCloud(scan):
    """
    Calculate point (x, y, theta) cloud from a scan hash.
    x is forward of Robert.
    y is leftward.
    theta is counterclockwise.
    """
    cloud = {}
    for index in scan.keys():
        angle = index # degrees
        distance = float(scan[index][0])
        strength = scan[index][1]
        x = int(distance * math.cos(math.radians(angle)))
        y = int(distance * math.sin(math.radians(angle)))
        cloud[index] = (x, y, strength)
    return cloud

def prune(readings):    # remove erroneous readings from scan data
    keys = readings.keys()
    for key in keys:
        if readings[key][0]>16000 or readings[key][0]<10 or (int(key)>8 and int(key)<42):   # ALSO prunes shadow of robot body (tower)!
            del readings[key]
    return readings

def rotated(readings, angle):
    result = {}
    keys = readings.keys()
    for key in keys:
        result[(key+angle)%360] = readings[key]
    return result    

def shiftCloud(cloud, delta):
    result={}
    for key in cloud.keys():
        result[key]=cloud[key]
        result[key]=(result[key][0]+delta,)+result[key][1:]  # neet way to change a value in a tuple!
    return result
    
if __name__=="__main__":
    portname = sys.argv[1]
    print 'NEATO HAckery v1.0'
    print '=================='
    print
    print 'Port',portname
    print

    neato = Neato(portname, 115200)
    if neato.isOpen():
        print 'Port opened.'
    else:
        print 'ARSE'
        sys.exit()

    print 'Dumping 2000 bytes'
    print '=================='

    neato.dump(2000)

    print
    print 'RPM :', neato.getRPM()
    print

    print 'Find 100 packets'
    print '================'
    packets = 0
    while packets<100:
#        print neato.getHeader()
        print neato.getPacket()
        packets = packets+1


    print 'Perform Scan'
    print '============'
    
    print neato.getScan()
    print neato.getScan()

    neato.close()
