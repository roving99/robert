#!/usr/bin/python
import os
import paho.mqtt.client as mqtt
import time
import json
import sys
import math
from Tkinter import *
        
import config

def doLidar(payload):
    global lastLidarUpdate
    lastLidarUpdate=lastLidarUpdate+1
    if lastLidarUpdate>1: # limit rate of updates to 2Hz.
        uCloud = payload['data'] # unicode keys
        cloud = {}
        for key in uCloud.keys(): # json converts int keys to unicode. change back to ints..
            cloud[int(key)]=uCloud[key]
        #print str(cloud)[:50]
        cloud1.setData(cloud)
        lastLidarUpdate=0

def doForce(payload):
    uCloud = payload['data'] # unicode keys
    cloud = {}
    for key in uCloud.keys(): # json converts int keys to unicode. change back to ints..
        cloud[int(key)]=uCloud[key]
    cloud2.setData(cloud)

def doTarget(payload):
    poseTarget.setData(payload['data'])

def doPose(payload):
    posePose.setData(payload['data'])

def doBearing(payload):
    d = payload['data'][0]
    t = payload['data'][1]
    poseTargetBearing.setData([0, d, t])

def doBattery(payload):
    bigNumberBattery.setData(payload['data'][0])

TOPICNAMES = {  'drive/output/battery':doBattery,
                'drive/output/count':None,
                'odometry/output/pose':doPose,
                'sense/output/lidar':doLidar,
                'ransac/output/force':doForce,
                'navigation/output/target':doTarget,
                'navigation/output/bearing':doBearing,
                'navigation/output/stearing':None,
                }

GLOBALSDEFINED = False
        
def mqttOnMessage(client, userdata, msg):
    topic = str(msg.topic)
    print 'topic: '+topic
    payload = str(msg.payload)
    payload = json.loads(payload)
    if topic in TOPICNAMES and TOPICNAMES[topic] and GLOBALSDEFINED:
        print 'GO!'
        TOPICNAMES[topic](payload)
        
def mqttOnConnect(client, userdata, flags, rc):  # added 'flags' on work version of library?
    print("Connected with result code "+str(rc))
    # re subscribe here?
    for t in TOPICNAMES.keys():
        client.subscribe(t)

class BigNumber(Frame, object):
    def __init__(self,master, label, data, units):
        Frame.__init__(self, master)
        #self.grid_propagate(0)
        self.master = master
        self.data = data
        self.text = label
        self.background = Canvas(self, width=200, height=200)
        self.title = "BigNumber"
        self.label = Label
        self.dataLabel = "N/A"
        self.background.pack()
        self.background.create_rectangle(0,0,200,200, fill='#111')
        self.background.create_text(100,10,fill="#888",font="Helvetica", text=self.text, width=200)
        self.background.create_text(100,50,fill="#aaa",font=("Helvetica",24), text=self.text, width=200)
        self.dataText = self.background.create_text(100,100,fill="#fff",font=("Helvetica",32), text=str(self.data)[:6], width=200)
        self.background.create_text(100,150,fill="#fff",font=("Helvetica",32), text=units, width=200)

        self.pack()


    def setData(self, d):
        self.data = d
        self.background.itemconfig(self.dataText,text=str(self.data)[:6])

class Buttons(Frame, object):
    def __init__(self,master, label, data):
        Frame.__init__(self, master)
        #self.grid_propagate(0)
        self.master = master
        self.data = data
        self.text = label
        self.background = Canvas(self, width=200, height=200)
        self.title = "Press me"
        self.label = Label
        self.dataLabel = "N/A"
        
        self.background.create_rectangle(0,0,200,200, fill='#111')
        self.background.create_text(100,10,fill="#888",font="Helvetica", text=self.text, width=200)
        self.background.create_rectangle(55-40,40-20,55+40,40+20, fill='#333')
        self.background.create_rectangle(55-40,40+25,55+40,85+20, fill='#333')
        self.background.create_rectangle(55-40,40+70,55+40,130+20, fill='#333')
        self.background.create_rectangle(55-40,40+115,55+40,175+20, fill='#333')

        self.background.create_rectangle(145-40,40-20,145+40,40+20, fill='#333')
        self.background.create_rectangle(145-40,40+25,145+40,85+20, fill='#333')
        self.background.create_rectangle(145-40,40+70,145+40,130+20, fill='#333')
        self.background.create_rectangle(145-40,40+115,145+40,175+20, fill='#333')

        self.background.pack()

        self.buttons = []
        for b in self.data.keys():
            self.buttons.append(Button(self.background, text=b, command=self.data[b]))
        x=55
        y=40
        for b in self.buttons:
            self.background.create_window(x, y, window=b, height=40, width=80)
            y=y+45
            if y>190:
                y=40
                x=145
        self.background.pack()
        self.pack()

    def setData(self, d):
        self.data = d
        self.background.itemconfig(self.dataText,text=str(self.data)[:6])


class Pose(Frame, object):
    def __init__(self,master, label, data):
        Frame.__init__(self, master)
        self.master = master
        self.data = data # [x,y,theta]
        self.text = label
        self.canvas = Canvas(self, width=200, height=200, bd=0)
        self.title = "Pose"
        self.label = Label
        self.canvas.pack()
        self.draw()
        self.setData(self.data)
        self.pack()

    def draw(self):
        self.drawBackground()
        self.drawData()

    def drawData(self):
        self.canvas.create_text(100,10,fill="#888",font="Helvetica", text=self.text, width=200)
        self.dataTextX = self.canvas.create_text(100,50,fill="#fff",font=("Helvetica",32), text=str(self.data[0])[:6], width=200)
        self.dataTextY = self.canvas.create_text(100,100,fill="#fff",font=("Helvetica",32), text=str(self.data[1])[:6], width=200)
        degree_sign= u'\N{DEGREE SIGN}'
        self.dataTextT = self.canvas.create_text(100,150,fill="#fff",font=("Helvetica",32), text=str(self.data[2])[:5]+degree_sign, width=200)
        
    def drawBackground(self):
        self.backgroundID=self.canvas.create_rectangle(0,0,200,200, fill='#111')
        self.arrowID=self.canvas.create_polygon([50,50, 150,50, 100,150], outline='#333', fill='#333', width=2)
        
    def setData(self, d):
        self.data = d
        self.canvas.itemconfig(self.dataTextX,text=str(self.data[0])[:6])
        self.canvas.itemconfig(self.dataTextY,text=str(self.data[1])[:6])
        self.canvas.itemconfig(self.dataTextT,text=str(self.data[2])[:6])
        a = math.radians(self.data[2])
        b = math.radians(160)
        l = 75
        s = l
        self.canvas.coords(self.arrowID, 100-l*math.sin(a),100-l*math.cos(a), 100-s*math.sin(a+b), 100-s*math.cos(a+b), 100-s*math.sin(a-b), 100-s*math.cos(a-b))    

class Cloud(Frame, object):
    def __init__(self,master, label, data):
        Frame.__init__(self, master)
        self.master = master
        self.data = data 
        self.text = label
        self.canvas = Canvas(self, width=200, height=200, bd=0)
        self.title = "Scan"
        self.label = Label
        self.canvas.pack()
        self.draw()
        self.setData(self.data)
        self.pack()

    def draw(self):
        self.drawBackground()
        self.drawData()

    def drawData(self):
        self.canvas.delete('data')
        self.canvas.create_text(100,10,fill="#888",font="Helvetica", text=self.text, width=200, tags='data')
        if self.data:
            for angle in self.data.keys():
                x = self.data[angle][0]/20
                y = self.data[angle][1]/20
                #self.canvas.create_line(100,100, 100-y, 100-x, tags='data', fill='#888')
                self.canvas.create_rectangle(100-y, 100-x, 101-y, 101-x, fill='#800', outline='#800', tags='data')

    def drawBackground(self):
        self.backgroundID=self.canvas.create_rectangle(0,0,200,200, fill='#111')
        
    def setData(self, d):
        self.data = d
        self.drawData()

class ForceCloud(Frame, object):
    def __init__(self,master, label, data):
        Frame.__init__(self, master)
        self.master = master
        self.data = data 
        self.text = label
        self.canvas = Canvas(self, width=200, height=200, bd=0)
        self.title = "force"
        self.label = Label
        self.canvas.pack()
        self.draw()
        self.setData(self.data)
        self.pack()

    def draw(self):
        self.drawBackground()
        self.drawData()

    def drawData(self):
        self.canvas.delete('data')
        self.canvas.create_text(100,10,fill="#888",font="Helvetica", text=self.text, width=200, tags='data')
        if self.data:
            for angle in self.data.keys():
                x = self.data[angle][0]
                y = self.data[angle][1]
                f = self.data[angle][2]
                colour = '#080'
                if (f>33):
                    colour = '#880'
                if (f>66):
                    colour = '#800'
                self.canvas.create_line(100,100, 100-y, 100-x, tags='data', fill=colour)
                #self.canvas.create_rectangle(100-y, 100-x, 101-y, 101-x, fill=colour, outline='#800', tags='data')

    def drawBackground(self):
        self.backgroundID=self.canvas.create_rectangle(0,0,200,200, fill='#111')
        
    def setData(self, d):
        self.data = d
        self.drawData()

def doButton1():
    print '1'
    pass

def doButton2():
    print '2'
    pass
    
def doButton3():
    print '3'
    pass
     
def doButton4():
    print '4'
    pass   

client = mqtt.Client()
client.on_connect = mqttOnConnect
client.on_message = mqttOnMessage

ip = config.MQTTIP

print "Connecting to mqtt broker", ip

client.connect(ip, 1883, 60)
client.loop_start()

rows = 2
columns = 4     # big a display as the pi touchscreen will cope with.
lastLidarUpdate=0

socket = {}
root = Tk()

mainFrame = Frame(root, bg = '#644')
mainFrame.pack()
for i in range(0,rows):
    socket[i]={}
    for j in range(0,columns):
        socket[i][j] = Frame(mainFrame, bg='#446', width=200, height=200, bd=0)
        socket[i][j].grid(row=i, column=j)

bigNumberBattery = BigNumber(socket[0][0], "battery", 12.8, 'volts')

posePose = Pose(socket[0][1], "Pose", [10,100,45])
poseTarget = Pose(socket[0][2], "Target", [110,10,0])
poseTargetBearing = Pose(socket[0][3], "Target Bearing", [0, 56,12.2])

cloud1 = Cloud(socket[1][0], "lidar", None)
cloud2 = ForceCloud(socket[1][1], "force", None)

buttons = Buttons(socket[1][2], "buttons", { "button 1":doButton1, "no":doButton2, "perhaps":doButton3, "GO!":doButton4, "STOP!":doButton4})

GLOBALSDEFINED = True

root.mainloop()
root.destroy()
