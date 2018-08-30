import os
import time
import numpy as np
import pandas as pd

from threading import Thread
from multiprocessing import Process, current_process, Queue, JoinableQueue, Pipe
from PyQt5.QtCore import QThread, pyqtSignal

class processQueue(Process):
    def __init__(self, sendQueue:Queue, receiveQueue:Queue):
        super(processQueue, self).__init__()
        # local data
        self.trainSet = None
        self.testSet = None
        self.target = None
        self.features = None
        self.processQ = None
        self.numericFeatures = None
        self.categoricalFeatures = None
        self.saveData = None
        # comm data
        self.sendQueue = sendQueue
        self.receiveQueue = receiveQueue
        self.monitor = None

    # manage func
    def addProcess(self, processFunc):
        pass

    def delProcess(self, index):
        pass

    def setNumericFeature(self, features):
        pass

    def setCategoricalFeature(self, features):
        pass

    def moveProcess(self, curIndex, targetIndex):
        pass

    def run(self):
        self.test()

    def test(self):
        self.monitor = MyReceiver(self.receiveQueue, self)
        self.monitor.setDaemon(True)
        self.monitor.start()
        print('test start')
        self.sendQueue.put('test process working')
        time.sleep(3)
        print('test end')

    # process func
    def fillNA(self, value):
        pass

    # comm func
    def curProcess(self):
        pass

    def monitorThread(self):
        pass

class MyReceiver(Thread):
    def __init__(self, queue:Queue, target):
        super(MyReceiver, self).__init__()
        self.queue = queue
        self.target = target

    def run(self):
        print('thread start')
        while self.target.is_alive():
            while not self.queue.empty():
                text = self.queue.get()
                print(text)
        print('thread end')



class QtReceiver(QThread):
    mysignal = pyqtSignal(str)

    def __init__(self, queue, target):
        super(QtReceiver, self).__init__()
        self.queue = queue
        self.target = target

    def run(self):
        while True: # self.target.is_alive()
            while not self.queue.empty():
                text = self.queue.get()
                # self.mysignal.emit(text)
                print(text)
        print('process end')


if __name__ == '__main__':
    sendQ = Queue(5)
    recvQ = Queue(5)
    p = processQueue(sendQ, recvQ)
    t = QtReceiver(sendQ, p)
    t.start()
    p.start()
    recvQ.put('process commd 1')