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
from customWidget import ModelWidget, DataWidget, ProjectWidget, ScriptWidget, CollapsibleTabWidget
from customLayout import FlowLayout
from SwitchButton import switchButton


# widget for tab
class CreateModel(QWidget):
    def __init__(self, MLModel, parent=None):
        super(CreateModel, self).__init__(parent=parent)
        self.outLayout = QVBoxLayout(self)
        self.insideLayout = QVBoxLayout(self)
        self.insideWidget = QWidget(self)
        self.scrollArea = QScrollArea(self)
        self.modelFrame = QFrame(self)
        self.displayWidget = QWidget(self)
        self.tabWidget = CollapsibleTabWidget(self)
        self.MLModel = MLModel
        self.initUI()

    def initUI(self):
        self.insideLayout.addWidget(self.modelFrame)
        self.insideLayout.addWidget(self.displayWidget)
        self.insideWidget.setLayout(self.insideLayout)
        self.scrollArea.setWidgetResizable(True)
        scrollbar = QScrollBar(self)
        self.scrollArea.setWidget(self.insideWidget)
        self.scrollArea.setVerticalScrollBar(scrollbar)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.outLayout.addWidget(self.scrollArea)
        self.outLayout.addWidget(self.tabWidget)


class ml_model:
    def __init__(self, modelType, modelName, modelLocation):
        self.modelType = modelType
        self.modelName = modelName
        self.modelLocation = modelLocation
        self.modelFile = os.path.join(self.modelLocation, self.modelName + '.md')
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
            newModel = ml_project(modelDict['modelType', 'modelName', 'modelLocation'])
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


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QVBoxLayout(self)
        self.setFixedSize(800, 500)
        self.setLayout(self.mainLayout)
        self.item = CreateModel(self)
        self.item.tabWidget.addTab('test', QLabel('sdf'))
        self.mainLayout.addWidget(self.item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = testDialog()
    test.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
