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

        
def mqttOnMessage(client, userdata, msg):
    topic = str(msg.topic)
    print 'topic: '+topic
    payload = str(msg.payload)
    payload = json.loads(payload)
    if topic in TOPICNAMES and TOPICNAMES[topic]:
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
                self.canvas.create_line(100,100, 100-y, 100-x, tags='data', fill='#888')
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

cloudData= {0: (1167, 256), 1: (1162, 272), 2: (1156, 265), 3: (1152, 268), 4: (1147, 275), 5: (1144, 265), 6: (1141, 261), 7: (1138, 274), 8: (1135, 268), 9: (1132, 267), 10: (1130, 271), 11: (1129, 281), 12: (1128, 274), 13: (1127, 279), 14: (1127, 275), 15: (1128, 275), 16: (1128, 287), 17: (1128, 275), 18: (1129, 277), 19: (1129, 280), 20: (1132, 279), 21: (1135, 267), 22: (1137, 274), 23: (1140, 264), 24: (1142, 271), 25: (1147, 256), 26: (1152, 261), 27: (1156, 257), 28: (1161, 260), 29: (1167, 257), 30: (1171, 261), 31: (1179, 255), 32: (1184, 253), 33: (1191, 257), 34: (1199, 251), 35: (1207, 250), 36: (1214, 243), 37: (1225, 244), 38: (1233, 237), 39: (1244, 236), 40: (1256, 233), 41: (1267, 225), 42: (1278, 222), 43: (1291, 199), 44: (1304, 191), 45: (1318, 198), 46: (1335, 180), 47: (1351, 193), 48: (1368, 193), 49: (1385, 180), 50: (1403, 158), 51: (1422, 143), 52: (1440, 164), 53: (1459, 152), 54: (1484, 153), 55: (1506, 143), 56: (1529, 128), 57: (1556, 145), 58: (1585, 121), 59: (1613, 123), 60: (1641, 111), 61: (1674, 114), 62: (1707, 123), 63: (1727, 117), 64: (1695, 124), 65: (1669, 123), 66: (1646, 133), 67: (1623, 130), 68: (1599, 131), 69: (1582, 156), 70: (1557, 143), 71: (1540, 166), 72: (1522, 175), 73: (1504, 146), 74: (1488, 164), 75: (1471, 156), 76: (1454, 166), 77: (1438, 169), 78: (1461, 63), 79: (1520, 57), 80: (1589, 61), 81: (1659, 49), 82: (1735, 47), 83: (1817, 30), 84: (1915, 16), 85: (1825, 55), 86: (2144, 12), 87: (2263, 8), 90: (2083, 9), 91: (2059, 15), 93: (2246, 13), 95: (4509, 9), 96: (4432, 12), 97: (4470, 12), 105: (4197, 14), 106: (4045, 9), 116: (4707, 8), 133: (4249, 17), 134: (4287, 15), 135: (4388, 11), 136: (4459, 13), 139: (1823, 96), 140: (1813, 111), 141: (1822, 85), 142: (2387, 37), 143: (2316, 36), 144: (2265, 33), 145: (2217, 45), 146: (2173, 62), 147: (2120, 52), 148: (2082, 54), 149: (2045, 61), 150: (2008, 59), 151: (1966, 64), 152: (1935, 85), 153: (1981, 72), 154: (2017, 71), 155: (2076, 67), 156: (2088, 37), 157: (2147, 12), 158: (2196, 13), 159: (2260, 9), 160: (2308, 7), 161: (2403, 12), 162: (2467, 17), 163: (2591, 10), 165: (2786, 27), 166: (2821, 8), 190: (3346, 16), 191: (3344, 19), 218: (4825, 13), 219: (4624, 6), 220: (4351, 17), 221: (4151, 8), 222: (4108, 11), 223: (3965, 12), 224: (3809, 13), 225: (3675, 12), 226: (3602, 19), 227: (3480, 22), 228: (3346, 18), 229: (3250, 24), 230: (3189, 28), 231: (3107, 27), 232: (2990, 33), 233: (2940, 39), 234: (2881, 32), 235: (2818, 43), 236: (2761, 33), 237: (2698, 46), 238: (2633, 47), 239: (2581, 54), 240: (2532, 46), 241: (2502, 55), 242: (2453, 53), 243: (2451, 56), 244: (2514, 63), 245: (2580, 47), 246: (2651, 41), 247: (2707, 35), 248: (2776, 38), 249: (2842, 55), 250: (2830, 53), 251: (2789, 51), 252: (2767, 55), 253: (2741, 67), 254: (2697, 70), 255: (2676, 50), 256: (2645, 76), 257: (2621, 57), 258: (2589, 63), 259: (2584, 77), 260: (2553, 79), 261: (2531, 80), 262: (2503, 65), 263: (2491, 93), 264: (2470, 43), 265: (2456, 88), 266: (2445, 84), 267: (2348, 97), 268: (2344, 92), 269: (2306, 105), 270: (2309, 83), 271: (2312, 92), 272: (2302, 83), 273: (2304, 83), 274: (2270, 97), 275: (2275, 94), 276: (2261, 97), 277: (2241, 113), 278: (2245, 122), 279: (2250, 111), 280: (2245, 99), 281: (2225, 137), 282: (2241, 134), 283: (2242, 107), 284: (2236, 107), 285: (2241, 112), 286: (2244, 97), 287: (2238, 102), 288: (2246, 108), 289: (2251, 120), 290: (2262, 105), 291: (2259, 103), 292: (2261, 106), 293: (2265, 100), 294: (2276, 93), 295: (2286, 93), 296: (2299, 99), 297: (2303, 104), 298: (2320, 92), 299: (2328, 78), 300: (2340, 91), 301: (2353, 92), 302: (2373, 83), 303: (2381, 81), 304: (2397, 75), 305: (2411, 81), 306: (2438, 72), 307: (2454, 76), 308: (2481, 77), 309: (2495, 75), 310: (2521, 77), 311: (2530, 74), 312: (2580, 60), 313: (2602, 67), 314: (2610, 56), 315: (4380, 17), 316: (4187, 20), 317: (4301, 16), 318: (4245, 16), 319: (4242, 15), 320: (4214, 21), 321: (4102, 23), 322: (3983, 12), 323: (4086, 27), 324: (4157, 16), 325: (4161, 17), 326: (1726, 58), 327: (1688, 119), 328: (1654, 113), 329: (1624, 126), 330: (1597, 136), 331: (1568, 127), 332: (1543, 140), 333: (1521, 146), 334: (1498, 149), 335: (1472, 157), 336: (1451, 158), 337: (1433, 163), 338: (1412, 167), 339: (1397, 168), 340: (1377, 204), 341: (1362, 174), 343: (711, 66), 344: (693, 179), 345: (683, 212), 346: (674, 201), 347: (670, 278), 348: (666, 334), 349: (667, 337), 350: (669, 289), 351: (676, 220), 352: (687, 154), 353: (698, 79), 354: (719, 64), 355: (738, 19), 356: (1191, 249), 357: (1186, 238), 358: (1180, 263), 359: (1172, 257)}

client = mqtt.Client()
client.on_connect = mqttOnConnect
client.on_message = mqttOnMessage

ip = config.MQTTIP

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

root.mainloop()
root.destroy()
