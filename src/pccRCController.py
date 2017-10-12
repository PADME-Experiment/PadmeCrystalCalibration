import pccBaseModule

class RCController(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "RCController"

    def setupCmdDict(self):
        self.cmdDict = {}
        self.cmdDict["configRun"] = self.configRun
        self.cmdDict["startRun"]  = self.startRun
        self.cmdDict["runStatus"] = self.runStatus
        self.cmdDict["status"]    = self.status
