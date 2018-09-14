import os
import sys
import json
import time
from PyQt5 import QtCore
from multiprocessing import Queue
from process import QtReceiver,MyReceiver
from PyQt5.QtCore import QThread, pyqtSignal,QObject
import GENERAL

class manageProcess:
    def __init__(self):
        self.processList = list()
        self.processCOMDir = dict()
        self.processPIDDir = dict()
        self.sendQueueList = list()
        self.recvQueueList = list()
        self.receiverList = list()

    def setProcessList(self, processList):
        self.processList = processList

    def setCOMDir(self, processListIndex):
        sendQ = Queue(5)
        recvQ = Queue(5)
        self.sendQueueList.append(sendQ)
        self.recvQueueList.append(recvQ)
        self.processCOMDir[processListIndex] = sendQ, recvQ
        return sendQ, recvQ

    def setPIDDir(self, pq, PID):
        processListIndex = self.processList.index(pq)
        self.processPIDDir[processListIndex] = PID

    def getProcessCOMQ(self, processListIndex):
        return self.processCOMDir[processListIndex]

