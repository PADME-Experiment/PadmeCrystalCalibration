#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 12:11:54 2017

@author: franz
"""
from __future__ import print_function
import pccServer
import os
import argparse

import pccCommandCenter
import pccLogger
import pccTcpServer
import pccMoveController
import time
import asyncore

# start and setup server
# check config files
# check availability of infos

# ask for list of crystals from operator
# ask for list of voltages from operator

# set voltage of HV to V0
# position XY motors for source @ 0,0
# move to position of center of first crystal
# check HV 
# if okay, start, else wait 1s
# config run, crystal mask, crystal name for output file
# start run
# wait...
# run finished? start postprocessing
# move to next crystal... again


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=42424, type=int, help="the TCP port for the server")
    parser.add_argument("--config", type=str, help="the configuration file for the server")
    return parser.parse_args()


if __name__ == "__main__":
    args = parseArguments()

    threadList = []

    configuration = {}
    configuration["MovementServer"] = "http://192.168.0.52"
    configuration["TCPPort"] = 42424

    theLogger = pccLogger.PadmeLogger()
    threadList.append(theLogger)
    theLogger.start()
    theLogger.addWriter("print", pccLogger.PrintLoggerObject())
    theLogger.trace("logger is active...")

    theCommandCenter = pccCommandCenter.CommandCenter(theLogger, configuration)
    threadList.append(theCommandCenter)
    theCommandCenter.start()

    theTcpServer = pccTcpServer.TcpServer(theLogger, configuration)
    theCommandCenter.inputQueue.put(pccCommandCenter.Command(("CommandCenter", "addModule", theTcpServer.name, theTcpServer)))

    theMoveController = pccMoveController.MoveController(theLogger, configuration)
    threadList.append(theMoveController)
    theMoveController.start()
    theCommandCenter.inputQueue.put(pccCommandCenter.Command(("CommandCenter", "addModule", theMoveController.name, theMoveController)))

    asyncore.loop(timeout=0.1)
    time.sleep(1)

    for threadIdx in range(len(threadList)-1,-1,-1):
        threadList[threadIdx].exit()
        threadList[threadIdx].join()

    # theCommandCenter.exit()
    # theCommandCenter.join()
    # print("CC joined....")
    # theLogger.exit()
    # #theLogger.trace("Time to die...")
    # theLogger.join()
    print("Done!")