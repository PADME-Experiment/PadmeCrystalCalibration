"""A thread-safe logger used to feed multiple log channels.
One day I might actually write some documentation for it.
Until then, use the source."""

from __future__ import print_function
import sys
import time
import threading
import tsdict

if sys.version_info.major == 3:
    import queue as Queue
else:
    import Queue


class PadmeLogger(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.destinations = tsdict.TSDict()
        self.dataQueue = Queue.Queue()
        self.logLevel = 0 
    
    def getLogLevel(self):
        return self.logLevel

    def setLogLevel(self, logLevel):
        self.logLevel = logLevel

    def trace(self, *data, **kwds):
        self.logMsg(1, *data, **kwds)

    def debug(self, *data, **kwds):
        self.logMsg(50, *data, **kwds)

    def info(self, *data, **kwds):
        self.logMsg(100, *data, **kwds)

    def warn(self, *data, **kwds):
        self.logMsg(150, *data, **kwds)

    def error(self, *data, **kwds):
        self.logMsg(200, *data, **kwds)

    def fatal(self, *data, **kwds):
        self.logMsg(250, *data, **kwds)

    def logMsg(self, level, *data, **kwds):
        if level>= self.logLevel:
            self.dataQueue.put(data)

    def exit(self):
        self.goOn = False

    def run(self):
        self.goOn = True
        while self.goOn:
            try:
                data = self.dataQueue.get(timeout=1)
            except Queue.Empty:
                continue
            self.printLog(*data)

        print("Farewell...")

    def addWriter(self, name, writer_object):
        self.destinations[name] = writer_object

    def delWriter(self, name):
        if name in self.destinations.keys():
            self.destinations[name].close()
            del(self.destinations[name])

    def printLog(self, *args, **kwds):
        for wobj in self.destinations.keys():
            self.destinations[wobj].print(*args)

    def status(self):
        return self.destinations.keys()


# base class for writer objects...
class PadmeLoggerObject(object):
    def print(self, *args):
        pass

    def close(self):
        pass

# print wrapper
class PrintLoggerObject(PadmeLoggerObject):
    def __init__(self, sep=' ', end='\n', file=sys.stdout):
        self.sep  = sep
        self.end  = end
        self.file = file

    def print(self, *args):
        message = " ".join(args)
        print(message, sep=self.sep, end=self.end, file=self.file)
    
class LogMessage(PadmeLoggerObject):
    def __init__(self, logFileName, dateFormat="[%d %b %Y - %H:%M:%S]"):
        self.logFileName = logFileName
        self.dateFormat  = dateFormat
        self.createLogfile()

    def createLogfile(self):
        try:
            testFile = open(self.logFileName)
        except FileNotFoundError:
            self.logfile = open(self.logFileName,"w")
        else:
            self.logfile = open(self.logFileName,"a")

    def print(self, *args):
        message = " ".join(args)
        dt      = time.strftime(self.dateFormat)
        message = "%s %s\n"%(dt, message)
        self.logfile.write(message)

    def close(self):
        self.logfile.flush()
        self.logfile.close()