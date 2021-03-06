#!/usr/bin/python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtCore import QTimer,QDateTime, QFile, QTextStream, Qt
from PyQt5.QtGui import QFont

import sys
import json
import random
import argparse
import datetime
import os
import time
import colorsys
import traceback
import threading
from math import sin, cos, sqrt, atan2, radians

from pathlib import Path
import XPlaneUdp


#LISTEN_PORT = 49006
SEND_PORT = 49000
XPLANE_IP = "192.168.0.18"


# Egna  funktioner
current_milli_time = lambda: int(round(time.time() * 1000))


parser = argparse.ArgumentParser()

parser.add_argument("--ip", help="Ip address of X-plane")
args = parser.parse_args()

if args.ip:
    XPLANE_IP = args.ip
print ("Connecting to ", XPLANE_IP)


def getDistanceGPS(lat1,lon1, lat2, lon2):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    #print("Result:", distance)
    return distance
def get_dist(banan):
    return banan.get("distance")
    
def signal_handler(sig, frame):
        print("You pressed Ctrl+C!")
        running = False
        sys.exit(0)
        os._exit(0)

def updateSlider(self, lamp, dataref, type=1):
    value = self.xp.getDataref(dataref,10)
    
    if (type == 1):
        value = value*100 + 100
    if (type == 2):
        value = value*100
    #print("udpate slider", value)
    lamp.setValue(int(value))

def updateText(self, lamp, dataref):
    value = self.xp.getDataref(dataref,1)
    lamp.setText(str(int(value))+"%")

def updateLamp(self, lamp, dataref, color):
    if (self.xp.getDataref(dataref,10) >0):
        lamp.setStyleSheet("background-color: "+color)
    else:
        lamp.setStyleSheet("background-color: white")
    
def connectButton(self, button, dataref):
    button.pressed.connect(lambda: self.buttonPressed(dataref))
    button.released.connect(lambda: self.buttonReleased(dataref))
    
def connectButtonCommand(self, button, dataref):
    button.pressed.connect(lambda: self.buttonPressedCommand(dataref))
    
    
def connectOnButton(self, button, dataref):
    button.pressed.connect(lambda: self.buttonPressed(dataref))
def connectOffButton(self, button, dataref):
    button.pressed.connect(lambda: self.buttonReleased(dataref))

def connectValueButton(self, button, dataref, value):
    button.pressed.connect(lambda: self.buttonPressedValue(dataref, value))

class ColorButton():
    def __init__(self, parent, button, dataref, color, type, lampDR=""):
        self.parent = parent
        self.button = button
        self.dataref = dataref
        self.color = color
        self.type = type
        if (lampDR==""):
            self.lampdataref = self.dataref
        else:
            self.lampdataref = lampDR
        
        if (type == 0):
            button.pressed.connect(self.onClickedToggle)
        if (type == 1):
            button.pressed.connect(self.buttonPressed)
            button.released.connect(self.buttonReleased)
        
    def onClickedToggle(self):
        prevvalue = self.parent.xp.getDataref(self.dataref, 1)
        if (prevvalue == 1):
            self.parent.xp.sendDataref(self.dataref, 0)
        else:
            self.parent.xp.sendDataref(self.dataref, 1)
            
    def buttonPressed(self):
        print("buttonPressed2:", self.dataref)
        self.parent.xp.sendDataref(self.dataref, 1)
        
    def buttonReleased(self):
        print("buttonReleased2:", self.dataref)
        self.parent.xp.sendDataref(self.dataref, 0)  
        
    def updateColor(self):
        if (self.parent.xp.getDataref(self.lampdataref,10) >0):
            self.button.setStyleSheet("background-color: "+self.color)
        else:
            self.button.setStyleSheet("background-color: white")
        

class RunGUI(QMainWindow):
    def __init__(self,):
        super(RunGUI,self).__init__()

        
        self.buttonList = []
        self.xp = XPlaneUdp.XPlaneUdp(XPLANE_IP,SEND_PORT)
        
        self.xp.getDataref("sim/flightmodel/position/indicated_airspeed",1)
        self.lat = self.xp.getDataref("sim/flightmodel/position/latitude",1)
        self.lon = self.xp.getDataref("sim/flightmodel/position/longitude",1)
        self.readApt()
        
        self.initUI()
        
    def initUI(self):
        #self.root = Tk() # for 2d drawing
        
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.ui = uic.loadUi(os.path.join(current_dir, "../ui/kontrollpanel.ui"), self)
        # print(self.ui)
        #self.setGeometry(200, 200, 300, 300)
        #self.resize(640, 480)
        self.setWindowTitle("JAS Kontrollpanel")
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        ## J
        # connectButton(self, self.ui.button_j_mod,"JAS/io/st/di/J")
        connectButton(self, self.ui.button_fire,"JAS/io/spak/di/fire")
        
        # ST knappar
        connectButton(self, self.ui.button_j_st_hvp,"JAS/io/st/di/HVP")
        connectButton(self, self.ui.button_j_st_ir,"JAS/io/st/di/IRB")
        connectButton(self, self.ui.button_j_st_akan,"JAS/io/st/di/AK")
        
        # Spak knappar
        
        connectButton(self, self.ui.button_j_spak_hvp,"JAS/io/spak/di/hat1_up")
        connectButton(self, self.ui.button_j_sijir,"JAS/io/spak/di/hat1_left")
        connectButton(self, self.ui.button_j_sijak,"JAS/io/spak/di/hat1_right")
        connectButton(self, self.ui.button_j_spak_ak,"JAS/io/spak/di/hat1_down")
        
        
        connectValueButton(self, self.ui.button_j_target1,"sim/cockpit/weapons/plane_target_index", 1)
        
        connectButtonCommand(self, self.ui.button_j_reload,"sim/weapons/re_arm_aircraft")
        
        self.ui.button_j_ping.clicked.connect(self.PingAll)
        
        
        
        
        ## Landning
        # connectButton(self, self.ui.button_land_mod,"JAS/io/st/di/L")
        self.ui.land_set_all.clicked.connect(self.Land_set_all)
        
        connectValueButton(self, self.ui.land_hb,"JAS/ti/land/bibana", 0)
        connectValueButton(self, self.ui.land_bi,"JAS/ti/land/bibana", 1)
        connectValueButton(self, self.ui.land_rikt_n,"JAS/ti/land/rikt", 0)
        connectValueButton(self, self.ui.land_rikt_inv,"JAS/ti/land/rikt", 1)
        
        connectValueButton(self, self.ui.luft_in,"sim/cockpit2/controls/speedbrake_ratio", 0)
        connectValueButton(self, self.ui.luft_ut,"sim/cockpit2/controls/speedbrake_ratio", 1)

        # connectOnButton(self, self.ui.button_apu_on,"JAS/button/apu")
        #connectOffButton(self, self.ui.button_apu_off,"JAS/button/apu")
        
        
        # self.buttonList.append( ColorButton(self,self.ui.button_afk, "JAS/io/frontpanel/di/afk", "orange", 1, lampDR="JAS/io/frontpanel/lo/afk") )
        # self.buttonList.append( ColorButton(self,self.ui.button_hojd, "JAS/io/frontpanel/di/hojd", "orange", 1, lampDR="JAS/io/frontpanel/lo/hojd") )
        # self.buttonList.append( ColorButton(self,self.ui.button_att, "JAS/io/frontpanel/di/att", "orange", 1, lampDR="JAS/io/frontpanel/lo/att") )
        # self.buttonList.append( ColorButton(self,self.ui.button_spak, "JAS/io/frontpanel/di/spak", "orange", 1, lampDR="JAS/io/frontpanel/lo/spak") )
        # 
        # self.buttonList.append( ColorButton(self,self.ui.button_apu_on, "JAS/io/vu22/di/apu", "green", 0) )
        # self.buttonList.append( ColorButton(self,self.ui.button_ess_on, "JAS/io/vu22/di/ess", "green", 0) )
        # self.buttonList.append( ColorButton(self,self.ui.button_hstrom_on, "JAS/io/vu22/di/hstrom", "green", 0) )
        # self.buttonList.append( ColorButton(self,self.ui.button_lt_kran_on, "JAS/io/vu22/di/ltbra", "green", 0) )
        # #self.buttonList.append( ColorButton(self,self.ui.dap_button_pluv, "JAS/system/dap/lamp/pluv", "green", 0) )
        
        
        
        
        self.ui.button_banljus_on.clicked.connect(self.banljusOn)
        self.ui.button_banljus_off.clicked.connect(self.banljusOff)
        self.ui.button_tanka_20.clicked.connect(self.buttonTanka20)
        self.ui.button_tanka_50.clicked.connect(self.buttonTanka50)
        self.ui.button_tanka_100.clicked.connect(self.buttonTanka100)
        
        connectButtonCommand(self, self.ui.button_reload_acf,"sim/operation/reload_aircraft_no_art")
        
        
        self.ui.button_land_update.clicked.connect(self.updateAirportBox)
        
        # 
        # self.ui.auto_afk_text.valueChanged.connect(self.autoAFK)
        # self.ui.auto_hojd_text.valueChanged.connect(self.autoHOJD)
        self.ui.comboBox_airports.currentTextChanged.connect(self.airportBoxOnChange)
        
        #Snabbval
        ## ESKN
        
        self.ui.snabb_eskn_1.clicked.connect(self.ESKN1)
        self.ui.snabb_eskn_2.clicked.connect(self.ESKN2)
        self.ui.snabb_eskn_3.clicked.connect(self.ESKN3)
        self.ui.snabb_eskn_4.clicked.connect(self.ESKN4)
        
        font = QFont("Sans")
        font.setPixelSize(18)
        self.setFont(font)
        
        self.ui.tabWidget.setStyleSheet("""QTabWidget::pane { 
                                     margin: -0px -5px -0px -5px;
                                     
                                    }""")

        self.timer = QTimer()
        self.timer.timeout.connect(self.loop)
        self.timer.start(100)
        
        # self.timer2 = QTimer()
        # self.timer2.timeout.connect(self.updateAirportBox)
        # self.timer2.start(1000)

    def airportBoxOnChange(self):
        print("chagne box", self.ui.comboBox_airports.currentText())
        self.ui.comboBox_airports.setCurrentText(self.ui.comboBox_airports.currentText().upper())
        
        for apt in self.airportList:
            if (self.ui.comboBox_airports.currentText() == apt["id"] ):
                self.xp.sendDataref("JAS/ti/land/index", apt["index"])
                print("found airport", apt["id"], apt["index"])

    def updateAirportBox(self):
        
        self.lat = self.xp.getDataref("sim/flightmodel/position/latitude",1)
        
        self.lon = self.xp.getDataref("sim/flightmodel/position/longitude",1)
        print("updateAirportBox", self.lat, self.lon)
        if (self.lat < 0.1 and self.lat > -0.1):
            print("ingen egen plats", self.lat, self.lon)
            return
        if (self.lon < 0.1 and self.lon > -0.1):
            print("ingen egen plats", self.lat, self.lon)
            return
        self.airportListClose = []
        for apt in self.airportList:
            apt["distance"] = getDistanceGPS(self.lat,self.lon, apt["lat"], apt["lon"])
            self.airportListClose.append(apt)
            
        self.airportListClose.sort(key=get_dist)
        print("n??rmaste ", self.airportListClose[0])
        self.namelist = []
        for apt in self.airportListClose:
            banan = str(apt["id"])
            self.namelist.append(banan)
        self.ui.comboBox_airports.clear()
        self.ui.comboBox_airports.addItems(self.namelist)

    def readApt(self):
        
        self.airportList = []
        with open("../apt.csv", "r") as apt_file:
            data = apt_file.read().split("\n")
            print("Airports found: ",len(data))
            apt_file.close()
            i = 0
            for d in data:
                apt = {}
                col = d.split(";")
                if (len(col)>3):
                    apt["id"] = col[0]
                    apt["alt"] = float(col[1])
                    apt["lat"] = float(col[2])
                    apt["lon"] = float(col[3])
                    apt["index"] = i
                    i = i +1
                    self.airportList.append(apt)
        self.airportDict = {}
        for apt in self.airportList:
            self.airportDict[apt["id"]] = {}
            self.airportDict[apt["id"]]["id"] = apt["id"]
            self.airportDict[apt["id"]]["alt"] = apt["alt"]
            self.airportDict[apt["id"]]["lat"] = apt["lat"]
            self.airportDict[apt["id"]]["lon"] = apt["lon"]
            self.airportDict[apt["id"]]["index"] = apt["index"]
                
                
    def updateGUI(self):
    
        pass
    
    def PingAll(self):
        self.xp.sendDataref("JAS/radar/ping[1]", 2000)
        self.xp.sendDataref("JAS/radar/ping[2]", 2000)
        self.xp.sendDataref("JAS/radar/ping[3]", 2000)
        self.xp.sendDataref("JAS/radar/ping[4]", 2000)
        self.xp.sendDataref("JAS/radar/ping[5]", 2000)
        self.xp.sendDataref("JAS/radar/ping[6]", 2000)
        self.xp.sendDataref("JAS/radar/ping[7]", 2000)
        self.xp.sendDataref("JAS/radar/ping[8]", 2000)
        self.xp.sendDataref("JAS/radar/ping[9]", 2000)
        self.xp.sendDataref("JAS/radar/ping[10]", 2000)
        self.xp.sendDataref("JAS/radar/ping[11]", 2000)
        self.xp.sendDataref("JAS/radar/ping[12]", 2000)
        self.xp.sendDataref("JAS/radar/ping[13]", 2000)
        self.xp.sendDataref("JAS/radar/ping[14]", 2000)
        self.xp.sendDataref("JAS/radar/ping[15]", 2000)
        self.xp.sendDataref("JAS/radar/ping[16]", 2000)
        self.xp.sendDataref("JAS/radar/ping[17]", 2000)
        self.xp.sendDataref("JAS/radar/ping[18]", 2000)
        self.xp.sendDataref("JAS/radar/ping[19]", 2000)

    def Land_set_all(self):
        self.xp.sendDataref("JAS/ti/menu/menu", 3)
        
        return
    def ESKN1(self):
        self.xp.sendDataref("JAS/ti/land/index", self.airportDict["ESKN"]["index"])
        self.xp.sendDataref("JAS/ti/land/bana", 0)
        self.xp.sendDataref("JAS/ti/land/bibana", 0)
        self.xp.sendDataref("JAS/ti/land/rikt", 1)
        return
    def ESKN2(self):
        self.xp.sendDataref("JAS/ti/land/index", self.airportDict["ESKN"]["index"])
        self.xp.sendDataref("JAS/ti/land/bana", 0)
        self.xp.sendDataref("JAS/ti/land/bibana", 0)
        self.xp.sendDataref("JAS/ti/land/rikt", 0)
        return
    def ESKN3(self):
        self.xp.sendDataref("JAS/ti/land/index", self.airportDict["ESKN"]["index"])
        self.xp.sendDataref("JAS/ti/land/bana", 1)
        self.xp.sendDataref("JAS/ti/land/bibana", 1)
        self.xp.sendDataref("JAS/ti/land/rikt", 1)
        return
    def ESKN4(self):
        self.xp.sendDataref("JAS/ti/land/index", self.airportDict["ESKN"]["index"])
        self.xp.sendDataref("JAS/ti/land/bana", 1)
        self.xp.sendDataref("JAS/ti/land/bibana", 1)
        self.xp.sendDataref("JAS/ti/land/rikt", 0)
        return
    def banljusOn(self):
        self.xp.sendDataref("sim/operation/override/override_airport_lites", 1)
        self.xp.sendDataref("sim/graphics/scenery/airport_lights_on", 1)
    def banljusOff(self):
        self.xp.sendDataref("sim/operation/override/override_airport_lites", 0)
        self.xp.sendDataref("sim/graphics/scenery/airport_lights_on", 0)
        
    def Button_a_st_hvp(self):
        self.xp.sendDataref("JAS/huvudmod", 2)
        self.xp.sendDataref("JAS/huvudmod", 2)
    
    def buttonPressedCommand(self, dataref):
        print("buttonPressedCommand:", dataref)
        self.xp.sendCommand(dataref)
                    
    def buttonPressed(self, dataref):
        print("buttonPressed:", dataref)
        self.xp.sendDataref(dataref, 1)
        
    def buttonReleased(self, dataref):
        print("buttonReleased:", dataref)
        self.xp.sendDataref(dataref, 0)   
        
    def buttonPressedValue(self, dataref, value):
        print("buttonPressed:", dataref)
        self.xp.sendDataref(dataref, value)
                 
    def buttonTanka100(self):
        self.xp.sendDataref("sim/flightmodel/weight/m_fuel1", 2400)
    def buttonTanka50(self):
        self.xp.sendDataref("sim/flightmodel/weight/m_fuel1", 1200)
    def buttonTanka20(self):
        self.xp.sendDataref("sim/flightmodel/weight/m_fuel1", 480)
        
    def autoAFK(self):
        newvalue = float(self.ui.auto_afk_text.value()) / 1.85200
        self.xp.sendDataref("JAS/autopilot/afk", newvalue)
        
    def autoHOJD(self):
        newvalue = float(self.ui.auto_hojd_text.value()) / 0.3048
        self.xp.sendDataref("JAS/autopilot/alt", newvalue)
                
    def loop(self):
        self.xp.readData()
        self.updateGUI()
        
        #print(self.xp.dataList)
        self.timer.start(10)
        pass
        

if __name__ == "__main__":

    try:
        app = QApplication(sys.argv)
        win = RunGUI()
        win.show()
        sys.exit(app.exec_())
    except Exception as err:
        exception_type = type(err).__name__
        print(exception_type)
        print(traceback.format_exc())
        os._exit(1)
    print ("program end")
    os._exit(0)
