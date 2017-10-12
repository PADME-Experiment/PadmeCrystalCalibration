import pccBaseModule

class HVController(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "HVController"

    def setupCmdDict(self):
        self.cmdDict["checkHV"] = self.checkHV
        self.cmdDict["setHV"] = self.setHV
        self.cmdDict["turnOnChannel"] = self.turnOnChannel
        self.cmdDict["turnOffChannel"] = self.turnOnChannel
        self.cmdDict["status"] = self.status