import os
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QListWidget, QToolBox, \
    QTabWidget, QTextEdit, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QSpinBox, \
    QDoubleSpinBox, QFrame, QSizePolicy, QHeaderView, QTableView, QApplication, QScrollArea, QScrollBar, QSplitter, \
    QSplitterHandle, QComboBox, QGroupBox, QFormLayout, QCheckBox, QMenu, QAction, QWidgetAction, QStackedWidget, \
    QHeaderView,QRadioButton,QButtonGroup
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, QSettings, QTimer, QUrl, QDir, \
    QAbstractTableModel, QEvent, QObject, QModelIndex, QVariant, QThread, QObject, QMimeData
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath, QStandardItemModel, QTextCursor, \
    QCursor, QDrag, QStandardItem
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from customWidget import CollapsibleTabWidget, ImageViewer, DragTableView, customProcessModel
from customLayout import FlowLayout

from SwitchButton import switchButton
import pandas as pd
import numpy as np
import subprocess
import logging
import threading
import gc
import time
import datetime
from multiprocessing import Queue

from model import xgbModel

import seaborn as sns
from process import processQueue

logfileformat = '[%(levelname)s] (%(threadName)-10s) %(message)s'
logging.basicConfig(level=logging.DEBUG, format=logfileformat)


def log(message):
    logging.debug(message)


def process_thread_pipe(process):
    while process.poll() is None:  # while process is still alive
        log(str(process.stderr.readline()))


class initPQDialog(QDialog):
    def __init__(self, processQ:processQueue, parent=None):
        super(initPQDialog, self).__init__(parent=parent)
        self.processQ = processQ
        self.dataType = None
        self.trainSet = None
        self.testSet = None
        self.if_inited = False
        # widgets
        self.mainLayout = QVBoxLayout(self)
        self.downLayout = QHBoxLayout(self)
        self.leftLayout = QVBoxLayout(self)
        self.rightLayout = QVBoxLayout(self)
        # titleLabel
        self.titleLabel = QLabel('init process', self)

        self.initUI()

    def initUI(self):
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.mainLayout.addLayout(self.downLayout, 10)
        self.downLayout.addLayout(self.leftLayout,1)
        self.downLayout.addLayout(self.rightLayout,3)
        # titleLabel
        self.titleLabel.setFont(QFont('Arial', 15, QFont.Times))
        self.titleLabel.setStyleSheet('QLabel {background-color : #A9A9A9; color: #FFFFFF}')
        self.titleLabel.setFixedHeight(40)
        self.titleLabel.setContentsMargins(30, 0, 0, 0)


class fillNADialog(QDialog):
    def __init__(self, PQ: processQueue, parent=None):
        super(fillNADialog, self).__init__(parent=parent)
        # local data
        self.processQ = PQ
        self.value = None
        self.applyAllFeatures = True
        self.applyFeatures = None
        self.applyAllRows = True
        self.applyRows = None
        # widgets
        self.mainLayout = QVBoxLayout(self)
        self.downLayout = QHBoxLayout(self)
        self.leftLayout = QVBoxLayout(self)
        self.rightLayout = QVBoxLayout(self)

        self.titleLabel = QLabel('Fill NA', self)
        # features
        self.featureGroup = QGroupBox('Features',self)
        self.featureButtonGroup = QButtonGroup(self)
        self.checkAllFeatures = QRadioButton(self)
        self.checkNumericFeatures = QRadioButton(self)
        self.checkCategoricalFeatures = QRadioButton(self)
        self.checkCustomFeatures = QRadioButton(self)
        # rows
        self.rowGroup = QGroupBox('Rows',self)
        self.rowButtonGroup = QButtonGroup(self)
        self.checkAllRows = QRadioButton(self)
        self.checkCustomRows = QRadioButton(self)
        self.featureList = QTextEdit(self)
        self.rowList = QTextEdit(self)
        self.initUI()

    def initUI(self):
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.mainLayout.addLayout(self.downLayout, 10)
        self.downLayout.addLayout(self.leftLayout,1)
        self.downLayout.addLayout(self.rightLayout,3)
        # titleLabel
        self.titleLabel.setFont(QFont('Arial', 15, QFont.Times))
        self.titleLabel.setStyleSheet('QLabel {background-color : #A9A9A9; color: #FFFFFF}')
        self.titleLabel.setFixedHeight(40)
        self.titleLabel.setContentsMargins(30, 0, 0, 0)

        # feature
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.checkAllFeatures)
        vbox.addWidget(self.checkNumericFeatures)
        vbox.addWidget(self.checkCategoricalFeatures)
        vbox.addWidget(self.checkCustomFeatures)
        vbox.addWidget(self.featureList)
        self.featureList.setEnabled(False)
        self.featureGroup.setLayout(vbox)
        self.featureButtonGroup.addButton(self.checkAllFeatures)
        self.featureButtonGroup.addButton(self.checkNumericFeatures)
        self.featureButtonGroup.addButton(self.checkCategoricalFeatures)
        self.featureButtonGroup.addButton(self.checkCustomFeatures)
        # checkAllFeatures
        self.checkAllFeatures.setText('Fill All Features')
        self.checkAllFeatures.setFixedHeight(20)
        self.checkAllFeatures.setFont(QFont('Arial', 10, QFont.Times))
        self.checkAllFeatures.toggled.connect(self.setFeatures)
        self.checkAllFeatures.setChecked(True)
        # checkNumericFeatures
        self.checkNumericFeatures.setText('Fill All Numeric Features')
        self.checkNumericFeatures.setFixedHeight(20)
        self.checkNumericFeatures.setFont(QFont('Arial', 10, QFont.Times))
        # checkCategoricalFeatures
        self.checkCategoricalFeatures.setText('Fill All Numeric Features')
        self.checkCategoricalFeatures.setFixedHeight(20)
        self.checkCategoricalFeatures.setFont(QFont('Arial', 10, QFont.Times))
        # checkCustomFeatures
        self.checkCustomFeatures.setText('Fill Custom Features')
        self.checkCustomFeatures.setFixedHeight(20)
        self.checkCustomFeatures.setFont(QFont('Arial', 10, QFont.Times))
        self.checkCustomFeatures.toggled.connect(self.featureList.setEnabled)
        # row
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.checkAllRows)
        vbox.addWidget(self.checkCustomRows)
        vbox.addWidget(self.rowList)
        self.rowList.setEnabled(False)
        self.rowGroup.setLayout(vbox)
        self.rowButtonGroup.addButton(self.checkAllRows)
        self.rowButtonGroup.addButton(self.checkCustomRows)
        self.checkAllRows.setChecked(True)
        # checkAllRows
        self.checkAllRows.setText('Fill All Rows')
        self.checkAllRows.setFixedHeight(20)
        self.checkAllRows.setFont(QFont('Arial', 10, QFont.Times))
        # checkCustomRows
        self.checkCustomRows.setText('Fill All Rows')
        self.checkCustomRows.setFixedHeight(20)
        self.checkCustomRows.setFont(QFont('Arial', 10, QFont.Times))
        self.checkCustomRows.toggled.connect(self.rowList.setEnabled)
        # row list
        self.leftLayout.addWidget(self.featureGroup, alignment=Qt.AlignTop)
        self.leftLayout.addWidget(self.rowGroup, alignment=Qt.AlignTop)
        self.leftLayout.addStretch(1)

    def setFeatures(self):
        if self.checkAllFeatures.isChecked():
            self.featureList.clear()
            for f in self.processQ.features:
                self.featureList.append(f)

    def addProcess(self):
        index = self.processQ.addProcess(None, param=dict())
        self.processQ.addDescribe(index,'fillNA', 'fill NA')


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QGridLayout(self)
        self.setFixedSize(800, 500)
        self.setLayout(self.mainLayout)
        self.item = initPQDialog(self)
        self.mainLayout.addWidget(self.item)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
