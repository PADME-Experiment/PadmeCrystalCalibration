from __future__ import print_function
import sys
import time
import threading
import tsdict
import pccCommandCenter
import httplib

if sys.version_info.major == 3:
    import queue as Queue
else:
    import Queue

class MoveController(threading.Thread):
    def __init__(self, logger, configuration):
        threading.Thread.__init__(self)
        self.logger = logger
        self.inputQueue = Queue.Queue()
        self.name = "MoveController"
        self.config = configuration

        self.arduinoAddress = self.config["MovementServer"]

    def commandQueue(self, queue):
        self.commandQueue = queue

    def exit(self):
        self.goOn = False

    def httpGet(self, *getData):
        gd = "/".join(getData)
        conn = httplib.HTTPConnection(self.arduinoAddress)
        conn.request("GET", "/arduino/%s"%gd)
        response = conn.getresponse()
        self.logger.debug("%d %s %s"%(response.status, response.reason, response.read()))
        conn.close()
        return (response.status, response.reason, response.read())

    # Arduino commands --
    def set_zero(self):
        info = self.httpGet("zero", "ok")
        return info
    
    def read_position(self):
        info = self.httpGet("leggi", "ok")
        return info

    def set_xabs(self, value):
        info = self.httpGet("xabs", str(value))
        return info

    def set_yabs(self, value):
        info = self.httpGet("yabs", str(value))
        return info
        
    def set_xy(self, xval, yval):
        info = self.httpGet("setxy", str(xval), str(yval))
        return info
        
    def resetx(self):
        info = self.httpGet("resetx", "ok")
        return info

    def resety(self):
        info = self.httpGet("resety", "ok")
        return info

    def run(self):
        self.logger.debug("MoveController starting...")
        self.goOn = True
        while self.goOn:
            try:
                cmd = self.inputQueue.get(timeout=1)
            except Queue.Empty:
                continue

            self.logger.debug("Received message to", cmd.receiver(), cmd.command(), cmd.tokenId())
            self.processCommand(cmd)
            
        print("Farewell MoveController...")
                
    def processCommand(self, cmd):
        theCommand = cmd.command()

        if theCommand == "status":
            response = self.read_position()
            cmd.answer(self.name, response)            

        if theCommand == "idle":
            response = self.read_position()
            if len(response.strip())>0:
                cmd.answer(self.name, True)
            else:
                cmd.answer(self.name, False)
            
        if theCommand == "zero":
            response = self.set_zero()
            cmd.answer(self.name, response)            
    
        if theCommand == "set_xabs":
            response = self.set_xabs(cmd.args()[0])
            cmd.answer(self.name, response)            

        if theCommand == "set_yabs":
            response = self.set_yabs(cmd.args()[0])
            cmd.answer(self.name, response)            

        if theCommand == "set_xy":
            response = self.set_xy(cmd.args()[0], cmd.args()[1])
            cmd.answer(self.name, response)

        if theCommand == "resetx":
            response = self.resetx()
            cmd.answer(self.name, response)            
        
        if theCommand == "resety":
            response = self.resety()
            cmd.answer(self.name, response)            

        if theCommand == "exit":
            self.goOn = False
