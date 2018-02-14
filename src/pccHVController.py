import pccBaseModule
import os
import time

def HVchannel(position, *discard):
    print("HVchannel: ", position)
    #position = positionTuple[0]
    pY, pX = [int(x) for x in position]
    return pY*5+pX

class HVController(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "HVController"

	self.safeReadMode = False
	if "HVSafeReadMode" in self.config and self.config["HVSafeReadMode"] == "True":
		self.safeReadMode = True

        #self.hvExec = "/home/daq/PCT_HV/PCT_HV -s 0 -c %d %s 2>/dev/null"
	#self.globalHvExec = "/home/daq/PCT_HV/PCT_HV -C %s 2>/dev/null"
        self.hvExec = "%s -s 0 -c %%d %%s 2>/dev/null"%self.config["HVexecutable"]
	self.globalHvExec = "%s -C %%s 2>/dev/null"%self.config["HVexecutable"]
        # Format
        self.HVMap = [(False, 0., 0., 0., 0., 0., 0.) for x in range(25)]
        # here I should put the code to interrogate the HV system
        # and collect info about its current status
	self.loadCurrentStatus()
        # Also this class needs a watchdog to monitor the status
        # of HV channels and eventually raise alarms

    def grabGlobalData(self, cmd):
	#retry = True
	while True:
		dataChan = os.popen(self.globalHvExec%cmd)
		info = dataChan.readlines()
		dataChan.close()
		if len(info)>0:
			return info[-1].strip().split()
		elif self.safeReadMode:
			time.sleep(0.1)
		else:
			return [-424242]*25 

    def execPCT_HV(self, position, command):
        print("Sto passando: ", position)
        channel = HVchannel(position)
	
	while True:
	        dataChan = os.popen(self.hvExec%(channel, command))
        	data = dataChan.readlines()
        	dataChan.close()
        	print(data)
	
		if len(data)>0:
		        return data[-1]
		elif self.safeReadMode:
			time.sleep(0.1)
		else:
			return "-424242"

    def setupCmdDict(self):
        self.cmdDict["checkHV"] = self.checkHV
        self.cmdDict["setHVfake"] = self.setHVfake
        self.cmdDict["setHV"] = self.setHV
        self.cmdDict["turnOnChannel"] = self.turnOnChannel
        self.cmdDict["turnOffChannel"] = self.turnOffChannel
        self.cmdDict["status"] = self.status
        self.cmdDict["readVoltage"] = self.readVoltage
        self.cmdDict["readCurrent"] = self.readCurrent
        self.cmdDict["readImpedance"] = self.readImpedance
        self.cmdDict["getChannelData"] = self.getChannelData
        self.cmdDict["readSetVoltage"] = self.readSetVoltage
        self.cmdDict["readSetCurrent"] = self.readSetCurrent
        self.cmdDict["readSetImpedance"] = self.readSetImpedance
        self.cmdDict["getSetChannelData"] = self.getSetChannelData
        self.cmdDict["getFullChannelData"] = self.getFullChannelData
	self.cmdDict["allHVStatus"] = self.loadCurrentStatus
	self.cmdDict["doAllChanOn"] = self.doAllChanOn
	self.cmdDict["doAllChanOff"] = self.doAllChanOff

    def loadCurrentStatus(self):
	powerInfo = self.grabGlobalData("-S")
	currentVoltageInfo = self.grabGlobalData("-V")
	currentCurrentInfo = self.grabGlobalData("-I")
	currentImpedanceInfo = self.grabGlobalData("-Z")		
	setVoltageInfo = self.grabGlobalData("-v")
	setCurrentInfo = self.grabGlobalData("-i")
	setImpedanceInfo = self.grabGlobalData("-z")
	for x in range(25):
		self.HVMap[x] = (
			powerInfo[x],
			float(currentVoltageInfo[x]),
			float(currentCurrentInfo[x]),
			float(currentImpedanceInfo[x]),
			float(setVoltageInfo[x]),
			float(setCurrentInfo[x]),
			float(setImpedanceInfo[x]) 
			)
		print("%02d"%x, self.HVMap[x])


    def doAllChanOn(self, *discard):
	return self.grabGlobalData("-1")

    def doAllChanOff(self, *discard):
	return self.grabGlobalData("-0")

    def checkHV(self, position, *discard):
	status = self.status(position)
	if status == "Off":
		self.logger.warn("Channel %d for position %s is currently OFF"%(HVchannel(position), position))
		return False
	
	voltage = -424242
	setVoltage = -424242
	delta = 0.1 # Volt

	while setVoltage == -424242:
		time.sleep(0.5)
		setVoltage = self.readSetVoltage(position)

	while voltage == -424242 or abs(voltage-setVoltage)>delta:
		time.sleep(0.5)
		voltage = self.readVoltage(position)

        return True

    def getChannelData(self, position, *discard):
        v = self.readVoltage(position)
        i = self.readCurrent(position)
        z = self.readImpedance(position)
        return (v,i,z)

    def getSetChannelData(self, position, *discard):
        v = self.readSetVoltage(position)
        i = self.readSetCurrent(position)
        z = self.readSetImpedance(position)
        return (v,i,z)

    def getFullChannelData(self, position, *discard):
	dataCurrent = self.getChannelData(position)
	dataSet     = self.getSetChannelData(position)
	return dataCurrent+dataSet

    def setHVfake(self, position, index, *discard):
	return self.setHV(int(index), 1, 1, position, "pippo", [1000, 1100, 1200, 1300, 1400])

    def setHV(self, args):
	print(args)
        vPoint, posX, posY, position, crystalID, voltages = args
	vPoint = int(vPoint)
        print(vPoint, posX, posY, position, crystalID, voltages)
        
        print("here I'm supposed to set the HV channel for crystal %s to the specified value of %d"%(crystalID, voltages[vPoint]))
        print("The relevant channelId is: ", HVchannel(position))
	return self.execPCT_HV(position, "-H %d"%voltages[vPoint])

    def turnOnChannel(self, position, *discard):
	return self.execPCT_HV(position, "-1")

    def turnOffChannel(self, position, *discard):
	return self.execPCT_HV(position, "-0")
    
    def status(self, position, *discard):
	return self.execPCT_HV(position, "-S")

    def readVoltage(self, position, *discard):
	return float(self.execPCT_HV(position, "-V"))

    def readCurrent(self, position, *discard):
	return float(self.execPCT_HV(position, "-I"))

    def readImpedance(self, position, *discard):
	return float(self.execPCT_HV(position, "-Z"))

    def readSetVoltage(self, position, *discard):
	return float(self.execPCT_HV(position, "-v"))

    def readSetCurrent(self, position, *discard):
	return float(self.execPCT_HV(position, "-i"))

    def readSetImpedance(self, position, *discard):
	return float(self.execPCT_HV(position, "-z"))

