import pccBaseModule
import httplib

class MoveController(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "MoveController"
        self.arduinoAddress = self.config["MovementServer"]

    def setupCmdDict(self):
        self.cmdDict["read_position"] = self.read_position
        self.cmdDict["idle"]          = self.idle
        self.cmdDict["set_zero"]      = self.set_zero
        self.cmdDict["set_xabs"]      = self.set_xabs
        self.cmdDict["set_yabs"]      = self.set_yabs
        self.cmdDict["set_xy"]        = self.set_xy
        self.cmdDict["resetx"]        = self.resetx
        self.cmdDict["resety"]        = self.resety
        
    def httpGet(self, *getData):
        gd = "/".join(getData)
        self.logger.debug(gd)
        return (200, 'OK', "yarghhhh")
        conn = httplib.HTTPConnection(self.arduinoAddress)
        conn.request("GET", "/arduino/%s"%gd)
        response = conn.getresponse()
        self.logger.debug("%d %s %s"%(response.status, response.reason, response.read()))
        conn.close()
        return (response.status, response.reason, response.read())

    # Arduino commands --
    def set_zero(self):
        info = self.httpGet("zero", "ok")
        return info
    
    def read_position(self):
        info = self.httpGet("leggi", "ok")
        return info

    def set_xabs(self, value):
        info = self.httpGet("xabs", str(value))
        return info

    def set_yabs(self, value):
        info = self.httpGet("yabs", str(value))
        return info
        
    def set_xy(self, xval, yval):
        info = self.httpGet("setxy", str(xval), str(yval))
        return info
        
    def resetx(self):
        info = self.httpGet("resetx", "ok")
        return info

    def resety(self):
        info = self.httpGet("resety", "ok")
        return info

    def idle(self):
        # the arduino Yun HTTP server
        # times out when the controller 
        # is busy moving the step-by-step 
        # motors, returning a 500 OK HTTP 
        # response. 200 OK is returned 
        # upon success
        response = self.read_position()
        if response[0] == 200:
            return True
        else:
            return False