import os
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QListWidget, QToolBox, \
    QTabWidget, QTextEdit, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QSpinBox, \
    QDoubleSpinBox, QFrame, QSizePolicy, QHeaderView, QTableView, QApplication, QScrollArea, QScrollBar, QSplitter, \
    QSplitterHandle, QComboBox, QGroupBox, QFormLayout, QCheckBox
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, QSettings, QTimer, QUrl, QDir, \
    QAbstractTableModel, QEvent, QObject, QModelIndex, QVariant
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath, QStandardItemModel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from customWidget import CollapsibleTabWidget

from SwitchButton import switchButton
import pandas as pd
import numpy as np
import subprocess
import logging
import threading
import gc
import datetime

from model import xgbModel

logfileformat = '[%(levelname)s] (%(threadName)-10s) %(message)s'
logging.basicConfig(level=logging.DEBUG, format=logfileformat)


def log(message):
    logging.debug(message)


def startnotebook(notebook_executable="jupyter-notebook", port=8888, directory=QDir.homePath()):
    return subprocess.Popen([notebook_executable,
                             "--port=%s" % port, "--browser=n", "-y",
                             "--notebook-dir=%s" % directory], bufsize=1,
                            stderr=subprocess.PIPE)


def process_thread_pipe(process):
    while process.poll() is None:  # while process is still alive
        log(str(process.stderr.readline()))


class DataTabWidget(QWidget):
    def __init__(self, filename):
        super(DataTabWidget, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        # local data
        self.filename = filename
        self.dataFrame = None
        self.verticalHeaderWidth = 70
        self.displayRows = 2
        self.displayCols = 7
        # init widgets
        self.mainLayout = QGridLayout(self)
        self.rightLayout = QVBoxLayout(self)
        self.toolset = QToolBox(self)
        self.tools_highLight = QWidget(self)
        self.tools_dataInfo = QWidget(self)
        self.tools_process = QWidget(self)
        self.tools_visualize = QWidget(self)

        self.dataWindow = QWidget(self)
        self.dataWindowLayout = QVBoxLayout(self)
        self.dataExplorer = QTableView(self)
        self.model = customTableModel(self)
        self.dataExplorer.setModel(self.model)
        self.statistic = QTableWidget(self)

        self.mainTab = QTabWidget(self)
        self.outputTab = QTabWidget(self)
        self.outputEdit = QTextEdit(self)
        # init UI
        self.initUI()
        self.initStatistic()

    def initUI(self):
        self.highLightSetting()
        self.initToolDataInfo()
        self.toolset.addItem(self.tools_highLight, 'Setting')
        self.toolset.addItem(self.tools_dataInfo, 'Data Info')
        self.toolset.addItem(self.tools_process, 'Data Process')
        self.toolset.addItem(self.tools_visualize, 'Data Visualize')
        # init data window
        self.initDataExplorer(self.filename)
        self.dataWindowLayout.addWidget(self.dataExplorer)
        self.dataWindowLayout.addWidget(self.statistic)
        self.dataWindowLayout.setStretch(0, 1000)
        self.dataWindowLayout.setStretch(1, 618)
        self.dataWindow.setLayout(self.dataWindowLayout)
        self.mainTab.addTab(self.dataWindow, 'Data Explorer')
        # init output window
        self.outputTab.addTab(self.outputEdit, 'Output')
        # init right lay out
        self.rightLayout.addWidget(self.mainTab)
        self.rightLayout.addWidget(self.outputTab)
        self.rightLayout.setStretch(0, 10)
        self.rightLayout.setStretch(1, 3)
        self.mainLayout.addWidget(self.toolset, 0, 0)
        self.mainLayout.addLayout(self.rightLayout, 0, 1)
        self.mainLayout.setColumnStretch(0, 2)
        self.mainLayout.setColumnStretch(1, 10)

    def highLightSetting(self):
        layout = QVBoxLayout(self)
        self.tools_highLight.setLayout(layout)
        # init object
        NA_Threshold = 0
        NA_ThresholdEdit = QDoubleSpinBox(self)
        NA_ThresholdEdit.setSingleStep(5.0)
        NA_ThresholdEdit.setValue(NA_Threshold)
        NA_ThresholdEdit.setSuffix('%')
        NA_ThresholdEdit.setMaximumSize(85, 25)
        NA_ThresholdLayout = QHBoxLayout(self)
        NA_ThresholdLayout.addWidget(QLabel('NA %: '))
        NA_ThresholdLayout.addWidget(NA_ThresholdEdit)
        # separate line
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(2)
        line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        line.setStyleSheet("background-color: #c0c0c0;")
        line.raise_()
        # switch
        switch = switchButton()
        switchLayout = QHBoxLayout(self)
        switchLayout.addWidget(QLabel('NA'))
        switchLayout.addWidget(switch)
        switch.toggled.connect(self.onSwitchToggled)
        resetButton = QPushButton('reset', self)
        # add object
        layout.addLayout(NA_ThresholdLayout, 3)
        layout.addWidget(line, 3)
        layout.addLayout(switchLayout, 20)
        layout.addWidget(resetButton, 3, Qt.AlignBottom)

    def initToolDataInfo(self):
        layout = QVBoxLayout(self)
        self.tools_dataInfo.setLayout(layout)
        layout.addWidget(QLabel('File Name:'))

    def initDataExplorer(self, filename):
        # load data
        self.dataFrame = pd.read_csv(filename)
        # init table
        self.dataExplorer.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.dataExplorer.verticalHeader().setFixedWidth(self.verticalHeaderWidth)
        self.model.loadCSV(self.dataFrame)

    def initStatistic(self):
        rowCount = 0
        self.statistic.verticalHeader().setFixedWidth(self.verticalHeaderWidth)
        self.statistic.setColumnCount(self.dataFrame.shape[1])
        self.statistic.setHorizontalHeaderLabels(self.dataFrame.columns.tolist())
        # Type
        self.statistic.insertRow(rowCount)
        for i, c in enumerate(self.dataFrame.columns):
            self.statistic.setItem(rowCount, i, QTableWidgetItem(str(np.sum(self.dataFrame[c].dtype))))
        rowCount += 1
        # count NA
        self.statistic.insertRow(rowCount)
        for i, c in enumerate(self.dataFrame.columns):
            self.statistic.setItem(rowCount, i, QTableWidgetItem(str(np.sum(self.dataFrame[c].isnull()))))
        rowCount += 1
        # NA percentage
        self.statistic.insertRow(rowCount)
        for i, c in enumerate(self.dataFrame.columns):
            self.statistic.setItem(rowCount, i,
                                   QTableWidgetItem(str(np.sum(self.dataFrame[c].isnull()) / self.dataFrame.shape[0])))
        rowCount += 1
        # mean
        self.statistic.insertRow(rowCount)
        for i, c in enumerate(self.dataFrame.columns):
            if self.dataFrame[c].dtype == 'object':
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str('N/A')))
            else:
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str(self.dataFrame[c].mean())))
        rowCount += 1
        # std
        self.statistic.insertRow(rowCount)
        for i, c in enumerate(self.dataFrame.columns):
            if self.dataFrame[c].dtype == 'object':
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str('N/A')))
            else:
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str(self.dataFrame[c].std())))
        rowCount += 1
        # max
        self.statistic.insertRow(rowCount)
        for i, c in enumerate(self.dataFrame.columns):
            if self.dataFrame[c].dtype == 'object':
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str('N/A')))
            else:
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str(self.dataFrame[c].max())))
        rowCount += 1
        # min
        self.statistic.insertRow(rowCount)
        for i, c in enumerate(self.dataFrame.columns):
            if self.dataFrame[c].dtype == 'object':
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str('N/A')))
            else:
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str(self.dataFrame[c].min())))
        rowCount += 1
        # skew
        self.statistic.insertRow(rowCount)
        for i, c in enumerate(self.dataFrame.columns):
            if self.dataFrame[c].dtype == 'object':
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str('N/A')))
            else:
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str(self.dataFrame[c].skew())))
        rowCount += 1
        # Kurtosis
        self.statistic.insertRow(rowCount)
        for i, c in enumerate(self.dataFrame.columns):
            if self.dataFrame[c].dtype == 'object':
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str('N/A')))
            else:
                self.statistic.setItem(rowCount, i, QTableWidgetItem(str(self.dataFrame[c].kurtosis())))
        rowCount += 1
        # set vertical head label
        self.statistic.setVerticalHeaderLabels(
            ['Type', 'Count NA', 'NA %', 'mean', 'std', 'max', 'min', 'skew', 'Kurtosis'])

    def onSwitchToggled(self, checked):
        print(checked)

    def closeEvent(self, QCloseEvent):
        # del self.dataFrame
        gc.collect()

    def eventFilter(self, target, event):
        if target == self.dataExplorer.horizontalScrollBar():
            if event.type() == QEvent.Wheel:
                print('wheel')
                return False
            elif event.type() == QEvent.MouseButtonPress:
                print('mouse Press')
                return False
            elif event.type() == QEvent.MouseButtonRelease:
                print(self.dataExplorer.item(0, 0))
                print('mouse Release')
                return False
            elif event.type() == QEvent.MouseMove:
                print('mouse move')
                return False
            else:
                return False
        else:
            return QWidget.eventFilter(target, event)
        # return


class customTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super(customTableModel, self).__init__(parent=parent)
        self.rows = 0
        self.cols = 0
        self.dataFrame = pd.DataFrame()

    def loadCSV(self, dataFrame):
        self.dataFrame = dataFrame
        self.rows = self.dataFrame.shape[0]
        self.cols = self.dataFrame.shape[1]
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rows, self.cols))

    def rowCount(self, parent=None, *args, **kwargs):
        return self.rows

    def columnCount(self, parent=None, *args, **kwargs):
        return self.cols

    def setRowCount(self, rows):
        self.rows = rows

    def setColumnCount(self, cols):
        self.cols = cols

    def data(self, modelIndex: QModelIndex, role=None):
        if role == Qt.DisplayRole:
            return str(self.dataFrame.iloc[modelIndex.row()][modelIndex.column()])
        else:
            return QVariant()

    def headerData(self, section, orientation, role=None):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return self.dataFrame.columns[section]
        if orientation == Qt.Vertical:
            return self.dataFrame.index[section] + 1
        return QVariant()

    def flags(self, modelIndex):
        # flags = QAbstractTableModel.flags(self, modelIndex)
        flags = Qt.NoItemFlags
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        return flags


class IpythonTabWidget(QWidget):
    def __init__(self, scriptDir, parent=None):
        super(IpythonTabWidget, self).__init__(parent)
        log("Starting Jupyter notebook process")
        self.notebookp = startnotebook(directory=scriptDir)

        log("Waiting for server to start...")
        webaddr = None
        while webaddr is None:
            line = str(self.notebookp.stderr.readline())
            log(line)
            if "http://" in line:
                start = line.find("http://")
                end = line.find("/", start + len("http://"))
                webaddr = line[start:end]
        log("Server found at %s, migrating monitoring to listener thread" % webaddr)
        # pass monitoring over to child thread
        notebookmonitor = threading.Thread(name="Notebook Monitor", target=process_thread_pipe,
                                           args=(self.notebookp,))
        notebookmonitor.start()

        self.homepage = webaddr
        self.windows = []
        self.layout = QGridLayout(self)
        self.basewebview = IpythonWebView(self, main=True)
        self.layout.addWidget(self.basewebview, 0, 0)
        self.setLayout(self.layout)
        QTimer.singleShot(0, self.initialload)

    @pyqtSlot()
    def initialload(self):
        if self.homepage:
            self.basewebview.load(QUrl(self.homepage))
        self.show()

    def closeEvent(self, event):
        if self.windows:
            for i in reversed(range(len(self.windows))):
                w = self.windows.pop(i)
                w.close()
            event.accept()
        else:
            event.accept()
        self.notebookp.kill()

    def delProcess(self):
        self.notebookp.kill()


class IpythonWebView(QWebEngineView):
    newIpython = pyqtSignal(QWebEngineView)

    def __init__(self, mainwindow, main=False):
        super(IpythonWebView, self).__init__(None)
        self.parent = mainwindow
        self.main = main
        self.loadedPage = None

    @pyqtSlot(bool)
    def onpagechange(self, ok):
        log("on page change: %s, %s" % (self.url(), ok))
        if self.loadedPage is not None:
            log("disconnecting on close signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)
        self.loadedPage = self.page()
        log("connecting on close signal")
        self.loadedPage.windowCloseRequested.connect(self.close)

    def createWindow(self, windowType):
        v = IpythonWebView(self.parent)
        windows = self.parent.windows
        windows.append(v)
        self.newIpython.emit(v)
        v.show()
        return v

    def closeEvent(self, event):
        if self.loadedPage is not None:
            log("disconnecting on close signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)

        if not self.main:
            if self in self.parent.windows:
                self.parent.windows.remove(self)
            log("Window count: %s" % (len(self.parent.windows) + 1))
        event.accept()


# widget for tab
class ModelTabWidget(QWidget):
    from model import ml_model
    from project import ml_project
    def __init__(self, MLModel: ml_model, MLProject: ml_project, parent=None):
        super(ModelTabWidget, self).__init__(parent=parent)
        self.MLProject = MLProject
        self.MLModel = MLModel
        self.outLayout = QVBoxLayout(self)
        self.statusFrame = QFrame(self)
        self.statusLayout = QGridLayout(self)
        self.runButton = QPushButton('Run',self)
        self.stopButton = QPushButton('Stop',self)
        self.addButton = QPushButton('Add',self)

        self.settingLayout = QHBoxLayout(self)
        self.modelInfo = QGroupBox(self)
        self.modelParam = QGroupBox(self)
        self.modelData = QGroupBox(self)

        self.modelInfoScroll = QScrollArea(self)
        self.modelParamScroll = QScrollArea(self)
        self.modelDataScroll = QScrollArea(self)

        self.modelInfoLayout = QFormLayout(self)
        self.modelParamLayout = QFormLayout(self)
        self.modelDataLayout = QFormLayout(self)
        self.initUI()
        self.initModelInfo()
        self.initXGBParam()
        self.initData()

    def initUI(self):
        self.setLayout(self.outLayout)
        self.outLayout.addWidget(self.statusFrame)
        self.outLayout.addLayout(self.settingLayout)
        self.outLayout.setStretch(0, 1)
        self.outLayout.setStretch(1, 4)
        self.statusFrame.setLayout(self.statusLayout)
        self.statusLayout.addWidget(QLabel('Model Name'), 0, 0)
        self.statusLayout.addWidget(self.runButton, 0, 5)
        self.statusLayout.addWidget(self.stopButton, 1, 5)
        self.statusLayout.addWidget(self.addButton, 2, 5)

        l = QHBoxLayout(self)
        l.addWidget(self.modelInfoScroll)
        self.modelInfo.setLayout(l)
        self.modelInfoScroll.setWidgetResizable(True)
        t = QWidget(self)
        t.setLayout(self.modelInfoLayout)
        self.modelInfoScroll.setWidget(t)
        self.modelInfoScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        l = QHBoxLayout(self)
        l.addWidget(self.modelParamScroll)
        self.modelParam.setLayout(l)
        self.modelParamScroll.setWidgetResizable(True)
        t = QWidget(self)
        t.setLayout(self.modelParamLayout)
        self.modelParamScroll.setWidget(t)
        self.modelParamScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        l = QHBoxLayout(self)
        l.addWidget(self.modelDataScroll)
        self.modelData.setLayout(l)
        self.modelDataScroll.setWidgetResizable(True)
        t = QWidget(self)
        t.setLayout(self.modelDataLayout)
        self.modelDataScroll.setWidget(t)
        self.modelDataScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.settingLayout.addWidget(self.modelInfo)
        self.settingLayout.addWidget(self.modelParam)
        self.settingLayout.addWidget(self.modelData)

        self.modelInfo.setTitle('Model')
        self.modelParam.setTitle('Param')
        self.modelData.setTitle('Data')

    def initModelInfo(self):
        self.modelInfoLayout.setContentsMargins(15, 20, 15, 10)

        algorithm = QComboBox(self)
        algorithm.addItems(['xgboost', 'lightGBM', 'random forest'])
        self.modelInfoLayout.addRow('Algorithm: ', algorithm)
        metric = QComboBox(self)
        metric.addItems(['rmse', 'auc', 'logloss', 'error'])
        self.modelInfoLayout.addRow('Metric: ', metric)
        kFold = QSpinBox(self)
        kFold.setRange(0, 10)
        kFold.setSingleStep(1)
        kFold.setValue(5)
        self.modelInfoLayout.addRow('kFold: ', kFold)
        resultFile = QLineEdit(self)
        resultFileCheck = QCheckBox(self)
        resultFileCheck.setText('not save result')
        resultFile.setText('model.result')
        self.modelInfoLayout.addRow('result file: ', resultFile)
        self.modelInfoLayout.addRow('', resultFileCheck)
        resultFileCheck.stateChanged.connect(lambda: resultFile.setDisabled(resultFileCheck.checkState()))

    def initXGBParam(self):
        self.modelParamLayout.setContentsMargins(15, 20, 15, 10)

        objective = QComboBox(self)
        objective.addItems(
            ['reg:linear', 'reg:logistic', 'binary:logistic', 'binary:logitraw', 'count:poisson', 'reg:gamma'])
        self.modelParamLayout.addRow('objective: ', objective)

        learning_rate = QDoubleSpinBox(self)
        learning_rate.setRange(0, 1)
        learning_rate.setValue(0.3)
        learning_rate.setSingleStep(0.01)
        self.modelParamLayout.addRow('learning_rate: ', learning_rate)

        gamma = QDoubleSpinBox(self)
        gamma.setMinimum(0)
        gamma.setSingleStep(0.1)
        gamma.setValue(0)
        self.modelParamLayout.addRow('gamma: ', gamma)

        max_depth = QSpinBox(self)
        max_depth.setMinimum(0)
        max_depth.setValue(6)
        self.modelParamLayout.addRow('max_depth: ', max_depth)

        min_child_weight = QDoubleSpinBox(self)
        min_child_weight.setMinimum(0)
        min_child_weight.setSingleStep(0.1)
        min_child_weight.setValue(1)
        self.modelParamLayout.addRow('min_child_weight: ', min_child_weight)

        max_delta_step = QDoubleSpinBox(self)
        max_delta_step.setMinimum(0)
        max_delta_step.setSingleStep(0.1)
        max_delta_step.setValue(0)
        self.modelParamLayout.addRow('max_delta_step: ', max_delta_step)

        subsample = QDoubleSpinBox(self)
        subsample.setMinimum(0.01)
        subsample.setSingleStep(0.1)
        subsample.setValue(1)
        self.modelParamLayout.addRow('subsample: ', subsample)

        colsample_bytree = QDoubleSpinBox(self)
        colsample_bytree.setMinimum(0.01)
        colsample_bytree.setSingleStep(0.1)
        colsample_bytree.setValue(1)
        self.modelParamLayout.addRow('colsample_bytree: ', colsample_bytree)

        colsample_bylevel = QDoubleSpinBox(self)
        colsample_bylevel.setMinimum(0.01)
        colsample_bylevel.setSingleStep(0.1)
        colsample_bylevel.setValue(1)
        self.modelParamLayout.addRow('colsample_bylevel: ', colsample_bylevel)

        reg_lambda = QDoubleSpinBox(self)
        reg_lambda.setMinimum(0)
        reg_lambda.setSingleStep(0.1)
        reg_lambda.setValue(1)
        self.modelParamLayout.addRow('reg_lambda: ', reg_lambda)

        reg_alpha = QDoubleSpinBox(self)
        reg_alpha.setMinimum(0)
        reg_alpha.setSingleStep(0.1)
        reg_alpha.setValue(0)
        self.modelParamLayout.addRow('reg_alpha: ', reg_alpha)

        tree_method = QComboBox(self)
        tree_method.addItems(['auto', 'exact', 'approx', 'hist', 'gpu_exact', 'gpu_hist'])
        self.modelParamLayout.addRow('tree_method: ', tree_method)

        scale_pos_weight = QDoubleSpinBox(self)
        scale_pos_weight.setMinimum(0)
        scale_pos_weight.setSingleStep(0.1)
        scale_pos_weight.setValue(1)
        self.modelParamLayout.addRow('scale_pos_weight: ', scale_pos_weight)

        predictor = QComboBox(self)
        predictor.addItems(['cpu_predictor', 'gpu_predictor'])
        self.modelParamLayout.addRow('predictor: ', predictor)

    def initData(self):
        self.modelDataLayout.setContentsMargins(10, 20, 10, 10)

        trainSet = QComboBox(self)
        trainSet.addItems(self.MLProject.dataFiles_pkl)
        trainSet.addItems(self.MLProject.dataFiles_csv)
        self.modelDataLayout.addRow('trainSet: ', trainSet)

        testSet = QComboBox(self)
        testSet.addItems(self.MLProject.dataFiles_pkl)
        testSet.addItems(self.MLProject.dataFiles_csv)
        self.modelDataLayout.addRow('trainSet: ', testSet)


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QGridLayout(self)
        self.setFixedSize(800, 500)
        self.setLayout(self.mainLayout)
        self.item = QTableView(self)
        self.model = customTableModel(self)
        self.item.setModel(self.model)
        self.model.loadCSV(pd.DataFrame([[1, 2], [2, 3], [3, 4]], columns=['id', 'value']))
        self.mainLayout.addWidget(self.item, 0, 0)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
