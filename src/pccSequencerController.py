import pccBaseModule
import pccCommandCenter
import pccDAQConfigFileMaker as dm
import os
import sys

if sys.version_info.major == 3:
    import queue as Queue
else:
    import Queue

movementPattern = [
    # Vidx, Row, Col1,Col2,..,.
    (0, (0, (0, 1, 2, 3, 4))),
    (0, (1, (4, 3, 2, 1, 0))),
    (0, (2, (0, 1, 2, 3, 4))),
    (0, (3, (4, 3, 2, 1, 0))),
    (0, (4, (0, 1, 2, 3, 4))),
    (1, (3, (4, 3, 2, 1, 0))),
    (1, (4, (0, 1, 2, 3, 4))),
    (1, (2, (4, 3, 2, 1, 0))),
    (1, (1, (0, 1, 2, 3, 4))),
    (1, (0, (4, 3, 2, 1, 0))),
    (2, (1, (0, 1, 2, 3, 4))),
    (2, (0, (4, 3, 2, 1, 0))),
    (2, (2, (0, 1, 2, 3, 4))),
    (2, (3, (4, 3, 2, 1, 0))),
    (2, (4, (0, 1, 2, 3, 4))),
    (3, (3, (4, 3, 2, 1, 0))),
    (3, (4, (0, 1, 2, 3, 4))),
    (3, (2, (4, 3, 2, 1, 0))),
    (3, (1, (0, 1, 2, 3, 4))),
    (3, (0, (4, 3, 2, 1, 0))),
    (4, (1, (0, 1, 2, 3, 4))),
    (4, (0, (4, 3, 2, 1, 0))),
    (4, (2, (0, 1, 2, 3, 4))),
    (4, (3, (4, 3, 2, 1, 0))),
    (4, (4, (0, 1, 2, 3, 4)))
]


class Sequencer(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration, sequenceConfigFile):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "Sequencer"
        self.sequenceConfigFile = sequenceConfigFile

        # Load the actual test setup
        self.readInConfiguration()

        if not self.hasTestSetConfig:
            return

        # Parse the test set configuration
        self.testSetConfigParser()

        # Setup the DAQ dir based on the available info
        self.setupDAQ()

        # Prepare the test sequences
        self.createSequence()

    def setupCmdDict(self):
        #self.cmdDict["status"] = self.status
        #self.cmdDict["getSequence"] = self.getSequence
        self.cmdDict["resetXY"] = self.resetXY
        self.cmdDict["moveXY"] = self.moveXY
        self.cmdDict["setHV"] = self.setHV
        self.cmdDict["runDAQ"] = self.runDAQ

    def readInConfiguration(self):
        self.hasTestSetConfig = False
        if not os.path.isfile(self.sequenceConfigFile):
            self.logger.warn("%s cannot read the configuration file: %s", self.name, self.sequenceConfigFile)
            return

        df = open(self.sequenceConfigFile)
        myConfig = df.readlines()
        df.close()
        
        myConfig2 = filter(lambda x: (x[0]!="#" and x.strip()!=''), myConfig)
    
        self.testSetConfig = dict(map(lambda y: (y[0].strip(), y[1].strip()), map(lambda x: x.strip().split("="), myConfig2)))
        self.hasTestSetConfig = True

        print(self.testSetConfig)

        self.sequenceName = self.testSetConfig["SequenceName"]

    def testSetConfigParser(self):
        if not self.hasTestSetConfig:
            self.logger.warn("%s cannot start sequence %s: no test set configuration available"%(self.name, self.sequenceName))
        
        self.crystalMatrix = []
        for x in range(5):
            # the list neeeds to be formed correctly to then store the data....
            self.crystalMatrix.append([])
            for y in range(5):
                self.crystalMatrix[x].append(("%d%d"%(x,y), "disabled", [0]))

        for pX in range(5):
            for pY in range(5):
                CrystalID = "Crystal%d%d"%(pX,pY)
                print(pX, pY, CrystalID)
                if CrystalID in self.testSetConfig:
                    print("found")
                    datum = self.testSetConfig[CrystalID]
                    crystalID, voltageSet = datum.split()

                    vs = voltageSet.split(":")
                    if len(vs) != 5:
                        vsmin, vsmax = [float(x) for x in voltageSet.split("-")]
                        delta = vsmax-vsmin/4.
                        vs = [vsmin, vsmin+delta, vsmin+2*delta, vsmin+3*delta, vsmax]
                    else:
                        vs = [float(x) for x in vs]

                    if len(vs) != 5:
                        self.logger.error("There's something wrong with the configuration of crystal %s voltage points: %s."%(crystalID, vs))
                        #return

                    self.crystalMatrix[pX][pY] = ("%d%d"%(pX,pY), crystalID, vs)
            
        print("This is the crystal matrix: ", self.crystalMatrix)

    def setupDAQ(self):
        daqPath = "%s/%s"%(self.config["DAQConfigPath"], self.sequenceName)
        dm.mkDaqConfigDir(daqPath)

        daqConfigFiles = {}        

        for crystalX in range(5):
            for crystalY in range(5):
                position = "%d%d"%(crystalX, crystalY)
                cf = dm.mkDaqConfigFile(daqPath, "CrystalTesting", position)
                daqConfigFiles[position] = cf

        self.config["DAQConfigFiles"] = daqConfigFiles

    def createSequence(self):

        dataPoints = []
        for step in movementPattern:
            vIdx = step[0]
            row = step[1][0]
            for col in step[1][1]:
                dataPoints.append((vIdx, row, col, self.crystalMatrix[row][col][0], self.crystalMatrix[row][col][1], self.crystalMatrix[row][col][2]))

        print("Always the crystal matrix: ", self.crystalMatrix)

        self.crystalXsize = int(self.testSetConfig["CrystalXSize"])
        self.crystalYsize = int(self.testSetConfig["CrystalYSize"])

        # These two parameters are the position of the "zero" of 
        # the stepper motors with respect to the corner of the crystal array
        # They are necessary to calculate the absolute positions 
        # to move the radioactive source to.
        # For the "center" of crystal pXpY:
        # Xabs = (pX-0.5)*crystalXSize - initialXoffset
        # Yabs = (pY-0.5)*crystalYSize - initialYoffset
        self.initialXoffset = int(self.testSetConfig["InitialXOffset"])
        self.initialYoffset = int(self.testSetConfig["InitialYOffset"])

        sequenceIndex = 0
        self.theSequence = []
        self.theSequence.append(("resetXY", 0))
        self.theSequence.append(("setHV", dataPoints[sequenceIndex]))
        self.theSequence.append(("syncState", 0))

        while sequenceIndex < len(dataPoints):
            _, pX, pY, position, crystalID, _ = dataPoints[sequenceIndex]
            print(self.crystalXsize, self.crystalYsize, pX, pY)
            print("Loading steps for:", sequenceIndex, dataPoints[sequenceIndex])
            if crystalID != "disabled":
                xAbs = int((pX-0.5) * self.crystalXsize - self.initialXoffset)
                yAbs = int((pY-0.5) * self.crystalYsize - self.initialYoffset)
                self.theSequence.append(("moveXY", (xAbs, yAbs)))
                #print("move")

            if sequenceIndex < len(dataPoints)-1:
                if dataPoints[sequenceIndex+1][4] != "disabled":
                    self.theSequence.append(("setHV", dataPoints[sequenceIndex+1]))
                    #print("HV")
            self.theSequence.append(("syncState", 0))
            
            if crystalID != "disabled":
                self.theSequence.append(("runDAQ", (self.sequenceName, position, crystalID)))
                #print("runDAQ")
            self.theSequence.append(("syncState",0))

            sequenceIndex+=1 

            theSequence2 = []
            syncStateLast = False
            for entry in self.theSequence:
                if entry[0] == "syncState":
                    if not syncStateLast: 
                        syncStateLast = True
                        theSequence2.append(entry)
                else:
                    syncStateLast = False
                    theSequence2.append(entry)

            self.theSequence = theSequence2

            #for entry in self.theSequence:
            #    print(entry)

    def run(self):
        
        commandDict = self.cmdDict
        print("Sequence command queue: ", self.commandQueue)

        tokenDict = {}
        msgTokenId = 65536 # base value for toeknID

        if not self.hasTestSetConfig:
            self.logger.warn("The sequencer cannot run due to a configuration problem.")
            return "The sequencer cannot run due to a configuration problem."

        self.goOn = True
        while self.goOn:
            commandList = []
            freeState = True
            #self.waitingForSync = False
            while len(self.theSequence) > 0:
                if freeState:
                    command = self.theSequence.pop(0)
                
                    if command[0]== "syncState":
                        freeState = False
                        for cmdFull in commandList:            
                            cmd, arg = cmdFull
                            msgTokenId += 1
                            tokenDict[msgTokenId] = cmd
                            self.commandQueue.put(commandDict[cmd](msgTokenId, arg))
                        commandList = []
                    else:
                        commandList.append(command)
                else:
                    if len(tokenDict) == 0:
                        freeState = True
            
                try:
                    # this works also as a "sleep"
                    cmd = self.inputQueue.get(timeout=0.01)
                    print("tokenDict: ", tokenDict)
                    print("Got this back: ", cmd.command(), cmd.tokenId(), cmd.args())
                    retTokenId = int(cmd.tokenId())
                    if retTokenId in tokenDict:
                        print(retTokenId, "is in ", tokenDict)
                        del(tokenDict[retTokenId])
                    print("tokenDict: ", tokenDict)

                except Queue.Empty:
                    pass
            self.logger.info("%s: sequence %s complete."%(self.name, self.sequenceName))
            self.goOn = False


    def resetXY(self, theTokenId, args):
        return pccCommandCenter.Command(("MoveController", "resetXY"), tokenId=theTokenId, answerQueue=self.inputQueue)

    def moveXY(self, theTokenId, args):
        return pccCommandCenter.Command(("MoveController", "move_xy", args[0], args[1]), tokenId=theTokenId, answerQueue=self.inputQueue)

    def setHV(self, theTokenId, args):
        return pccCommandCenter.Command(("HVController", "setHV", args), tokenId=theTokenId, answerQueue=self.inputQueue)
        
    def runDAQ(self, theTokenId, args):
        print("runDAQ: ", args) # sequenceName, position, crystalID
        return pccCommandCenter.Command(("RCController", "runDAQ", args[0], args[1], args[2]), tokenId=theTokenId, answerQueue=self.inputQueue)


class SequencerController(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "SequencerController"
        self.theSequencer = None

    #def exit(self):
    #     self.logger.warn("This needs to do a little more than the usual...")

    def setupCmdDict(self):
        self.cmdDict["loadSequence"]    = self.loadSequence
        self.cmdDict["sequencerStart"]  = self.startSequence
        self.cmdDict["sequencerStop"]   = self.stopSequence
        self.cmdDict["sequencerStatus"] = self.sequencerStatus

    def loadSequence(self, *args):
        fname = args[0]
        if os.path.isfile(fname):
            self.logger.info("%s: creating sequence from file %s"%(self.name, fname))
            self.theSequencer = Sequencer(self.logger, self.config, fname)
            self.theSequencer.setCommandQueue(self.commandQueue)
            return "The Sequencer was correctly created."
        else:
            self.logger.warn("%s: could not find file %s"%(self.name, fname))
            return "There was a problem creating the Sequencer. File %s not found"%fname
    
    def startSequence(self):
        if self.theSequencer:
            self.theSequencer.start()
            self.logger.info("%s: starting sequencer"%self.name)
        else:
            self.logger.warn("%s: could not start sequencer"%self.name)
    
    def stopSequence(self):
        pass

    def sequencerStatus(self):
        pass