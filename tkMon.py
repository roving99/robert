import os
import paho.mqtt.client as mqtt
import time
import json
import sys
import math
from Tkinter import *

TOPICNAMES = {  'drive/output/battery':None,
                'drive/output/count':None,
                'odometry/output/pose':None,
                'sense/output/lidar':None,
                'navigation/output/target':None,
                'navigation/output/bearing':None,
                'navigation/output/stearing':None,
                }

        
def mqttOnMessage(client, userdata, msg):
    topic = str(msg.topic)
    payload = str(msg.payload)
    #print 'received', topic, payload
    payload = json.loads(payload)
    for t in TOPICNAMES.keys():
        if t==topic:
            print 'updated '+topic
            app.TOPICNAMES[t][2].set(str(payload['data']))

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
        self.background.create_text(100,8,fill="#444",font="Helvetica", text="BigNumber", width=200)
        self.background.create_text(100,50,fill="#aaa",font=("Helvetica",24), text=self.text, width=200)
        self.dataText = self.background.create_text(100,100,fill="#fff",font=("Helvetica",32), text=str(self.data)[:6], width=200)
        self.background.create_text(100,150,fill="#fff",font=("Helvetica",32), text=units, width=200)

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
        self.background = Canvas(self, width=200, height=200)
        self.title = "Pose"
        self.label = Label
        self.background.pack()
        self.background.create_rectangle(0,0,200,200, fill='#111')
        self.background.create_text(100,8,fill="#444",font="Helvetica", text="Pose", width=200)
        self.dataTextX = self.background.create_text(100,50,fill="#fff",font=("Helvetica",32), text=str(self.data[0])[:6], width=200)
        self.dataTextY = self.background.create_text(100,100,fill="#fff",font=("Helvetica",32), text=str(self.data[1])[:6], width=200)
        degree_sign= u'\N{DEGREE SIGN}'
        self.dataTextT = self.background.create_text(100,150,fill="#fff",font=("Helvetica",32), text=str(self.data[2])[:5]+degree_sign, width=200)
        
        self.pack()

    def setData(self, d):
        self.data = d
        self.background.itemconfig(self.dataTextX,text=str(self.data[0])[:6])
        self.background.itemconfig(self.dataTextY,text=str(self.data[1])[:6])
        self.background.itemconfig(self.dataTextT,text=str(self.data[2])[:6])



client = mqtt.Client()
client.on_connect = mqttOnConnect
client.on_message = mqttOnMessage
ip = 'localhost'
if len(sys.argv)>1:
    ip = sys.argv[1]
print "mqtt at "+ip
client.connect(ip, 1883, 60)
#    client.connect(world['ip'], 1883, 60)
client.loop_start()

rows = 3
columns = 5

socket = {}
root = Tk()
#mainFrame = Frame(root, width=columns*100, height=rows*100, bg = '#444')
mainFrame = Frame(root, bg = '#644')
mainFrame.pack()
for i in range(0,rows):
    socket[i]={}
    for j in range(0,columns):
        socket[i][j] = Frame(mainFrame, bg='#446', width=200, height=200)
        socket[i][j].grid(row=i, column=j)

bigNumber1 = BigNumber(socket[0][0], "battery", 128, 'volts')

bigNumber2 = BigNumber(socket[1][0], "e", math.e, '')

bigNumber3 = BigNumber(socket[1][1], "three", 3, 'candles')
bigNumber3.setData(4)

pose1 = Pose(socket[0][1], "Pose", [10,100,45])
pose1.setData([20,120,37.5])
#socket[0][1] = BigNumber(mainFrame, "direct", math.pi)

print socket

root.mainloop()
root.destroy()