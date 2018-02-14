import pccBaseModule
import pccCommandCenter
import subprocess
import time
import os

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

	answer = self.sendSyncCommand("HVController", "getFullChannelData", position)
        print("Response from HVController: ", answer)
	print("Data: ", answer.args())

	daqWorkDir = "%s/%s"%(self.config["DAQConfigPath"], sequenceName)

	voltage, current, _, setVoltage, setCurrent, _ = answer.args()[0]

        daqConfigFile = self.config["DAQConfigFiles"][position]

	outputFileName = "CrystalTesting_at-%s_CID-%s_Vreal-%s_Ireal-%s_Vset-%s"%(position, crystalID, voltage, current, setVoltage)

        logFileName = "%s/log/%s.log"%(daqWorkDir, outputFileName)
        logFile     = open(logFileName, "wt")

	print("LogFileName  = ", logFileName)
	print("DAQ Work dir = ", daqWorkDir)

	print("Removing init files from run/")
	os.system("rm %s/run/init*"%daqWorkDir)

        daqCommand  = [self.config["PadmeDAQexecutable"], "-c", daqConfigFile]

        self.logger.info("%s: starting DAQ process for sequence %s, crystal %s@%s with %sV"%(self.name, sequenceName, crystalID, position, voltage))

        # for looks - TO REMOVE!
        #time.sleep(1)
        print("This is what I'm about to exec: %s"%daqCommand)
        #return "DAQ ran without problems"

	daqProcess = subprocess.Popen(daqCommand, stdout=logFile, cwd=daqWorkDir)
	print("This is the process: ", daqProcess)

        self.status = "running"
        self.daqPid = daqProcess.pid

        self.logger.info("%s: DAQ process started with pid %d"%(self.name, self.daqPid))

        notDone = True
        while notDone:
            rv = daqProcess.poll()
            if rv != None:
                notDone = False
            else:
                time.sleep(1)

	logFile.close()

	outputDAQdata = os.popen("ls -1 %s/data/CrystalCheck*"%daqWorkDir)
	outputDAQfile = outputDAQdata.readlines()[-1].strip()
	outputDAQdata.close()


	dt = outputDAQfile.split("+")[1]
	dataFileName = "%s/data/%s%s"%(daqWorkDir, outputFileName, dt)

	print("Found the DAQ file: %s"%outputDAQfile)
	print("Moving it to: %s"%dataFileName)

	os.system("mv %s %s"%(outputDAQfile, dataFileName))

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
