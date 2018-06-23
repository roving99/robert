#!/usr/bin/python

import sys
import serial
import time

class Leo():
    '''Communicate with LEO command board.'''
    def __init__(self, portName, baud):
        '''
        Accepts USB port name and serial baud rate.
        flushes ports and then syncs with arduino.
        '''
        self.portName = portName
        self.baud = baud
        self.port = None

        try:
            self.port = serial.Serial(portName, baud, timeout=0.5)
            time.sleep(1)
            self.port.flushInput()
            self.port.flushOutput()
        except:
            self.port = None

    def sync(self):
        '''
        Flush buffers and syncs command/response sequence with arduino.
        '''
        if self.port:
            text = ''
            i = 10
            print 'sync'
            while text[:4]!=' Mic' and i>0:
                self.port.write('\n')
                text = self.port.readline()
                print '['+text+']', i
                i=i-1
            return i!=0
        else:
            return False

    def isOpen(self):
        '''
        Is port sucessfully opened?
        '''
        if self.port:
            return True
        else:
            return False

    def send(self, command):
        '''
        Send command, appending return and nl.
        BLOCKING.
        returns response.
        '''
        start = time.time()
        self.port.write(command+'\r\n')         # write IS blocking.
        writetime = time.time()
        text = self.port.readline()
        readtime = time.time()
        return text

    def close(self):
        '''
        Close port..
        '''
        try:
            self.port.close()
        except:
            pass
        self.port = None

if __name__=='__main__':
    portName = sys.argv[1]

    command = ("""fe%x"""%int(time.time()*100)).upper()

    leo = Leo(portName, 9600)

    if leo.isOpen():
        print 'Synchronizing..'
        if leo.sync():
            print 'sucess'
            print
            print leo.send('FF') # HELP
            print
            print 'sent :', command
            text = leo.send(command)
            print 'received :',text

            if command[2:].rstrip()==text.rstrip():
                print 'GOOD'
                leo.send('0120'+'\n')
        else:
            print 'FAILED to synchonize'
    else:
        print 'FAILED to open',portName
    leo.close()
    print "Exiting"

