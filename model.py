'''
create model file *.md
create model based on model type
'''

import os
import sys
import json
import pandas as pd
from PyQt5.QtWidgets import QWidget, QDialog, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, \
    QApplication, QDockWidget, QLabel, QAction, QToolButton, QScrollArea, QScrollBar, QTabWidget, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QIcon
from project import ml_project
from SwitchButton import switchButton


class ml_model:
    def __init__(self, modelType, modelName, modelLocation):
        self.modelType = modelType
        self.modelName = modelName
        self.modelLocation = modelLocation
        self.modelPlatform = 'CPU'
        self.modelLastRunTime = 0
        self.localScore = 0
        self.LBScore = 0
        self.kFold = 5
        self.metric = 'rmse'
        self.currentLoadData = 'N/A'
        self.modelFile = os.path.join(self.modelLocation, self.modelName)
        self.param = self.initParam(modelType)
        self.modelLogs = list()
        self.modelResults = list()
        self.trainSet = None
        self.testSet = None

    @classmethod
    def initModel(cls, modelType, modelName, modelLocation):
        if not os.path.isdir(modelLocation):
            raise Exception(modelLocation, 'is not a dir')
        newModel = ml_model(modelType, modelName, modelLocation)
        return newModel

    @classmethod
    def loadModel(cls, modelFile):
        with open(modelFile, 'r') as f:
            modelDict = json.load(f)
            newModel = ml_model(modelDict['modelType'], modelDict['modelName'], modelDict['modelLocation'])
            newModel.param = modelDict['param']
            newModel.modelLogs = modelDict['modelLogs']
            newModel.modelResults = modelDict['modelResults']
            newModel.modelPlatform = modelDict['modelPlatform']
            newModel.modelLastRunTime = modelDict['modelLastRunTime']
            newModel.localScore = modelDict['localScore']
            newModel.LBScore = modelDict['LBScore']
            newModel.metric = modelDict['metric']
            newModel.currentLoadData = modelDict['currentLoadData']
            return newModel

    def dumpModel(self, modelFile=None):
        modelDict = dict()
        modelDict['modelType'] = self.modelType
        modelDict['modelName'] = self.modelName
        modelDict['modelLocation'] = self.modelLocation
        modelDict['param'] = self.param
        modelDict['modelLogs'] = self.modelLogs
        modelDict['modelResults'] = self.modelResults
        modelDict['modelPlatform'] = self.modelPlatform
        modelDict['modelLastRunTime'] = self.modelLastRunTime
        modelDict['localScore'] = self.localScore
        modelDict['LBScore'] = self.LBScore
        modelDict['metric'] = self.metric
        modelDict['currentLoadData'] = self.currentLoadData
        if modelFile:
            self.modelFile = os.path.join(self.modelLocation, modelFile)
        with open(self.modelFile, 'w') as f:
            json.dump(modelDict, f)

    def update(self):
        self.dumpModel(self.modelFile)

    def initParam(self, modelType):
        param = {}
        if modelType == 'XGB':
            # General Parameters
            param['booster'] = 'gbtree'
            param['objective'] = 'reg:linear'
            param['silent'] = 0
            param['nthread'] = 1
            # Parameters for Tree Booster
            param['eta'] = 0.3
            param['gamma'] = 0
            param['max_depth'] = 6
            param['min_child_weight'] = 1
            param['max_delta_step'] = 0
            param['subsample'] = 1
            param['colsample_bytree'] = 1
            param['colsample_bylevel'] = 1
            param['reg_lambda'] = 1
            param['reg_alpha'] = 0
            param['tree_method'] = 'auto'
            param['scale_pos_weight'] = 1
            param['max_leaves'] = 0
            param['max_bin'] = 256
            param['predictor'] = 'cpu_predictor'
            param['eval_metric'] = 'rmse'
        elif modelType == 'LGBM':
            param['eta'] = 0
        elif modelType == 'LINEAR':
            param['eta'] = 0
        return param

    def setKFold(self, kFold):
        self.kFold = kFold
        self.update()

    def setMetric(self, metric):
        self.metric = metric
        self.update()

    def setModelType(self, type):
        self.modelType = type
        self.update()

    def setTrainSet(self, trainSet):
        self.trainSet = trainSet
        self.update()

    def setTestSet(self, testSet):
        self.testSet = testSet
        self.update()


class xgbModel:
    def __init__(self, param, train, test=None, kFold=5, metric='rmse'):
        self.train = train
        self.test = test
        self.kFold = kFold
        self.metric = metric
        self.param = param

    def fit(self):
        pass

    def predict(self):
        pass

    def predictProb(self):
        pass

    def setParam(self):
        pass
