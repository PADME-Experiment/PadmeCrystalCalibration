from __future__ import print_function
import sys
import threading
import tsdict
import pccCommandCenter

if sys.version_info.major == 3:
    import queue as Queue
else:
    import Queue

class BaseModule(threading.Thread):
    def __init__(self, logger, configuration):
        threading.Thread.__init__(self)
        self.logger = logger
        self.config = configuration
        self.inputQueue = Queue.Queue()
        self.name = "BaseModule"
        self.cmdDict = {}
        self.setupCmdDict()

    def setupCmdDict(self):
        self.logger.error(self.name, "module does not have a configured cmdDict.")

    def setCommandQueue(self, queue):
        self.commandQueue = queue

    def exit(self):
        #self.commandQueue.put("exitNowPlease")
        self.goOn = False

    def run(self):
        self.logger.debug(self.name+" starting...")
        self.goOn = True
        while self.goOn:
            try:
                cmd = self.inputQueue.get(timeout=0.1)
            except Queue.Empty:
                continue

            if cmd == "exitNowPlease":
                print("Got exitNowPlease")
                self.goOn = False
                break

            self.logger.debug(self.name, ": received message to", cmd.receiver(), cmd.command(), cmd.tokenId())
            self.processCommand(cmd)
            
        print(self.name, "farewell...")
                
    def processCommand(self, cmd):
        theCommand = cmd.command()

        if theCommand == "exit":
            self.goOn = False
        elif theCommand in self.cmdDict:
            result = self.cmdDict[theCommand](*cmd.args())
            cmd.answer(self.name, result)
        else:
            self.logger.warn(self.name, "Command %s not found. Ignoring."%theCommand)