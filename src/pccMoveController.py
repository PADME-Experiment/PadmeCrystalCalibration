import pccBaseModule
import httplib
import time

class MoveController(pccBaseModule.BaseModule):
    def __init__(self, logger, configuration):
        pccBaseModule.BaseModule.__init__(self, logger, configuration)
        self.name = "MoveController"
        self.arduinoAddress = self.config["MovementServer"]
        self.currentX = -1
        self.currentY = -1

    def setupCmdDict(self):
        self.cmdDict["read_position"] = self.read_position
        self.cmdDict["idle"]          = self.idle
        self.cmdDict["set_zero"]      = self.set_zero
        self.cmdDict["set_xabs"]      = self.set_xabs
        self.cmdDict["set_yabs"]      = self.set_yabs
        self.cmdDict["move_xy"]       = self.move_xy
        self.cmdDict["set_xy"]        = self.set_xy
        self.cmdDict["resetx"]        = self.resetx
        self.cmdDict["resety"]        = self.resety
        self.cmdDict["resetXY"]       = self.resetXY
        
    def httpGet(self, *getData):
        gd = "/".join(getData)
        self.logger.debug(gd)
        # remove to test the actual movement
        #return (200, 'OK', "this is a rather fake response!!!!!")
        print(self.arduinoAddress)
        conn = httplib.HTTPConnection(self.arduinoAddress)
        conn.connect()
        conn.request("GET", "/arduino/%s"%gd)  
        time.sleep(0.4)
        response = conn.getresponse()
        data2return = (response.status, response.reason, response.read())
        self.logger.debug("%d %s %s"%data2return)
        conn.close()
        return data2return

    # Arduino commands --
    # Here is assume that the zero position corresponds to the source
    # being correctly centered on the crystal (0,0).
    # All movements shall be considered relative to this position!
    def set_zero(self):
        info = self.httpGet("zero", "ok")
        self.currentX = 0
        self.currentY = 0
        return info
    
    # read the current position from Arduino and the one stored in the class
    def read_position(self):
        info = self.httpGet("leggi", "ok")
        return (info, (self.currentX, self.currentY))

    def move_xy(self, xval, yval):
        info1 = self.set_xabs(xval)
        info2 = self.set_yabs(yval)
        return (info1, info2)

    # set the absolutel position along the X axis
    def set_xabs(self, value):
        info = self.httpGet("xabs", str(value))
        self.currentX = value
        return info

    # set the absolutel position along the Y axis
    def set_yabs(self, value):
        info = self.httpGet("yabs", str(value))
        self.currentY = value
        return info
        
    # Assigns coords to the current position of the motors, no movement is implied
    def set_xy(self, xval, yval):
        #infoX = self.set_xabs(xval)
        #infoY = self.set_yabs(yval) 
        info = self.httpGet("setxy", str(xval), str(yval))
        self.currentX = xval
        self.currentY = yval
        return (infoX, infoY)
    
    # move back to zero along X axis
    def resetx(self):
        info = self.httpGet("resetx", "ok")
        self.currentX = 0
        return info

    # move back to zero along Y axis
    def resety(self):
        info = self.httpGet("resety", "ok")
        self.currentY = 0
        return info

    # combine the two resets from above
    def resetXY(self):
        infoX = self.httpGet("resetx", "ok")
        infoY = self.httpGet("resety", "ok")
        return (infoX, infoY)

    def idle(self):
        # the arduino Yun HTTP server times out when the controller 
        # is busy moving the step-by-step motors, returning a 500 OK HTTP 
        # response. 200 OK is returned upon success
        response = self.read_position()
        if response[0] == 200:
            return True
        else:
            return False
