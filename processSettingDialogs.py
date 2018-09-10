import os
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QListWidget, QToolBox, \
    QTabWidget, QTextEdit, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QSpinBox, \
    QDoubleSpinBox, QFrame, QSizePolicy, QHeaderView, QTableView, QApplication, QScrollArea, QScrollBar, QSplitter, \
    QSplitterHandle, QComboBox, QGroupBox, QFormLayout, QCheckBox, QMenu, QAction, QWidgetAction, QStackedWidget, \
    QHeaderView, QRadioButton, QButtonGroup, QMessageBox
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
        self.param = dict()
        self.method = None
        self.value = None
        # widgets
        self.mainLayout = QVBoxLayout(self)
        self.downLayout = QHBoxLayout(self)
        self.leftLayout = QVBoxLayout(self)
        self.rightLayout = QVBoxLayout(self)

        self.titleLabel = QLabel('Fill NA', self)
        # features
        self.featureGroup = QGroupBox('Features', self)
        self.featureButtonGroup = QButtonGroup(self)
        self.checkAllFeatures = QRadioButton(self)
        self.checkNumericFeatures = QRadioButton(self)
        self.checkCategoricalFeatures = QRadioButton(self)
        self.checkCustomFeatures = QRadioButton(self)
        self.featureMethod = None
        self.featureList = QTextEdit(self)
        # rows
        self.rowGroup = QGroupBox('Rows', self)
        self.rowButtonGroup = QButtonGroup(self)
        self.checkAllRows = QRadioButton(self)
        self.checkCustomRows = QRadioButton(self)
        self.rowList = QTextEdit(self)
        # filling method
        # FILL_VALUE, IGNORE, DELETE,FILL_MEAN, FILL_CLASS_MEAN, FILL_MEDIAN, FILL_BAYESIAN
        self.methodGroup = QGroupBox('Filling Method', self)
        self.fillValueEditor = QLineEdit(self)
        self.methodButtonGroup = QButtonGroup(self)
        self.method_FILL_VALUE = QRadioButton(self)
        self.method_FILL_MEAN = QRadioButton(self)
        self.method_FILL_CLASS_MEAN = QRadioButton(self)
        self.method_FILL_MEDIAN = QRadioButton(self)
        self.method_FILL_BAYESIAN = QRadioButton(self)
        self.method_IGNORE = QRadioButton(self)
        self.method_DELETE = QRadioButton(self)
        # confirm
        self.addToQueueButton = QPushButton('Add To Queue', self)
        self.initUI()

    def initUI(self):
        self.setFixedSize(800, 600)

        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.mainLayout.addLayout(self.downLayout, 10)
        self.downLayout.addLayout(self.leftLayout, 1)
        self.downLayout.addLayout(self.rightLayout, 3)
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
        self.checkCategoricalFeatures.setText('Fill All Categorical Features')
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
        for checkRow_ in [self.checkAllRows, self.checkCustomRows]:
            checkRow_.setFixedHeight(20)
            checkRow_.setFont(QFont('Arial', 10, QFont.Times))
        # checkAllRows
        self.checkAllRows.setText('Fill All Rows')
        self.checkAllRows.toggled.connect(self.setApplyAllRows)
        # checkCustomRows
        self.checkCustomRows.setText('Fill custom Rows')
        self.checkCustomRows.toggled.connect(self.rowList.setEnabled)
        # row list
        self.leftLayout.addWidget(self.featureGroup, alignment=Qt.AlignTop)
        self.leftLayout.addWidget(self.rowGroup, alignment=Qt.AlignTop)
        self.leftLayout.addStretch(1)
        # method
        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout(self)
        hbox.addWidget(self.method_FILL_VALUE)
        hbox.addWidget(self.fillValueEditor)
        self.fillValueEditor.setEnabled(False)
        vbox.addLayout(hbox)
        vbox.addWidget(self.method_FILL_MEAN)
        vbox.addWidget(self.method_FILL_CLASS_MEAN)
        vbox.addWidget(self.method_FILL_MEDIAN)
        vbox.addWidget(self.method_FILL_BAYESIAN)
        vbox.addWidget(self.method_IGNORE)
        vbox.addWidget(self.method_DELETE)
        self.methodGroup.setLayout(vbox)
        self.methodButtonGroup.addButton(self.method_FILL_VALUE)
        self.methodButtonGroup.addButton(self.method_FILL_MEAN)
        self.methodButtonGroup.addButton(self.method_FILL_CLASS_MEAN)
        self.methodButtonGroup.addButton(self.method_FILL_MEDIAN)
        self.methodButtonGroup.addButton(self.method_FILL_BAYESIAN)
        self.methodButtonGroup.addButton(self.method_IGNORE)
        self.methodButtonGroup.addButton(self.method_DELETE)
        # method_FILL_VALUE
        for method_ in [self.method_FILL_VALUE, self.method_FILL_MEAN, self.method_FILL_CLASS_MEAN,
                        self.method_FILL_MEDIAN, self.method_FILL_BAYESIAN, self.method_IGNORE, self.method_DELETE]:
            method_.setFixedHeight(20)
            method_.setFont(QFont('Arial', 10, QFont.Times))
        # method_FILL_VALUE
        self.method_FILL_VALUE.setText('Fill NA with value')
        self.method_FILL_VALUE.toggled.connect(self.fillValueEditor.setEnabled)
        self.method_FILL_VALUE.toggled.connect(lambda: self.setMethod('FILL_VALUE'))
        # method_FILL_MEAN
        self.method_FILL_MEAN.setText('Fill NA with mean')
        self.method_FILL_MEAN.toggled.connect(lambda: self.setMethod('FILL_MEAN'))
        # method_FILL_CLASS_MEAN
        self.method_FILL_CLASS_MEAN.setText('Fill NA with mean of same class')
        self.method_FILL_CLASS_MEAN.toggled.connect(lambda: self.setMethod('FILL_CLASS_MEAN'))
        # method_FILL_MEDIAN
        self.method_FILL_MEDIAN.setText('Fill NA with median')
        self.method_FILL_MEDIAN.toggled.connect(lambda: self.setMethod('FILL_MEDIAN'))
        # method_FILL_BAYESIAN
        self.method_FILL_BAYESIAN.setText('Fill NA with Bayesian method')
        self.method_FILL_BAYESIAN.toggled.connect(lambda: self.setMethod('FILL_BAYESIAN'))
        # method_IGNORE
        self.method_IGNORE.setText('Ignore NA rows')
        self.method_IGNORE.toggled.connect(lambda: self.setMethod('IGNORE'))
        # method_DELETE
        self.method_DELETE.setText('Delete NA rows(Apply to whole dataframe)')
        self.method_DELETE.toggled.connect(lambda: self.setMethod('DELETE'))

        # add to queue button
        self.addToQueueButton.setFixedSize(100, 35)
        self.addToQueueButton.clicked.connect(self.addToQueue)
        buttonLayout = QHBoxLayout(self)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.addToQueueButton)
        # right layout
        self.rightLayout.addWidget(self.methodGroup)
        self.rightLayout.addStretch(1)
        self.rightLayout.addLayout(buttonLayout)

    def addToQueue(self):
        if self.method:
            if not (self.method == 'FILL_VALUE' and self.value):
                QMessageBox.warning(self, 'warning', 'Please set a filling value', QMessageBox.Ok)
                return
            self.prepareData()
            self.accept()
        else:
            QMessageBox.warning(self, 'warning', 'Please select a filling method', QMessageBox.Ok)

    def setApplyAllRows(self, value):
        self.applyAllRows = value

    def setFeatures(self):
        self.featureList.clear()
        if self.checkAllFeatures.isChecked():
            self.applyAllFeatures = True
            self.featureMethod = 'ALL Features'
            for f in self.processQ.features:
                self.featureList.append(f)
        else:
            self.applyAllFeatures = False
        if self.checkNumericFeatures.isChecked():
            self.featureMethod = 'Numeric Features'
            for f in self.processQ.numericFeatures:
                self.featureList.append(f)
        if self.checkCategoricalFeatures.isChecked():
            self.featureMethod = 'Categorical Features'
            for f in self.processQ.categoricalFeatures:
                self.featureList.append(f)

    def setMethod(self, value):
        self.method = value

    def prepareData(self):
        if self.checkAllFeatures.isChecked():
            self.applyFeatures = self.processQ.features
        elif self.checkNumericFeatures.isChecked():
            self.applyFeatures = self.processQ.numericFeatures
        elif self.checkCategoricalFeatures.isChecked():
            self.applyFeatures = self.processQ.categoricalFeatures
        else:
            s = self.featureList.toPlainText()
            self.applyFeatures = [i.strip('\'') for i in s.split(',')]

        if not self.checkAllRows:
            s = self.rowList.toPlainText()
            self.applyRows = [int(i) for i in s.split(',')]
        else:
            self.applyRows = self.processQ.trainSet.index.tolist()

        if self.method_FILL_VALUE.isChecked():
            tmp = self.fillValueEditor.text()
            try:
                self.value = float(tmp)
            except ValueError:
                self.value = tmp

        self.param['applyFeatures'] = self.applyFeatures
        self.param['applyRows'] = self.applyRows
        self.param['method'] = self.method
        self.param['value'] = self.value

    def addProcess(self):
        describe = {
            'FILL_VALUE': 'Fill ' + self.featureMethod + ' NA with value (' + str(self.value) + ')',
            'FILL_MEAN': 'Fill ' + self.featureMethod + ' NA with mean of column',
            'FILL_CLASS_MEAN': 'Fill ' + self.featureMethod + ' NA with mean of column while belong to same class',
            'FILL_MEDIAN': 'Fill ' + self.featureMethod + ' NA with median of column',
            'FILL_BAYESIAN': 'Fill ' + self.featureMethod + ' NA with Bayesian method',
            'IGNORE': 'Ignore ' + self.featureMethod + ' NA, Do Nothing',
            'DELETE': 'Delete ' + self.featureMethod + ' rows with NA'
        }
        # index = self.processQ.addProcess(self.processQ.fillNA, param=self.param)
        # self.processQ.addDescribe(index, 'fillNA', describe[self.method])
        return self.processQ.fillNA, self.param, 'fillNA', describe[self.method]


class logTransformDialog(QDialog):
    def __init__(self, PQ: processQueue, parent=None):
        super(logTransformDialog, self).__init__(parent=parent)
        # local data
        self.processQ = PQ
        self.applyAllFeatures = True
        self.applyFeatures = None
        self.param = dict()
        self.method = None
        self.loadSkewed = False
        self.SkewedFeatures = None
        # widgets
        self.mainLayout = QVBoxLayout(self)
        self.downLayout = QHBoxLayout(self)
        self.leftLayout = QVBoxLayout(self)
        self.rightLayout = QVBoxLayout(self)

        self.titleLabel = QLabel('Log Transformation', self)
        # features
        self.featureList = QTextEdit(self)
        self.featureGroup = QGroupBox('Features', self)
        self.featureButtonGroup = QButtonGroup(self)
        self.checkAllFeatures = QRadioButton(self)
        self.checkNumericFeatures = QRadioButton(self)
        self.checkCategoricalFeatures = QRadioButton(self)
        self.checkCustomFeatures = QRadioButton(self)
        self.featureMethod = None
        self.loadSkewedFeatures = QPushButton('load Skewed Feature', self)

        # confirm
        self.addToQueueButton = QPushButton('Add To Queue', self)
        self.initUI()

    def initUI(self):
        self.setFixedSize(800, 600)
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.mainLayout.addLayout(self.downLayout, 10)
        self.downLayout.addLayout(self.leftLayout, 1)
        self.downLayout.addLayout(self.rightLayout, 3)
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
        vbox.addWidget(self.loadSkewedFeatures)
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
        #self.checkAllFeatures.toggled.connect(self.setFeatures)
        self.checkAllFeatures.setChecked(True)
        # checkNumericFeatures
        self.checkNumericFeatures.setText('Fill All Numeric Features')
        self.checkNumericFeatures.setFixedHeight(20)
        self.checkNumericFeatures.setFont(QFont('Arial', 10, QFont.Times))
        # checkCategoricalFeatures
        self.checkCategoricalFeatures.setText('Fill All Categorical Features')
        self.checkCategoricalFeatures.setFixedHeight(20)
        self.checkCategoricalFeatures.setFont(QFont('Arial', 10, QFont.Times))
        # checkCustomFeatures
        self.checkCustomFeatures.setText('Fill Custom Features')
        self.checkCustomFeatures.setFixedHeight(20)
        self.checkCustomFeatures.setFont(QFont('Arial', 10, QFont.Times))
        self.checkCustomFeatures.toggled.connect(self.featureList.setEnabled)
        self.checkCustomFeatures.toggled.connect(self.loadSkewedFeatures.setEnabled)
        self.loadSkewedFeatures.setEnabled(False)
        self.loadSkewedFeatures.clicked.connect(self.loadSkewedColumns)
        # leftLayout
        self.leftLayout.addWidget(self.featureGroup, alignment=Qt.AlignTop)
        self.leftLayout.addStretch(1)

        # add to queue button
        self.addToQueueButton.setFixedSize(100, 35)
        self.addToQueueButton.clicked.connect(self.addToQueue)
        buttonLayout = QHBoxLayout(self)
        buttonLayout.setContentsMargins(0,0,20,0)
        buttonLayout.addWidget(self.addToQueueButton,alignment=Qt.AlignRight)
        # right layout

        self.rightLayout.addLayout(buttonLayout,stretch=1)

    def setFeatures(self):
        self.featureList.clear()
        if self.checkAllFeatures.isChecked():
            self.applyAllFeatures = True
            self.featureMethod = 'ALL Features'
            for f in self.processQ.features:
                self.featureList.append(f)
        else:
            self.applyAllFeatures = False
        if self.checkNumericFeatures.isChecked():
            self.featureMethod = 'Numeric Features'
            for f in self.processQ.numericFeatures:
                self.featureList.append(f)
        if self.checkCategoricalFeatures.isChecked():
            self.featureMethod = 'Categorical Features'
            for f in self.processQ.categoricalFeatures:
                self.featureList.append(f)

    def prepareData(self):
        if self.checkAllFeatures.isChecked():
            self.applyFeatures = self.processQ.features
        elif self.checkNumericFeatures.isChecked():
            self.applyFeatures = self.processQ.numericFeatures
        elif self.checkCategoricalFeatures.isChecked():
            self.applyFeatures = self.processQ.categoricalFeatures
        else:
            if self.loadSkewed:
                self.applyFeatures = self.SkewedFeatures
            else:
                s = self.featureList.toPlainText()
                self.applyFeatures = [i.strip('\'') for i in s.split(',')]

        self.param['applyFeatures'] = self.applyFeatures

    def addToQueue(self):
        if self.method:
            self.prepareData()
            self.accept()
        QMessageBox.warning(self, 'warning', 'Please select a filling method', QMessageBox.Ok)

    def loadSkewedColumns(self):
        self.SkewedFeatures = []


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QGridLayout(self)
        self.setFixedSize(800, 500)
        self.setLayout(self.mainLayout)
        self.item = logTransformDialog(self)
        self.mainLayout.addWidget(self.item)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
