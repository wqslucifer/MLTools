import os
import gc
import time
import cv2
import numpy as np
import pandas as pd
from threading import Thread
from PyQt5.QtGui import QImage
from multiprocessing import Process, current_process, Queue, JoinableQueue, Pipe
from PyQt5.QtCore import QThread, pyqtSignal


class processQueue(Process):
    # method: FILL_VALUE, IGNORE, DELETE,FILL_MEAN, FILL_CLASS_MEAN, FILL_MEDIAN, FILL_BAYESIAN
    def __init__(self):
        super(processQueue, self).__init__()
        # local data
        self.dataType = None
        self.trainSet = None
        self.testSet = None
        self.trainSetOnly = True
        self.target = None
        self.features = None
        self.processQ = list()  # (id, func, param)
        self.processInfo = dict()  # (processQ id: process Name, process describe)
        self.numericFeatures = None
        self.categoricalFeatures = None
        self.saveData = None
        self.count = 0
        # comm data
        self.monitor = None
        self.sendQueue = None
        self.receiveQueue = None
        self.currentProcessIndex = 0
        # process info
        self.PID = None
        self.parentPID = None

    def setSignalQueue(self, sendQueue: Queue, receiveQueue: Queue):
        self.sendQueue = sendQueue
        self.receiveQueue = receiveQueue

    def setData(self, dataType, trainSet, testSet=None):
        self.dataType = dataType
        self.trainSet = trainSet
        self.testSet = testSet
        self.trainSetOnly = True if testSet is None else False
        self.features = self.trainSet.columns.tolist()
        self.setDataInfo()

    def setTarget(self, target):
        self.target = target

    def setTestSet(self, testSet: pd.DataFrame):
        self.testSet = testSet

    def setFeatures(self, features):
        self.features = features

    def setSaveData(self, value):
        self.saveData = value

    # manage func
    def clean(self):
        self.dataType = None
        if self.trainSet is not None:
            del self.trainSet
            gc.collect()
            self.trainSet = None
        if self.testSet is not None:
            del self.testSet
            gc.collect()
            self.testSet = None
        self.target = None
        self.features = None
        self.processQ = dict()
        self.numericFeatures = None
        self.categoricalFeatures = None
        self.saveData = None
        self.PID = None
        self.parentPID = None
        gc.collect()

    def setDataInfo(self):
        # csv: set numeric/categorical feature
        # image: set image size, image count
        if self.trainSet is not None:
            if self.dataType in ['csv', 'pkl']:
                if self.features:
                    self.numericFeatures = [f for f in self.features
                                            and self.trainSet.columns[self.trainSet.dtypes != 'object']]
                    self.categoricalFeatures = [f for f in self.features
                                                and self.trainSet.columns[self.trainSet.dtypes == 'object']]
                else:
                    if self.target is None:
                        # raise Exception('target not set')
                        self.features = self.trainSet.columns.tolist()
                    else:
                        self.features = self.trainSet.columns.difference(list(self.target)).tolist()
                    self.numericFeatures = list(self.trainSet.columns[self.trainSet.dtypes != 'object'])
                    self.categoricalFeatures = list(self.trainSet.columns[self.trainSet.dtypes == 'object'])

            elif self.dataType in ['png']:
                self.trainSet = ImageData(self.trainSet)
                self.testSet = ImageData(self.testSet)
        else:
            raise Exception('Data not loaded')

    def addProcess(self, processFunc, param=None):
        index = self.count
        self.processQ.append((index, processFunc, param))
        self.count += 1
        return index

    def addDescribe(self, index, processName, describe):
        self.processInfo[index] = (processName, describe)

    def delProcess(self, index):
        self.processQ.pop(index)

    def setNumericFeature(self, features):
        self.numericFeatures = features

    def setCategoricalFeature(self, features):
        self.categoricalFeatures = features

    def moveProcess(self, curIndex, targetIndex):
        self.processQ.insert(targetIndex, self.processQ.pop(curIndex))

    def run(self):
        self.monitor = MyReceiver(self.receiveQueue, self)
        self.monitor.setDaemon(True)
        self.monitor.start()
        self.doProcess()

    def doProcess(self):
        self.getProcessInfo()
        #self.sendQueue.put((self, self.pid))
        for processQueueID, func, param in self.processQ:
            self.currentProcessIndex = processQueueID
            self.sendQueue.put('RUN:' + str(self.currentProcessIndex))
            print('run:', func)
            print('current pid:', self.pid)
            func(**param)
            print('FIN')
            self.sendQueue.put('FINISHED:' + str(self.currentProcessIndex))

    # data process func
    def fillNA(self, applyFeatures, applyRows, method, value):
        try:
            targetList = [self.trainSet] if self.trainSetOnly else [self.trainSet, self.testSet]
            for d in targetList:
                if method == 'FILL_VALUE':
                    d.loc[applyRows, applyFeatures].fillna(value=value, inplace=True)
        except Exception as e:
            return e
        else:
            return 0

    def dataTransform(self, applyFeatures, applyRows, method):
        targetList = [self.trainSet] if self.trainSetOnly else [self.trainSet, self.testSet]
        for d in targetList:
            if method == 'RECIPROCAL':
                d.loc[applyRows, applyFeatures] = d.loc[applyRows, applyFeatures].apply(lambda x: 1 / (x + 1))
            elif method == 'LOG_10':
                d.loc[applyRows, applyFeatures] = d.loc[applyRows, applyFeatures].apply(lambda x: np.log10(x))
            elif method == 'LOG_2':
                d.loc[applyRows, applyFeatures] = d.loc[applyRows, applyFeatures].apply(lambda x: np.log2(x))
            elif method == 'LOG_E':
                d.loc[applyRows, applyFeatures] = d.loc[applyRows, applyFeatures].apply(lambda x: np.log(x))
            elif method == 'SQUARE_ROOT':
                d.loc[applyRows, applyFeatures] = d.loc[applyRows, applyFeatures].apply(lambda x: np.sqrt(x))
            elif method == 'CUBE_ROOT':
                d.loc[applyRows, applyFeatures] = d.loc[applyRows, applyFeatures].apply(lambda x: np.cbrt(x))

    def sleep(self, seconds):
        time.sleep(seconds)

    # image process func
    def resizeImage(self, size):
        pass

    # image augment func

    # comm func
    def curProcess(self):
        pass

    def monitorThread(self):
        pass

    # process manage
    def getProcessInfo(self):
        self.PID = os.getpid()
        self.parentPID = os.getppid()


class MyReceiver(Thread):
    def __init__(self, queue: Queue, target):
        super(MyReceiver, self).__init__()
        self.queue = queue
        self.target = target

    def run(self):
        print('MyReceiver start')
        while self.target.is_alive():
            while not self.queue.empty():
                text = self.queue.get()
                print(text)
        print('MyReceiver end')


class QtReceiver(QThread):
    mysignal = pyqtSignal(str)
    def __init__(self, queue, target):
        super(QtReceiver, self).__init__()
        self.queue = queue
        self.target = target
        self.targetAlive = False

    def run(self):
        while True and not self.targetAlive:
            if self.target.is_alive():
                self.targetAlive = True

        while self.target.is_alive():  #self.target.is_alive()
            while not self.queue.empty():
                text = self.queue.get()
                #self.mysignal.emit(text)
                print(text)
        print('process end')


class ImageData:
    def __init__(self, imageDir):
        self.imageDir = imageDir
        self.imageList = None
        self.imageCount = None
        self.empty = False

    def loadImage(self):
        self.imageList = os.listdir(self.imageDir)
        if len(self.imageDir):
            self.imageCount = len(self.imageDir)
        else:
            self.imageCount = 0
            self.empty = True

    def getSize(self, imageName):
        if imageName in self.imageList:
            image = QImage(imageName)
            return image.size()


if __name__ == '__main__':
    sendQ = Queue(5)
    recvQ = Queue(5)
    p = processQueue(sendQ, recvQ)
    t = QtReceiver(sendQ, p)
    train = pd.read_csv('E:\\project\\MLTest\\data\\train.csv')
    test = pd.read_csv('E:\\project\\MLTest\\data\\test.csv')
    p.setData('csv', train, test)
    p.setTarget('SalePrice')
    p.setDataInfo()

    t.start()
    p.start()
    recvQ.put('process commd 1')
