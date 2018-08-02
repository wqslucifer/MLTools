'''
create model file *.md
create model based on model type
'''

import os
import gc
import sys
import json
import time
import pickle
import pandas as pd
from PyQt5.QtWidgets import QWidget, QDialog, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, \
    QApplication, QDockWidget, QLabel, QAction, QToolButton, QScrollArea, QScrollBar, QTabWidget, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QIcon
from project import ml_project
from SwitchButton import switchButton

from multiprocessing import Process, current_process, Queue, JoinableQueue
import xgboost as xgb
from sklearn.model_selection import KFold
from sklearn.metrics import *


class ml_model:
    modelUpdated = pyqtSignal()

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
        self.modelFile = os.path.join(self.modelLocation, self.modelName)
        self.modelPickle = self.modelFile + '.pkl'
        self.param = self.initParam(modelType)
        self.modelLogs = list()
        self.modelResults = list()
        self.trainSet = ''
        self.testSet = ''
        self.ID = ''
        self.target = ''
        self.model = None

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
            newModel.trainSet = modelDict['trainSet']
            newModel.testSet = modelDict['testSet']
            newModel.ID = modelDict['ID']
            newModel.target = modelDict['target']
            newModel.kFold = modelDict['kFold']
            newModel.modelPickle = modelDict['modelPickle']
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
        modelDict['trainSet'] = self.trainSet
        modelDict['testSet'] = self.testSet
        modelDict['ID'] = self.ID
        modelDict['target'] = self.target
        modelDict['kFold'] = self.kFold
        modelDict['modelPickle'] = self.modelPickle
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

    def setCurrentModel(self, model):
        with open(self.modelPickle, 'wb') as f:
            pickle.dump(model, f)
        self.update()

    def loadCurrentModel(self):
        with open(self.modelPickle, 'rb') as f:
            self.model = pickle.load(f)

    def setID(self, ID):
        self.ID = ID
        self.update()

    def setTarget(self, target):
        self.target = target
        self.update()


class xgbModel(Process):
    def __init__(self, queue, MLModel: ml_model, num_rounds=1000, kFold=5):
        super(xgbModel, self).__init__()
        self.X = None
        self.y = None
        self.test = None
        self.features = ['MSSubClass', 'LotFrontage']
        self.kFold = kFold
        self.param = MLModel.param
        self.num_rounds = num_rounds
        self.random_state = 0
        self.modelList = []
        self.cvPredict = None
        self.MLModel = MLModel
        self.ID = None
        self.target = None
        self.prepareData()
        self.queue = queue

    def prepareData(self):
        self.ID = self.MLModel.ID
        self.target = self.MLModel.target
        # load train set
        if self.MLModel.trainSet.endswith('csv'):
            self.X = pd.read_csv(self.MLModel.trainSet)
        elif self.MLModel.trainSet.endswith('pkl'):
            self.X = pd.read_pickle(self.MLModel.trainSet)
        # load test set
        if self.MLModel.testSet.endswith('csv'):
            self.test = pd.read_csv(self.MLModel.testSet)
        elif self.MLModel.testSet.endswith('pkl'):
            self.test = pd.read_pickle(self.MLModel.testSet)
        # set y
        self.y = self.X[self.target]
        # init cv prediction dataframe
        self.cvPredict = pd.DataFrame(index=self.X.index, columns=[self.ID, self.target])
        self.cvPredict[self.ID] = self.X[self.ID]

        self.X = self.X.loc[:, self.features].values
        self.y = self.y.values
        self.test = self.test.loc[:, self.features].values

    def train(self):
        sys.excepthook = sys._excepthook
        sys.stdout = EmitStream(textWritten=self.writeToQueue)
        #sys.stderr = EmitStream(textWritten=self.writeToQueue)

        kf = KFold(self.kFold, shuffle=True, random_state=self.random_state)
        for n_fold, (trainIndex, cvIndex) in enumerate(kf.split(self.X)):
            train_X, train_y = self.X[trainIndex], self.y[trainIndex]
            cv_X, cv_y = self.X[cvIndex], self.y[cvIndex]
            trainset = xgb.DMatrix(train_X, train_y)
            cv_train = xgb.DMatrix(cv_X)
            cvset = xgb.DMatrix(cv_X, cv_y)

            del train_X, train_y, cv_X, cv_y
            gc.collect()
            evallist = [(trainset, 'train'), (cvset, 'cv')]
            print('fitting')
            model = xgb.train(self.param, dtrain=trainset, num_boost_round=self.num_rounds, evals=evallist,
                              early_stopping_rounds=100)
            self.cvPredict.iloc[cvIndex, 1] = model.predict(cv_train)
            self.modelList.append(model)

        #sys.stdout = sys.__stdout__
        #sys.stderr = sys.__stderr__
        return self.getScore(self.y, self.cvPredict.iloc[:, 1])


    def getScore(self, y_true, y_pred):
        if self.MLModel.metric == 'rmse':
            r = mean_squared_error(y_true, y_pred)
        elif self.MLModel.metric == 'auc':
            r = roc_auc_score(y_true, y_pred)
        elif self.MLModel.metric == 'logloss':
            r = log_loss(y_true, y_pred)
        elif self.MLModel.metric == 'error':
            r = precision_score(y_true, y_pred)
        return r


    def predict(self):
        testPredict = pd.DataFrame(index=self.test.index, columns=[self.ID, self.target])
        testPredict[self.ID] = self.test[self.ID]
        testPredict[self.target] = [0 for _ in range(self.test.shape[0])]
        for model in self.modelList:
            testPredict.iloc[:, 1] += model.predict(xgb.DMatrix(self.test)) / self.kFold
        return testPredict


    def predictProb(self):
        testPredict = pd.DataFrame(index=self.test.index, columns=[self.ID, self.target])
        testPredict[self.ID] = self.test[self.ID]
        testPredict[self.target] = [0 for _ in range(self.test.shape[0])]
        for model in self.modelList:
            testPredict.iloc[:, 1] += model.predict_proba(xgb.DMatrix(self.test)) / self.kFold
        return testPredict


    def setParam(self):
        pass


    def run(self):
        print('Run child process (%s)' % os.getpid())
        self.train()

    def writeToQueue(self, text):
        self.queue.put(text)


class EmitStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass