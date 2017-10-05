from __future__ import print_function
import sys
import time
import threading
import tsdict

if sys.version_info.major == 3:
    import queue as Queue
else:
    import Queue

class Command(object):
    def __init__(self, command=(), tokenId=42, answerQueue=None):
        self.cmd = command
        self.token = str(tokenId)

        if answerQueue:
            self.wantAnswer = True
            self.answerQueue = answerQueue
        else:
            self.wantAnswer = False

    def receiver(self):
        return self.cmd[0]

    def command(self):
        return self.cmd[1]

    def tokenId(self):
        return self.token

    def args(self):
        return self.cmd[2:]
        
    def answer(self, sender, *theAnswer):
        theRealAnswer = (sender, "answer") + theAnswer
        answerMessage = Command(theRealAnswer, tokenId=self.tokenId())
        if self.wantAnswer:
            self.answerQueue.put(answerMessage)

class CommandCenter(threading.Thread):
    def __init__(self, logger, configuration):
        self.cmdCenter = tsdict.TSDict()
        threading.Thread.__init__(self)
        self.logger = logger
        self.inputQueue = Queue.Queue()
        self.name = "CommandCenter"
        self.config = configuration

    def addModule(self, name, module):
        self.logger.debug(self.name, "- addModule: ", name)
        module.commandQueue(self.inputQueue)
        self.cmdCenter[name] = module

    def rmModule(self, name):
        self.logger.debug(self.name, "- rmModule: ", name)
        if name in self.cmdCenter:
            del(self.cmdCenter[name])
    
    def sendCommand(self, cmd):
        self.inputQueue.put(cmd)

    def exit(self):
        self.goOn = False

    def run(self):
        self.logger.debug("CommandCenter starting...")
        self.goOn = True
        while self.goOn:
            try:
                cmd = self.inputQueue.get(timeout=1)
            except Queue.Empty:
                continue

            dest = cmd.receiver()
            self.logger.debug("Received message to", cmd.receiver(), cmd.command(), cmd.tokenId())
            if dest == "CommandCenter":
                self.processCommand(cmd)
            else:
                if module in self.cmdCenter[dest]:
                    module = self.cmdCenter[dest]
                    module.processCommand(cmd)
                else:
                    self.logger.error(self.name, ": Whoops, module", module, "not found...")
        print("Farewell CC...")
                
    def processCommand(self, cmd):
        theCommand = cmd.command()

        if theCommand == "addModule":
            self.addModule(*cmd.args())
        
        if theCommand == "rmModule":
            self.rmModule(*cmd.args())

        if theCommand == "exit":
            self.goOn = False
        
        if theCommand == "moduleList":
            moduleList = self.cmdCenter.keys()
            cmd.answer(self.name, moduleList)
