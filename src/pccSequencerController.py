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

class Sequencer(threading.Thread):
    def __init__(self, logger, sequenceName):
        threading.Thread.__init__(self)
        self.logger = logger
        self.sequenceName = sequenceName
        self.needHV = True
        self.needCrystals = True
        self.needPositions = True
        self.name = "Sequencer"
        self.communicationQueue = Queue.Queue()

    def set_HVs(self, *hvList):
        self.HVlist = hvList
        self.needHV = False

    def set_Crystals(self, *crystalList):
        self.crystalList = crystalList
        self.needCrystals = False
    
    def set_Positions(self, *positionList):
        self.positionList = positionList
        self.needPositions = False

    def createSequence(self):
        dataPoints = zip(self.crystalList, self.positionList)
        self.theSequence = {}
        for tension in self.HVlist:
            self.theSequence.append(("setHV", tension))
            self.theSequence.append(("resetXY", 0))
            for crystal in dataPoints:
                self.theSequence.append(("moveXY", dataPoints[1]))
                self.theSequence.append(("syncState"))
                self.theSequence.append(("runDAQ", dataPoints[0]))
                self.theSequence.append(("syncState"))

    def run(self):
        if self.needHV:
            self.logger.warn("%s cannot start sequence %s: HV points are not configured"%(self.name, self.sequenceName))
            return

        if self.needCrystals:
            self.logger.warn("%s cannot start sequence %s: the list of crystals is not configured"%(self.name, self.sequenceName))
            return

        if self.needPositions:
            self.logger.warn("%s cannot start sequence %s: the list of positions is not configured"%(self.name, self.sequenceName))
            return

        self.createSequence()

        self.goOn = True
        while self.goOn:
            commandList = []
            freeState = True
            self.waitingForSync = False
            while len(self.theSequence) > 0:
                if freeState:
                    command = self.theSequence.pop(0)
                
                if command[0]== "syncState":
                    freeState = syncExec(commandList)
                    if freeState == True:
                        commandList = []
                else:
                    commandList.append(command)
            
                try:
                    # this works also as a "sleep"
                    cmd = self.communicationQueue.get(timeout=0.01)
                    self.processCommand(cmd)
                except Queue.Empty:
                    pass
                
    def syncExec(self, commandList):
        status = True
        if not self.waitingForSync: self.waitingForSync = True
        
        for cmdTuple in commandList:
            cmd, arg = cmdTuple
            if cmd == "setHV":
                status &= self.setHV(arg)
            if cmd == "resetXY":
                status &= self.resetXY()
            if cmd == "moveXY":
                status &= self.statusXY(arg)
            if cmd == "runDAQ":
                status &= self.runDAQ(arg)

        if status: self.waitingForSync = False
        return status
    

class SequencerController(threading.Thread):
    def __init__(self, logger, configuration):
        threading.Thread.__init__(self)
        self.logger = logger
        self.inputQueue = Queue.Queue()
        self.name = "SequencerController"
        self.config = configuration
        
    def commandQueue(self, queue):
        self.commandQueue = queue

    def exit(self):
        self.goOn = False

    def run(self):
        self.logger.debug("Sequencer starting...")
        self.goOn = True
        while self.goOn:
            try:
                cmd = self.inputQueue.get(timeout=1)
            except Queue.Empty:
                continue

            self.logger.debug("Received message to", cmd.receiver(), cmd.command(), cmd.tokenId())
            self.processCommand(cmd)
            
        print("Farewell Sequencer...")
                
    def processCommand(self, cmd):
        theCommand = cmd.command()

        if theCommand == "startSequence":
            pass
        
        if theCommand == "getSequence":
            pass

        if theCommand == "loadSequence":
            pass
        
        if theCommand == "stopSequence":
            pass

        if theCommand == "resetSequence":
            pass
        


        if theCommand == "exit":
            self.goOn = False
