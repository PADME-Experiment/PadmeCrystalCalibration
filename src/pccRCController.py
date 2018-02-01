import pccBaseModule
import pccCommandCenter
import subprocess
import time

class RCController(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "RCController"
        self.status = "idle"
        self.daqPid = -1

    def setupCmdDict(self):
        self.cmdDict["status"]    = self.status
        self.cmdDict["runDAQ"]    = self.runDAQ

    def status(self):
        if self.status == "running":
            return "DAQ running with pid %d"%self.daqPid
        else:
            return "DAQ idle"

    def runDAQ(self, sequenceName, position, crystalID):
        
        dataQueue = pccBaseModule.Queue.Queue()
        infoData = pccCommandCenter.Command(("HVController", "getChannelData", position), answerQueue = dataQueue)
        self.commandQueue.put(infoData)
        answer = dataQueue.get(block=True)
        print("Response from HVController: ", answer)

        daqConfigFile = self.config["DAQConfigFile"][position]

        daqProcess  = ["PadmeDAQ", "-c", daqConfigFile]
        logFileName = "%s/log/CrystalTesting_%s_%s_%s.log"%(self.config["DAQConfig"], position, crystalID, voltage)
        logFile     = open(logFileName, "wt")

        self.logger.info("%s: starting DAQ process for sequence %s, crystal %s@%s with %sV"%(self.name, sequenceName, crystalID, position, voltage))

        # for looks - TO REMOVE!
        time.sleep(1)
        return "DAQ ran without problems"

        daqProcess = subprocess.Popen(daqProcess, stdout=logFile)

        self.status = "running"
        self.daqPid = daqProcess.pid()

        self.logger.info("%s: DAQ process started with pid %d"%(self.name, self.daqPid))

        notDone = True
        while notDone:
            rv = daqProcess.poll()
            if rv != None:
                notDone = False
            else:
                time.sleep(1)

        self.logger.info("%s: DAQ process %d finished with return value %d"%(self.name, self.daqPid, rv))

        self.status = "idle"
        self.daqPid = -1

        return "DAQ done"

    class Lvl1Controller(pccBaseModule.BaseModule):
        def __init__(self, logger, configuration):
            pccBaseModule.BaseModule.__init__(self, logger, configuration)
            self.name = "Lvl1Controller"
            self.processingQueue = []

        def setupCmdDict(self):
            self.cmdDict = {}
            self.cmdDict["status"]    = self.status
            self.cmdDict["processRun"] = self.processRun

        def processRun(self, rawDataFile):
            pass