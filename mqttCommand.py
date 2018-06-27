import config
from cmd import Cmd
import os
import paho.mqtt.client as mqtt
import time
import json

'''
Command-line interface to MQTT client controlling robot.

drive/input/steer  {"data": [<translate>, <rotate>], } cms-1, degrees-1
drive/input/motors {"data": [<motor left speed>, <motor right speed>], }   cms-1, cms-1
drive/input/leds   {"data": [led0, led1, led2, ..], }  n
drive/input/lidar  {"data": [0|1], }   n
drive/input/raw    {"data": [<string>], }  raw command to controlling arduino
        
sense/output/sonar {"data": { <angle>: <distance>, <angle>:<distance>, ...}, } degree, cm
sense/output/touch {"data": [ <touch0>, <touch1>, ...], }  0/1
sense/output/cliff {"data": [ <cliff0>, <cliff1>, ...], }  0/1
sense/output/compass   {"data": <bearing>, }   degree
        
drive/output/count {"data": [<motor left count>, <motor right count>], }   
drive/output/battery   {"data": [<volts>], }   volts
odometry/output/pose   {"data": [ <x>, <y>, <theta>], }    cm, cm, degree
odometry/output/rate   {"data": [ <dx>, <dy>, <dtheta>], } cms-1, cms-1, degrees-1
'''
TOPICNAMES = { 'drive/output/battery':None,
                'drive/output/count':None,
                'odometry/output/pose':None,
                'sense/output/lidar':None,
                }

class MyPrompt(Cmd):

    def do_hello(self, args):
        """Says hello. If you provide a name, it will greet you with it."""
        if len(args) == 0:
            name = 'stranger'
        else:
            name = args
        print "Hello, %s" % name

    def do_quit(self, args):
        """Quits the program."""
        print "Quitting."
        raise SystemExit

    def do_status(self, args):
        """Status of monitored topics"""
        global TOPICNAMES
        for k in TOPICNAMES.keys():
            print k,': ',TOPICNAMES[k]

    def do_lidaron(self, args):
        """switch lidar motor ON"""
        data = {"time":time.time(), "type":"", "data":[1]} 
        client.publish(topic='drive/input/lidar', payload=json.dumps(data))
        
    def do_lidaroff(self, args):
        """switch lidar motor OFF"""
        data = {"time":time.time(), "type":"", "data":[0]} 
        client.publish(topic='drive/input/lidar', payload=json.dumps(data))

    def do_forward(self, args):
        """go forward at 10cms-1"""
        data = {"time":time.time(), "type":"", "data":[10, 10]} 
        client.publish(topic='drive/input/motors', payload=json.dumps(data))
    
    def do_backward(self, args):
        """go forward at 10cms-1"""
        data = {"time":time.time(), "type":"", "data":[-10, -10]} 
        client.publish(topic='drive/input/motors', payload=json.dumps(data))
        
    def do_stop(self, args):
        """really?"""
        data = {"time":time.time(), "type":"", "data":[0, 0]} 
        client.publish(topic='drive/input/motors', payload=json.dumps(data))
    
    def do_left(self, args):
        """turn left at 10cms-1"""
        data = {"time":time.time(), "type":"", "data":[10, -10]} 
        client.publish(topic='drive/input/motors', payload=json.dumps(data))
    
    def do_right(self, args):
        """turn right at 10cms-1"""
        data = {"time":time.time(), "type":"", "data":[-10, 10]} 
        client.publish(topic='drive/input/motors', payload=json.dumps(data))

    def do_reset(self, args):
        """Stop robot, reset odometry"""
        data = {"time":time.time(), "type":"pose", "data":[0.0, 0.0, 0,0]} 
        client.publish(topic='odometry/input/pose', payload=json.dumps(data))

        
def mqttOnMessage(client, userdata, msg):
    topic = str(msg.topic)
    payload = str(msg.payload)
    #print 'received', topic, payload
    payload = json.loads(payload)
    for t in TOPICNAMES.keys():
        if t==topic:
            TOPICNAMES[t]= payload

def mqttOnConnect(client, userdata, flags, rc):  # added 'flags' on work version of library?
    print("Connected with result code "+str(rc))
    # re subscribe here?
    for t in TOPICNAMES.keys():
        client.subscribe(t)

if __name__ == '__main__':
#    world = { 'ip': config.MQTTIP,
#            }
    world = { 'ip': 'robert.local',
            }
    
    client = mqtt.Client()
    client.on_connect = mqttOnConnect
    client.on_message = mqttOnMessage
    client.connect("robert.local", 1883, 60)
#    client.connect(world['ip'], 1883, 60)
    client.loop_start()

    print 'MQTT command'
    print '============'
    for v in world.keys():
        print v, ': ',world[v]
    print
    print'By your command!'

    prompt = MyPrompt()
    prompt.prompt = '> '
    prompt.cmdloop('Starting prompt...')

    print 'stopping mqtt client..'
    client.loop_stop()
