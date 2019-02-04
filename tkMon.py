import os
import paho.mqtt.client as mqtt
import time
import json
import sys
from Tkinter import *

TOPICNAMES = {  'drive/output/battery':None,
                'drive/output/count':None,
                'odometry/output/pose':None,
                'sense/output/lidar':None,
                'navigation/output/target':None,
                'navigation/output/bearing':None,
                'navigation/output/stearing':None,
                }

class Application(Frame):
    def say_hi(self):
        print "hi there, everyone!"

    def createWidgets(self):
        i=0
        for key in self.TOPICNAMES.keys():
            self.TOPICNAMES[key] = [Label(self, text=key), None, StringVar()]
            self.TOPICNAMES[key][2].set('no updates yet')
            self.TOPICNAMES[key][1] = Label(self, textvariable=self.TOPICNAMES[key][2])
            self.TOPICNAMES[key][0].grid(column=0, row=i)
            self.TOPICNAMES[key][1].grid(column=1, row=i)
       #     self.TOPICNAMES[key][0].pack()
       #     self.TOPICNAMES[key][1].pack()
            i=i+1
 			

    def __init__(self, TOPICNAMES, master=None):
    	self.TOPICNAMES = TOPICNAMES
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

        
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

root = Tk()
app = Application(TOPICNAMES, master=root)
app.mainloop()
root.destroy()