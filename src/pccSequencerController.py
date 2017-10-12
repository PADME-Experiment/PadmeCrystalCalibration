import pccBaseModule

class Sequencer(pccBaseModule.BaseModule):
    def __init__(self, logger, sequenceName):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.sequenceName = sequenceName
        self.needHV = True
        self.needCrystals = True
        self.needPositions = True
        self.name = "Sequencer"

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
            self.theSequence.append(("syncState",))
            for crystal in dataPoints:
                self.theSequence.append(("moveXY", dataPoints[1]))
                self.theSequence.append(("syncState",))
                self.theSequence.append(("runDAQ", dataPoints[0]))
                self.theSequence.append(("syncState",))

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
    

class SequencerController(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "SequencerController"

    def exit(self):
        self.logger.warn("This needs to do a little more than the usual...")

    def setupCmdDict(self):
        self.cmdDict["startSequence"] = self.startSequence
        self.cmdDict["getSequence"]   = self.getSequence
        self.cmdDict["loadSequence"]  = self.loadSequence
        self.cmdDict["stopSequence"]  = self.stopSequence
        self.cmdDict["resetSequence"] = self.resetSequence
        self.cmdDict["loadCrystals"]  = self.loadCrystals
        self.cmdDict["getCrystals"]   = self.getCrystals
        self.cmdDict["loadHVpoints"]  = self.loadHVpoints
        self.cmdDict["getHVpoints"]   = self.getHVpoints 
        self.cmdDict["loadPositions"] = self.loadPositions 
        self.cmdDict["getPositions"]  = self.getPositions
