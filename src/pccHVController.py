from __future__ import print_function
import sys
import time
import threading
import tsdict
import pccCommandCenter

if sys.version_info.major == 3:
    import queue as Queue
else:
    import Queue

class HVController(threading.Thread):
    def __init__(self, logger, configuration):
        threading.Thread.__init__(self)
        self.logger = logger
        self.inputQueue = Queue.Queue()
        self.name = "HVController"
        self.config = configuration
        self.setupCmdDict()


    def setupCmdDict(self):
        self.cmdDict = {}
        self.cmdDict["checkHV"] = self.checkHV
        self.cmdDict["setHV"] = self.setHV
        self.cmdDict["turnOnChannel"] = self.turnOnChannel
        self.cmdDict["turnOffChannel"] = self.turnOnChannel
        self.cmdDict["status"] = self.status
        
    def commandQueue(self, queue):
        self.commandQueue = queue

    def exit(self):
        self.goOn = False

    def run(self):
        self.logger.debug("HVController starting...")
        self.goOn = True
        while self.goOn:
            try:
                cmd = self.inputQueue.get(timeout=1)
            except Queue.Empty:
                continue

            self.logger.debug("Received message to", cmd.receiver(), cmd.command(), cmd.tokenId())
            self.processCommand(cmd)
            
        print("Farewell HVController...")
                
    def processCommand(self, cmd):
        theCommand = cmd.command()

        if theCommand == "exit":
            self.goOn = False
        elif theCommand in self.cmdDict:
            result = self.cmdDict[theCommand](cmd)
            cmd.answer(self.name, result)
        else:
            self.logger.warn(self.name, "Command %s not found. Ignoring."%theCommand)