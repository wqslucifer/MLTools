import os
import sys
import json
import time
import subprocess
import signal
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QIcon
from customWidget import ModelWidget, DataWidget, ProjectWidget, ScriptWidget, CollapsibleTabWidget, ResultWidget, \
    HistoryWidget, ImageDataWidget, QTreeWidgetItem
from customLayout import FlowLayout
from tabWidget import DataTabWidget, IpythonTabWidget, process_thread_pipe, IpythonWebView, log, ModelTabWidget, \
    ImageDataTabWidget, queueTabWidget, scriptTabWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtQuick import QQuickView
from PyQt5.QtCore import QUrl, QEvent

from SwitchButton import switchButton
from model import ml_model
from project import ml_project
from multiprocessing import Queue
from management import manageProcess
import GENERAL

GENERAL.init()


class createModelDialog(QDialog):
    def __init__(self, MLProject: ml_project, parent=None):
        super(createModelDialog, self).__init__(parent=parent)
        self.setWindowIcon(QIcon('MLTool.ico'))
        self.mainLayout = QHBoxLayout(self)
        self.rightLayout = QVBoxLayout(self)
        self.stackedLayout = QStackedLayout(self)
        self.bottomLayout = QHBoxLayout(self)
        self.nextButton = QPushButton('next', self)
        self.guide = guideWidget(self)
        self.initUI()

    def initUI(self):
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainLayout.addWidget(self.guide)
        self.mainLayout.addLayout(self.rightLayout)
        self.bottomLayout.addSpacing(10)
        self.bottomLayout.addWidget(self.nextButton)
        self.bottomLayout.setAlignment(Qt.AlignRight)
        self.rightLayout.addLayout(self.stackedLayout)
        self.rightLayout.addLayout(self.bottomLayout)
        self.mainLayout.setStretch(0, 1)
        self.mainLayout.setStretch(1, 1)

        self.setStyleSheet('background-color:#eaeae1;')

        self.guide.addLabel('Intro')
        self.guide.addLabel('Model Type')
        self.guide.addLabel('Load Data')
        self.guide.addLabel('Data Process')
        self.guide.addLabel('Model Param Setting')
        self.guide.addLabel('Finish')
        self.guide.setLabelColor(0)

class guideWidget(QWidget):
    def __init__(self, parent=None):
        super(guideWidget, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.labelList = []
        self.font = QFont("Arial", 10, QFont.Bold)
        self.setFixedWidth(100)
        self.setMinimumHeight(400)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.mainLayout.addSpacing(50)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setSpacing(10)

    def addLabel(self, labelName):
        label = QLabel(self)
        label.setText(labelName)
        label.setFont(self.font)
        label.setStyleSheet("color:#8c8c8c;")
        self.labelList.append(label)
        self.mainLayout.addWidget(label)

    def setLabelColor(self, index):
        self.labelList[index].setStyleSheet("color:#000000;")


class createModel_1(QWidget):
    def __init__(self, parent):
        super(createModel_1, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
