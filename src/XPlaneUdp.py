import socket
import struct
import binascii
import time


LISTEN_PORT = 49006
SEND_PORT = 49000

current_milli_time = lambda: int(round(time.time() * 1000))

class XPlaneUdp:
    
    def __init__(self, ip, port):
        self.xip = ip
        self.xport = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(0)
        self.sock.bind(("", LISTEN_PORT))
        self.sendList = []
        self.dataList = {}
        self.lastDataTimer = current_milli_time()
        self.connected = False
        
    def readData(self):
        if (self.lastDataTimer+10000 < current_milli_time()):
            if (self.connected == False):
                print("reconnect")
                self.sendList = []
                self.dataList = {}
        try:
            data, addr = self.sock.recvfrom(1024)
            # print("received data:")
            # print(addr)
            # print(data)
            header=data[0:5]
            if(header==b"RREF,"):
                self.lastDataTimer = current_milli_time()
                self.connected = True
                values =data[5:]
                lenvalue = 8
                numvalues = int(len(values)/lenvalue)
                for i in range(0,numvalues):
                    singledata = data[(5+lenvalue*i):(5+lenvalue*(i+1))]
                    (idx,value) = struct.unpack("if", singledata)
                    #print("found values", idx, value)
                    if idx<len(self.sendList):
                        if self.sendList[idx] in self.dataList:
                            self.dataList[self.sendList[idx]] = value
                            #print("set ",self.sendList[idx], "value", value )
        except BlockingIOError:
            #print('no data')
            pass
        
        
    def sendDataref(self, dataref, value):
        message = b'DREF0'
        message = message + struct.pack("f", float(value))
        bytestring = dataref.encode()
        message = message + bytestring + b'\00'
        #print(message)
        
        for i in range(509):
            message = message+b'\x20'

        message = message[:509]

        self.sock.sendto(message, (self.xip, self.xport))
        
    def sendCommand(self, dataref):
        message = b'CMND0'
        
        bytestring = dataref.encode()
        message = message + bytestring + b'\00'
        #print(message)
        
        for i in range(509):
            message = message+b'\x20'

        message = message[:509]

        self.sock.sendto(message, (self.xip, self.xport))
        
    def getDataref(self, dataref, interval):
        if dataref not in self.dataList:
            self.createDataref(dataref, interval)
            return 0
        else:
            return self.dataList[dataref]
        
    def createDataref(self, dataref, interval):
        self.sendList.append(dataref)
        self.dataList[dataref] = 0
        index = len(self.sendList) - 1
        #print("createDataref ", index)
        message = b'RREF0'
        message = message + struct.pack("i", interval)
        message = message + struct.pack("i", index)
        bytestring = dataref.encode()
        message = message + bytestring + b'\00'
        cmd = b"RREF\x00"
        message = struct.pack("<5sii400s", cmd, interval, index, bytestring)
        assert(len(message)==413)
        #print(message[:50])
        self.sock.sendto(message, (self.xip, self.xport))

