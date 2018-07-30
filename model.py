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
        self.modelFile = os.path.join(self.modelLocation, self.modelName)
        self.param = dict()
        self.modelLogs = list()
        self.modelResults = list()

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
            return newModel

    def dumpModel(self, modelFile=None):
        modelDict = dict()
        modelDict['modelType'] = self.modelType
        modelDict['modelName'] = self.modelName
        modelDict['modelLocation'] = self.modelLocation
        modelDict['param'] = self.param
        modelDict['modelLogs'] = self.modelLogs
        modelDict['modelResults'] = self.modelResults
        if modelFile:
            self.modelFile = os.path.join(self.modelLocation, modelFile + '.md')
        with open(self.modelFile, 'w') as f:
            json.dump(modelDict, f)
