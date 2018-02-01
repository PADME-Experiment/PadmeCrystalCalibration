import pccBaseModule
import os
import time

def HVchannel(position):
    print("HVchannel: ", position)
    #position = positionTuple[0]
    pX, pY = [int(x) for x in position]
    return pY*5+pX

class HVController(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "HVController"
        self.hvExec = "/home/daq/PCT_HV/PCT_HV -s 0 -c %d %s"

    def setupCmdDict(self):
        self.cmdDict["checkHV"] = self.checkHV
        self.cmdDict["setHV"] = self.setHVfake
        self.cmdDict["turnOnChannel"] = self.turnOnChannel
        self.cmdDict["turnOffChannel"] = self.turnOffChannel
        self.cmdDict["status"] = self.status
        self.cmdDict["readVoltage"] = self.readVoltage
        self.cmdDict["readCurrent"] = self.readCurrent
        self.cmdDict["readImpedance"] = self.readImpedance
        self.cmdDict["getChannelData"] = self.getChannelData

    def execPCT_HV(self, position, command):
        print("Sto passando: ", position)
        channel = HVchannel(position)
        dataFile = os.popen(self.hvExec%(channel, command))
        data = dataFile.readlines()
        dataFile.close()
        print(data)
        return data

    def checkHV(self, args):
        return "looks good!"

    def getChannelData(self, position):
        v = self.readVoltage(position)
        i = self.readCurrent(position)
        z = self.readImpedance(position)
        return (v,i,z)

    def setHVfake(self, position):
	    return self.setHV(0, 1, 1, position, "pippo", [1000, 1100, 1200, 1300, 1400])

    def setHV(self, *args):
	    print(args)
        vPoint, posX, posY, position, crystalID, voltages = args
        print(vPoint, posX, posY, position, crystalID, voltages)
        
        print("here I'm supposed to set the HV channel for crystal %s to the specified value of %d"%(crystalID, voltages[int(vPoint)]))
        print("The relevant channelId is: ", HVchannel(position))
        print("done... (not really, just for demo)")
	    return self.execPCT_HV(position, "-H %d"%voltages[vPoint])

    def turnOnChannel(self, position):
	    return self.execPCT_HV(position, "-1")

    def turnOffChannel(self, position):
	    return self.execPCT_HV(position, "-0")
    
    def status(self, position):
	    return self.execPCT_HV(position, "-S")

    def readVoltage(self, position):
	    return self.execPCT_HV(position, "-V")

    def readCurrent(self, position):
	    return self.execPCT_HV(position, "-I")

    def readImpedance(self, position):
	    return self.execPCT_HV(position, "-Z")

