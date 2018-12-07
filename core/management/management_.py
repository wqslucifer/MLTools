from multiprocessing import Queue


class manageProcess:
    def __init__(self):
        self.processList = list()
        self.processCOMDir = dict()
        self.processIDDir = dict()
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

    def setIDDir(self, processID, pq):
        processListIndex = self.processList.index(pq)
        self.processIDDir[processID] = processListIndex, pq

    def getProcessCOMQ(self, processListIndex):
        return self.processCOMDir[processListIndex]

