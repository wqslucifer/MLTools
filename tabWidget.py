import os
import sys
import importlib
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QListWidget, QToolBox, \
    QTabWidget, QTextEdit, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QSpinBox, \
    QDoubleSpinBox, QFrame, QSizePolicy, QHeaderView, QTableView, QApplication, QScrollArea, QScrollBar, QSplitter, \
    QSplitterHandle, QComboBox, QGroupBox, QFormLayout, QCheckBox, QMenu, QAction, QWidgetAction, QStackedWidget, \
    QHeaderView, QMessageBox, QProgressBar, QListWidgetItem, QToolBar, QFileDialog
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, QSettings, QTimer, QUrl, QDir, \
    QAbstractTableModel, QEvent, QObject, QModelIndex, QVariant, QThread, QObject, QMimeData, QRegExp, QTextStream, \
    QFile, QIODevice
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath, QStandardItemModel, QTextCursor, \
    QCursor, QDrag, QStandardItem, QIcon, QSyntaxHighlighter, QKeySequence, QTextCharFormat
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from customWidget import CollapsibleTabWidget, ImageViewer, DragTableView, customProcessModel
from customLayout import FlowLayout
from processSettingDialogs import fillNADialog, logTransformDialog

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

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns
from process import processQueue, QtReceiver
import GENERAL
from management import manageProcess

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
    Horizontal = 0
    Vertical = 1
    addProcessQueue = pyqtSignal(processQueue)
    jumpToPQTab = pyqtSignal()

    def __init__(self, filename):
        super(DataTabWidget, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        # local data
        self.filename = filename
        self.dataType = None
        self.dataFrame = None
        self.verticalHeaderWidth = 70
        self.displayRows = 2
        self.displayCols = 7

        self.displaySize = 3
        self.displayWidth = self.displaySize
        self.displayHeight = self.displaySize
        # init widgets
        self.splitterMain = QSplitter(Qt.Vertical)

        self.mainLayout = QGridLayout(self)
        self.rightLayout = QVBoxLayout(self)
        self.toolset = QToolBox(self)
        self.tools_highLight = QWidget(self)
        self.tools_dataInfo = QWidget(self)
        self.tools_process = QWidget(self)
        self.tools_visualize = QWidget(self)
        # highlight tools
        self.NA_Threshold = 80
        self.NAThresholdChanged = []

        # main window
        self.dataWindow = QWidget(self)
        self.dataWindowLayout = QVBoxLayout(self)
        self.dataProcess = QWidget(self)
        self.dataExplorer = QTableView(self)
        self.tableModel = customTableModel(self)
        self.dataExplorer.setModel(self.tableModel)
        self.dataExplorer.autoScrollMargin()
        self.statistic = QTableWidget(self)
        self.dataExplorerPopMenu = QMenu(self)
        self.plotLayout = FlowLayout()
        self.pq = processQueue()
        self.processTabModel = customProcessModel(self)
        # GENERAL.set_value('PROCESS_MANAGER', self.processManager)

        self.mainTab = QTabWidget(self)
        self.outputTab = CollapsibleTabWidget(self.Horizontal, self)
        self.outputEdit = QTextEdit(self)
        # init UI
        self.initUI()
        # init statistic table
        self.initStatistic()
        # right click menu
        self.initRightClickMenu()
        # plot tab setting
        self.initPlotTab()
        # init process tab
        self.initProcessTab()

    def initUI(self):
        self.highLightSetting()
        self.initToolDataInfo()
        self.initToolProcess()
        self.toolset.addItem(self.tools_highLight, 'Setting')
        self.toolset.addItem(self.tools_dataInfo, 'Data Info')
        self.toolset.addItem(self.tools_process, 'Data Process')
        self.toolset.addItem(self.tools_visualize, 'Data Visualize')
        self.toolset.currentChanged.connect(self.jumpToPQ)
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
        self.outputTab.setSplitter(self.splitterMain)
        # init right lay out
        self.rightLayout.addWidget(self.splitterMain)
        self.splitterMain.addWidget(self.mainTab)
        self.splitterMain.addWidget(self.outputTab)
        # self.splitterMain.setStretchFactor(0, 10)
        # self.splitterMain.setStretchFactor(1, 3)
        self.splitterMain.setCollapsible(0, False)
        self.splitterMain.setCollapsible(1, False)
        self.splitterMain.setSizes([10000, 0])  # move splitter to the bottom

        self.mainLayout.addWidget(self.toolset, 0, 0)
        self.mainLayout.addLayout(self.rightLayout, 0, 1)
        self.mainLayout.setColumnStretch(0, 2)
        self.mainLayout.setColumnStretch(1, 10)

    def initRightClickMenu(self):
        self.dataExplorer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dataExplorer.customContextMenuRequested.connect(self.onDataExplorerRightClicked)

    def initPlotTab(self):
        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        plotWidget = QWidget(self)
        plotWidget.setLayout(self.plotLayout)
        scrollArea.setWidget(plotWidget)
        self.mainTab.addTab(scrollArea, 'plot')
        self.mainTab.setMaximumHeight(10000)
        self.mainTab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainTab.updateGeometry()

    def regressionPlot(self, point: QPoint):
        """
        display line of column
        x: index y: value
        :param point:QPoint
        :return:None
        """
        layout = QVBoxLayout(self)
        index = self.dataExplorer.indexAt(point)
        sortColumn = True
        if sortColumn:
            meta = self.dataFrame.iloc[:, index.column()].dropna().sort_values().reset_index(drop=True)
            meta_index = meta.index
            meta = pd.DataFrame([meta_index, meta]).transpose()
            meta.columns = ['index', 'meta']
        else:
            meta = self.dataFrame.iloc[:, index.column()].dropna()
            meta_index = meta.index
            meta = pd.DataFrame([meta_index, meta]).transpose()
            meta.columns = ['index', 'meta']

        # create plot
        fig = Figure(figsize=(self.displayWidth, self.displayHeight))
        fig.set_tight_layout(True)
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        # set color
        # sns.set(palette="muted", color_codes=True)
        sns.set(style="whitegrid")
        # plot data
        sns.regplot(x='index', y='meta', data=meta, ax=ax)

        ax.set_xlabel('index')
        ax.set_ylabel('value')
        # set title
        ax.set_title('regression: ' + self.dataFrame.columns[index.column()])
        # clean coord info on tool bar
        ax.format_coord = lambda x, y: ""
        # set tool bar
        toolbar = NavigationToolbar(canvas, self)
        canvas.draw()

        # add toolbar
        tmp = QWidget(self)
        tmp.setLayout(layout)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        self.plotLayout.addWidget(tmp)
        self.mainTab.setCurrentIndex(1)
        self.plotLayout.update()

    def scatterPlot(self, point: QPoint):
        """
        display scatter of column, show distribution by index  x: index y: dataFrame column
        :param point:QPoint
        :return:None
        """
        layout = QVBoxLayout(self)
        index = self.dataExplorer.indexAt(point)

        X = self.dataFrame.index.tolist()
        Y = self.dataFrame.iloc[:, index.column()]
        # create plot
        fig = Figure(figsize=(self.displayWidth, self.displayHeight))
        fig.set_tight_layout(True)
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        # set color
        # sns.set(palette="muted", color_codes=True)
        sns.set(style="whitegrid")
        # plot data
        sns.scatterplot(x=X, y=Y, palette="ch:r=-.2,d=.3_r",
                        size=Y, sizes=(2, 5), linewidth=0, ax=ax, legend=False)
        ax.set_xlabel('index')
        ax.set_ylabel('value')
        # set title
        ax.set_title('scatter: ' + self.dataFrame.columns[index.column()])
        # clean coord info on tool bar
        ax.format_coord = lambda x, y: ""
        # set tool bar
        toolbar = NavigationToolbar(canvas, self)
        canvas.draw()

        # add toolbar
        tmp = QWidget(self)
        tmp.setLayout(layout)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        self.plotLayout.addWidget(tmp)
        self.mainTab.setCurrentIndex(1)
        self.plotLayout.update()

    def distPlot(self, point: QPoint):
        """
        display scatter of column, show distribution histogram of this column
        x: value of column y: hist
        :param point:QPoint
        :return:None
        """
        layout = QVBoxLayout(self)
        index = self.dataExplorer.indexAt(point)

        X = self.dataFrame.iloc[:, index.column()]
        # create plot
        fig = Figure(figsize=(self.displayWidth, self.displayHeight))
        fig.set_tight_layout(True)
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        # set color
        # sns.set(palette="muted", color_codes=True)
        sns.set(style="whitegrid")
        # plot data
        sns.distplot(a=X.dropna(), bins=30, hist=True, norm_hist=True, kde=True, rug=True, ax=ax)
        ax.set_xlabel('value')
        ax.set_ylabel('hist')
        # set title
        ax.set_title('distribution: ' + self.dataFrame.columns[index.column()])
        # clean coord info on tool bar
        ax.format_coord = lambda x, y: ""
        # set tool bar
        toolbar = NavigationToolbar(canvas, self)
        canvas.draw()

        # add toolbar
        tmp = QWidget(self)
        tmp.setLayout(layout)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        self.plotLayout.addWidget(tmp)
        self.mainTab.setCurrentIndex(1)
        self.plotLayout.update()

    def linePlot(self, point: QPoint):
        """
        display line of column
        x: index y: value
        :param point:QPoint
        :return:None
        """
        layout = QVBoxLayout(self)
        index = self.dataExplorer.indexAt(point)
        sortColumn = False
        if sortColumn:
            Y = self.dataFrame.iloc[:, index.column()].sort_values()
            X = [i for i in range(Y.shape[0])]
        else:
            X = self.dataFrame.index.tolist()
            Y = self.dataFrame.iloc[:, index.column()]
        # create plot
        fig = Figure(figsize=(self.displayWidth, self.displayHeight))
        fig.set_tight_layout(True)
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        # set color
        # sns.set(palette="muted", color_codes=True)
        sns.set(style="whitegrid")
        # plot data
        sns.lineplot(x=X, y=Y.dropna(), ax=ax)
        ax.set_xlabel('index')
        ax.set_ylabel('value')
        # set title
        ax.set_title('line: ' + self.dataFrame.columns[index.column()])
        # clean coord info on tool bar
        ax.format_coord = lambda x, y: ""
        # set tool bar
        toolbar = NavigationToolbar(canvas, self)
        canvas.draw()

        # add toolbar
        tmp = QWidget(self)
        tmp.setLayout(layout)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        self.plotLayout.addWidget(tmp)
        self.mainTab.setCurrentIndex(1)
        self.plotLayout.update()

    def countPlot(self, point: QPoint):
        """
        display number of each category in column
        x: category y: count
        :param point:QPoint
        :return:None
        """
        layout = QVBoxLayout(self)
        index = self.dataExplorer.indexAt(point)

        X = self.dataFrame.iloc[:, index.column()]
        X = X.fillna('NAN')
        # create plot
        fig = Figure(figsize=(self.displayWidth, self.displayHeight))
        fig.set_tight_layout(True)
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        # set color
        # sns.set(palette="muted", color_codes=True)
        sns.set(style="whitegrid")
        # plot data
        sns.countplot(x=X, ax=ax)
        ax.set_xlabel(self.dataFrame.columns[index.column()])
        ax.set_ylabel('count')
        # set title
        ax.set_title('count: ' + self.dataFrame.columns[index.column()])
        # clean coord info on tool bar
        ax.format_coord = lambda x, y: ""
        # set tool bar
        toolbar = NavigationToolbar(canvas, self)
        canvas.draw()

        # add toolbar
        tmp = QWidget(self)
        tmp.setLayout(layout)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        self.plotLayout.addWidget(tmp)
        self.mainTab.setCurrentIndex(1)
        self.plotLayout.update()

    def nanPlot(self, point: QPoint):
        """
        display number of nan in column
        x: column name y: nan or not count
        :param point:QPoint
        :return:None
        """
        layout = QVBoxLayout(self)
        index = self.dataExplorer.indexAt(point)
        meta = self.dataFrame.isnull().any()
        na_columns = meta[meta == True].index

        X = na_columns
        # create plot
        fig = Figure(figsize=(self.displayWidth + 2, self.displayHeight + 2))
        fig.set_tight_layout(True)
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        # set color
        # sns.set(palette="muted", color_codes=True)
        sns.set(style="whitegrid")
        # plot
        if len(X):
            Y1 = np.sum(self.dataFrame[X].isnull())
            Y2 = self.dataFrame.shape[0]
            sns.set_color_codes("pastel")
            sns.barplot(x=[Y2 for _ in X], y=X, ax=ax, color="b")
            sns.set_color_codes("muted")
            plot = sns.barplot(x=Y1, y=X, ax=ax, color="r")
            labels = ax.get_xticks()
            plot.set_xticklabels(labels, rotation=45)
            labels = plot.get_yticklabels()
            plot.set_yticklabels(labels, rotation=50)

            sns.set_palette(sns.cubehelix_palette(8))
            ax.axvline(self.dataFrame.shape[0] * self.NA_Threshold / 100.0, color='#856798', clip_on=False)

        ax.set_xlabel('count')
        ax.set_ylabel(os.path.basename(self.filename))
        # set title
        ax.set_title('count NA: ' + os.path.basename(self.filename))
        # clean coord info on tool bar
        ax.format_coord = lambda x, y: ""
        # set tool bar
        toolbar = NavigationToolbar(canvas, self)
        canvas.draw()

        # add toolbar
        tmp = QWidget(self)
        tmp.setLayout(layout)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        self.plotLayout.addWidget(tmp)
        self.mainTab.setCurrentIndex(1)
        self.plotLayout.update()

    def boxPlot(self, point: QPoint):
        layout = QVBoxLayout(self)
        index = self.dataExplorer.indexAt(point)

        X = self.dataFrame.iloc[:, index.column()]
        # create plot
        fig = Figure(figsize=(self.displayWidth, self.displayHeight))
        fig.set_tight_layout(True)
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        # set color
        # sns.set(palette="muted", color_codes=True)
        sns.set(style="whitegrid")
        # plot data
        sns.boxplot(x=X, ax=ax)
        ax.set_xlabel(self.dataFrame.columns[index.column()])
        ax.set_ylabel('count')
        # set title
        ax.set_title('count: ' + self.dataFrame.columns[index.column()])
        # clean coord info on tool bar
        ax.format_coord = lambda x, y: ""
        # set tool bar
        toolbar = NavigationToolbar(canvas, self)
        canvas.draw()

        # add toolbar
        tmp = QWidget(self)
        tmp.setLayout(layout)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        self.plotLayout.addWidget(tmp)
        self.mainTab.setCurrentIndex(1)
        self.plotLayout.update()

    def countNAPlot(self, point: QPoint):
        layout = QVBoxLayout(self)
        index = self.dataExplorer.indexAt(point)

        X = np.sum(self.dataFrame.iloc[:, index.column()].isnull())
        pNA = float(X * 100.0 / self.dataFrame.shape[0])

        # create plot
        fig = Figure(figsize=(self.displayWidth, self.displayHeight))
        fig.set_tight_layout(True)
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        # set color
        sns.set(palette="muted", color_codes=True)
        sns.set(style="whitegrid")
        # plot data
        p1 = sns.barplot(x=[self.dataFrame.columns[index.column()]], y=self.dataFrame.shape[0], hue=['Total'], ax=ax,
                         palette=sns.color_palette(["#4c72b0"]))
        bar = p1.patches[0]
        centre = bar.get_x() + bar.get_width() / 2.
        bar.set_x(centre - 0.2)
        bar.set_width(0.4)
        p1.text(bar.get_x() + bar.get_width() / 2 - 0.1, bar.get_height(), '%.2f%%' % pNA)
        p1.axes.legend(loc='best')

        p2 = sns.barplot(x=[self.dataFrame.columns[index.column()]], y=X, ax=ax, hue=['NA'],
                         palette=sns.color_palette(["#c44e52"]))
        bar = p2.patches[1]
        centre = bar.get_x() + bar.get_width() / 2.
        bar.set_x(centre - 0.2)
        bar.set_width(0.4)

        ax.set_xlabel('column')
        ax.set_ylabel('count')
        # set title
        ax.set_title('count NA: ' + self.dataFrame.columns[index.column()])
        # clean coord info on tool bar
        ax.format_coord = lambda x, y: ""
        # set tool bar
        toolbar = NavigationToolbar(canvas, self)
        canvas.draw()

        # add toolbar
        tmp = QWidget(self)
        tmp.setLayout(layout)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        self.plotLayout.addWidget(tmp)
        self.mainTab.setCurrentIndex(1)
        self.plotLayout.update()

    def highLightSetting(self):
        layout = QVBoxLayout(self)
        self.tools_highLight.setLayout(layout)
        # init object
        NA_ThresholdEdit = QSpinBox(self)
        NA_ThresholdEdit.setSingleStep(5)
        NA_ThresholdEdit.setValue(self.NA_Threshold)
        NA_ThresholdEdit.setSuffix('%')
        NA_ThresholdEdit.setMaximumSize(95, 25)
        NA_ThresholdEdit.valueChanged.connect(self.setNA_Threshold)
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
        # highlight over threshold NA
        overNAThreshold = switchButton()
        overNAThresholdLayout = QHBoxLayout(self)
        overNAThresholdLayout.addWidget(QLabel('highlight NA'))
        overNAThresholdLayout.addWidget(overNAThreshold)
        overNAThreshold.toggled.connect(self.onOverNAThresholdToggled)

        resetButton = QPushButton('reset', self)
        # add object
        layout.addLayout(NA_ThresholdLayout, 3)
        layout.addWidget(line, 3)
        layout.addLayout(switchLayout, 3)
        layout.addLayout(overNAThresholdLayout, 20)
        layout.addWidget(resetButton, 3, Qt.AlignBottom)

    def initToolDataInfo(self):
        layout = QVBoxLayout(self)
        self.tools_dataInfo.setLayout(layout)
        layout.addWidget(QLabel('File Name:'))

    def initToolProcess(self):
        layout = QVBoxLayout(self)
        self.tools_process.setLayout(layout)
        # fill na
        fillNAButton = QPushButton('Fill NA', self)
        fillNAButton.clicked.connect(lambda: self.popSetting('fillNA'))
        # log transform
        logTransformButton = QPushButton('Log Transformation', self)
        logTransformButton.clicked.connect(lambda: self.popSetting('logTrans'))
        # add sleep 10s
        sleepDelayButton = QPushButton('sleep 10s', self)
        sleepDelayButton.clicked.connect(lambda: self.addDelay())
        # add import function button
        importFuncButton = QPushButton('import function', self)
        importFuncButton.clicked.connect(lambda: self.popFuncManager())

        # add to queue
        addToQueueButton = QPushButton('add to Queue', self)
        addToQueueButton.clicked.connect(lambda: self.addToQueue())

        layout.addWidget(fillNAButton)
        layout.addWidget(logTransformButton)
        layout.addWidget(sleepDelayButton)
        layout.addWidget(importFuncButton)
        layout.addStretch(10)
        layout.addWidget(addToQueueButton)

    def initDataExplorer(self, filename):
        # load data
        if filename.endswith('csv'):
            self.dataFrame = pd.read_csv(filename)
            self.dataType = 'csv'
        elif filename.endswith('pkl'):
            self.dataFrame = pd.read_pickle(filename)
            self.dataType = 'pkl'
        # init table
        self.dataExplorer.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.dataExplorer.verticalHeader().setFixedWidth(self.verticalHeaderWidth)
        self.tableModel.loadCSV(self.dataFrame)
        self.pq.setData(self.dataType, self.dataFrame)

    def initStatistic(self):
        rowCount = 0
        self.statistic.verticalHeader().setFixedWidth(self.verticalHeaderWidth)
        self.statistic.setColumnCount(self.dataFrame.shape[1])
        self.statistic.setHorizontalHeaderLabels([str(i) for i in self.dataFrame.columns.tolist()])
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
                                   QTableWidgetItem(
                                       '%.2f%%' % (np.sum(self.dataFrame[c].isnull()) * 100 / self.dataFrame.shape[0])))
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

    def setNA_Threshold(self, value):
        self.NA_Threshold = value

    def onOverNAThresholdToggled(self, checked):
        if checked:
            for col in range(len(self.dataFrame.columns)):
                tmp = self.statistic.item(2, col).text()
                if int(float(tmp[:-1])) > self.NA_Threshold:
                    self.statistic.item(1, col).setBackground(Qt.red)
                    self.statistic.item(2, col).setBackground(Qt.red)
                    self.NAThresholdChanged.append(col)
        else:
            for col in self.NAThresholdChanged:
                self.statistic.item(1, col).setBackground(Qt.transparent)
                self.statistic.item(2, col).setBackground(Qt.transparent)
            self.NAThresholdChanged.clear()

    def closeEvent(self, QCloseEvent):
        del self.dataFrame
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

    # init right click menu
    def onDataExplorerRightClicked(self, point: QPoint):
        self.dataExplorerPopMenu.clear()
        generalMenu = QMenu('General', self)
        g1 = QAction('NA plot', self)
        g1.triggered.connect(lambda: self.nanPlot(point))

        dataExplorerActionList = [g1]
        generalMenu.addActions(dataExplorerActionList)
        self.dataExplorerPopMenu.addMenu(generalMenu)

        # numeric
        numericMenu = QMenu('Numeric', self)
        a1 = QAction('scatter plot', self)
        a1.triggered.connect(lambda: self.scatterPlot(point))
        a2 = QAction('distribute plot', self)
        a2.triggered.connect(lambda: self.distPlot(point))
        a3 = QAction('line plot', self)
        a3.triggered.connect(lambda: self.linePlot(point))
        a4 = QAction('regression plot', self)
        a4.triggered.connect(lambda: self.regressionPlot(point))
        a5 = QAction('box plot', self)
        a5.triggered.connect(lambda: self.boxPlot(point))

        dataExplorerActionList = [a1, a2, a3, a4, a5]
        numericMenu.addActions(dataExplorerActionList)
        self.dataExplorerPopMenu.addMenu(numericMenu)

        # category
        categoryMenu = QMenu('Category', self)
        b1 = QAction('count plot', self)
        b1.triggered.connect(lambda: self.countPlot(point))

        dataExplorerActionList = [b1]
        categoryMenu.addActions(dataExplorerActionList)
        self.dataExplorerPopMenu.addMenu(categoryMenu)

        # process for column
        processMenu = QMenu('Process', self)
        p1 = QAction('Fill NA', self)
        p1.triggered.connect(lambda: self.fillNA(point))
        processMenu.addActions([p1])
        self.dataExplorerPopMenu.addMenu(processMenu)

        # test action
        t1 = QAction('column NA plot', self)
        t1.triggered.connect(lambda: self.fillNA(point))
        self.dataExplorerPopMenu.addAction(t1)

        test = QAction('test plot', self)
        test.triggered.connect(lambda: self.countNAPlot(point))
        self.dataExplorerPopMenu.addAction(test)
        # pop menu
        self.dataExplorerPopMenu.exec(QCursor.pos())

    def updateSplitter(self):
        if not self.outputTab.splitterLower:
            upper, lower = self.splitterMain.sizes()
            height = upper + lower
            self.splitterMain.setSizes([height * 3, height * 1])
        elif self.outputTab.stackWidget.isVisible():
            upper, lower = self.splitterMain.sizes()
            height = upper + lower
            self.splitterMain.setSizes([height - self.outputTab.splitterLower, self.outputTab.splitterLower])
        else:
            self.splitterMain.setSizes([10000, 0])

    def initProcessTab(self):
        layout = QVBoxLayout(self)
        self.dataProcess.setLayout(layout)
        # init process tab
        t = DragTableView(self)
        t.setEditTriggers(QTableView.NoEditTriggers)
        t.setSelectionBehavior(QTableView.SelectRows)
        t.setSelectionMode(QTableView.SingleSelection)
        t.setAlternatingRowColors(True)
        t.setFocusPolicy(Qt.NoFocus)

        self.processTabModel.loadQueue(self.pq)
        t.setModel(self.processTabModel)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t.show()

        layout.addWidget(t)
        self.mainTab.addTab(self.dataProcess, 'Process')

    def addDataProcess(self, func, param: dict, func_name: str, describe: str):
        index = self.pq.addProcess(func, param)
        self.pq.addDescribe(index, func_name, describe)
        self.processTabModel.addProcess()

    # process setting
    def popSetting(self, processName: str):
        if processName == 'fillNA':
            dialog = fillNADialog(self.pq, parent=self)
            dialog.show()
            dialog.accepted.connect(lambda: self.addDataProcess(*dialog.addProcess()))
        if processName == 'logTrans':
            dialog = logTransformDialog(self.pq, parent=self)
            dialog.show()
            dialog.accepted.connect(lambda: self.addDataProcess(*dialog.addProcess()))

    def addDelay(self):
        index = self.pq.addProcess(self.pq.sleep, {'seconds': 10})
        self.pq.addDescribe(index, 'Delay', 'Delay: sleep 10s')
        self.processTabModel.addProcess()

    def addToQueue(self):
        if len(self.pq.processQ) == 0:
            QMessageBox.information(self, 'Empty Process', 'Please Add Process', QMessageBox.Ok)
            return
        processManager = GENERAL.get_value('PROCESS_MANAGER')
        processList = GENERAL.get_value('PROCESS_LIST')
        processList.append(self.pq)
        sendQueue, receiveQueue = processManager.setCOMDir(len(processList) - 1)
        self.pq.setSignalQueue(sendQueue, receiveQueue)
        processManager.setProcessList(processList)
        processManager.setIDDir(self.pq.id, self.pq)
        GENERAL.set_value('PROCESS_LIST', processList)
        GENERAL.set_value('PROCESS_MANAGER', processManager)
        self.addProcessQueue.emit(self.pq)
        QMessageBox.information(self, 'Add Process', 'Add Process To Process List', QMessageBox.Ok)

        self.pq = processQueue()
        self.pq.setData(self.dataType, self.dataFrame)
        self.processTabModel.loadQueue(self.pq)
        self.jumpToPQTab.emit()

    def jumpToPQ(self, index):
        if index == 2:
            self.mainTab.setCurrentIndex(2)

    def popFuncManager(self):
        dialog = functionManagerDialog(self)
        dialog.show()


class queueTabWidget(QWidget):
    def __init__(self, parent=None):
        super(queueTabWidget, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.mainList = QListWidget(self)
        self.mainLayout.addWidget(self.mainList)
        self.processList = GENERAL.get_value('PROCESS_LIST')
        self.manageProcess = GENERAL.get_value('PROCESS_MANAGER')
        self.empty = True

    def initProcessList(self):
        self.processList = GENERAL.get_value('PROCESS_LIST')
        self.manageProcess = GENERAL.get_value('PROCESS_MANAGER')
        if self.empty:
            for pq in self.processList:
                self.addProcess(pq)
        else:
            self.empty = False

    def addProcess(self, pq: processQueue):
        item = QWidget(self)
        itemLayout = QVBoxLayout(self)
        item.setLayout(itemLayout)
        item.setObjectName('MainItem')
        item.setStyleSheet('QWidget#MainItem{border: 2px solid}')

        header = QWidget(self)
        headerLayout = QHBoxLayout(self)
        header.setLayout(headerLayout)
        header.setStyleSheet('border-bottom: 2px solid')
        if pq.pid:
            PID = QLabel('%d' % pq.pid, self)
        else:
            PID = QLabel('PID', self)
        PID.setFixedWidth(35)
        PID.setAlignment(Qt.AlignCenter)
        PID.setObjectName('PID')
        typeLabel = QLabel('Process Queue', self)
        typeLabel.setFixedWidth(150)
        runButton = QPushButton(self)
        runButton.setIcon(QIcon('./res/RunQueue.ico'))
        runButton.setToolTip('Run Process')
        runButton.setStatusTip('Run Process')
        runButton.clicked.connect(lambda: self.runProcess(pq))
        pauseButton = QPushButton(self)
        pauseButton.setIcon(QIcon('./res/PauseQueue.ico'))
        pauseButton.setToolTip('Pause Process')
        pauseButton.setStatusTip('Pause Process')
        stopButton = QPushButton(self)
        stopButton.setIcon(QIcon('./res/StopQueue.ico'))
        stopButton.setToolTip('Stop Process')
        stopButton.setStatusTip('Stop Process')
        headerLayout.addWidget(PID)
        headerLayout.addWidget(typeLabel)
        headerLayout.addWidget(runButton)
        headerLayout.addWidget(pauseButton)
        headerLayout.addWidget(stopButton)
        headerLayout.addStretch(1)
        itemLayout.addWidget(header)

        count = 0
        for id_, func, param in pq.processQ:
            name, describe = pq.processInfo[id_]
            _itemLayout = QHBoxLayout(self)
            _item = QWidget(self)
            _item.setLayout(_itemLayout)
            idLabel = QLabel('%d' % count, self)
            idLabel.setAlignment(Qt.AlignCenter)
            idLabel.setFixedWidth(25)
            processName = QLabel('%s' % name)
            processName.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            processDescribe = QLabel('%s' % describe)
            processDescribe.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            progressBar = QProgressBar(self)
            progressBar.setOrientation(Qt.Horizontal)
            progressBar.setMinimum(0)
            progressBar.setMaximum(100)
            progressBar.setValue(0)
            progressBar.setFormat('0%')
            progressBar.setObjectName('progressBar_' + str(id_))

            _itemLayout.addWidget(idLabel, stretch=1)
            _itemLayout.addWidget(processName, stretch=4)
            _itemLayout.addWidget(processDescribe, stretch=10)
            _itemLayout.addWidget(progressBar, stretch=10)

            itemLayout.addWidget(_item)
            count += 1

        listWidgetItem = QListWidgetItem(self.mainList)
        self.mainList.addItem(listWidgetItem)
        listWidgetItem.setSizeHint(item.sizeHint())
        self.mainList.setItemWidget(listWidgetItem, item)
        self.empty = False

    def runProcess(self, pq):
        sendQ, recvQ = self.manageProcess.getProcessCOMQ(len(self.processList) - 1)
        t = QtReceiver(sendQ, pq)
        t.mysignal.connect(self.signalProcess)
        t.start()
        pq.start()

    def signalProcess(self, signalObj: object):
        processAction = signalObj[0]
        if processAction in ['RUN', 'FIN']:
            pass
        elif processAction == 'PROGRESS':
            _, processID, currentProcessIndex, totalProgress = signalObj
            processListIndex, _ = self.manageProcess.processIDDir[processID]
            item = self.mainList.itemWidget(self.mainList.item(processListIndex))
            widget = item.findChild(QProgressBar, 'progressBar_' + str(currentProcessIndex))
            widget.setValue(totalProgress)
            widget.setFormat('%d%%' % totalProgress)
        elif processAction == 'PID':
            processID = signalObj[1]
            pid = signalObj[2]
            processListIndex, _ = self.manageProcess.processIDDir[processID]
            item = self.mainList.itemWidget(self.mainList.item(processListIndex))
            widget = item.findChild(QLabel, 'PID')
            widget.setText(str(pid))


class scriptTabWidget(QWidget):
    def __init__(self, scriptFile, parent=None):
        super(scriptTabWidget, self).__init__(parent=parent)
        self.scriptFile = scriptFile
        self.editable = True
        # widgets
        self.mainLayout = QVBoxLayout(self)
        self.editor = QTextEdit(self)
        # init
        self.initUI()

    def initUI(self):
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.editor)
        self.loadFile()
        font = QFont("Courier", 11)
        font.setFixedPitch(True)
        self.editor.setFont(font)
        self.editor.setStyleSheet('background-color:#353535')
        self.setHighLight()

    def loadFile(self):
        file = QFile(self.scriptFile)
        flag = file.open(QFile.ReadWrite | QFile.Text)
        if flag:
            readStream = QTextStream(file)
            self.editor.setText(readStream.readAll())
            file.close()
            del file
        else:
            QMessageBox.information(self, 'Error Message', 'Open File: ' + file.errorString(), QMessageBox.Ok)

    def saveFile(self):
        pass

    def setHighLight(self):
        if self.scriptFile.endswith('py'):
            pythonHighlighter(self.editor)
        else:
            pass


class pythonHighlighter(QSyntaxHighlighter):
    Rules = []
    Formats = {}

    def __init__(self, parent=None):
        super(pythonHighlighter, self).__init__(parent)
        self.initializeFormats()

        KEYWORDS = ["and", "as", "assert", "break", "class",
                    "continue", "def", "del", "elif", "else", "except",
                    "exec", "finally", "for", "from", "global", "if",
                    "import", "in", "is", "lambda", "not", "or", "pass",
                    "print", "raise", "return", "try", "while", "with",
                    "yield"]
        BUILTINS = ["abs", "all", "any", "basestring", "bool",
                    "callable", "chr", "classmethod", "cmp", "compile",
                    "complex", "delattr", "dict", "dir", "divmod",
                    "enumerate", "eval", "execfile", "exit", "file",
                    "filter", "float", "frozenset", "getattr", "globals",
                    "hasattr", "hex", "id", "int", "isinstance",
                    "issubclass", "iter", "len", "list", "locals", "map",
                    "max", "min", "object", "oct", "open", "ord", "pow",
                    "property", "range", "reduce", "repr", "reversed",
                    "round", "set", "setattr", "slice", "sorted",
                    "staticmethod", "str", "sum", "super", "tuple", "type",
                    "vars", "zip"]
        CONSTANTS = ["False", "True", "None", "NotImplemented",
                     "Ellipsis"]

        pythonHighlighter.Rules.append((QRegExp(
            "|".join([r"\b%s\b" % keyword for keyword in KEYWORDS])),
                                        "keyword"))
        pythonHighlighter.Rules.append((QRegExp(
            "|".join([r"\b%s\b" % builtin for builtin in BUILTINS])),
                                        "builtin"))
        pythonHighlighter.Rules.append((QRegExp(
            "|".join([r"\b%s\b" % constant
                      for constant in CONSTANTS])), "constant"))
        pythonHighlighter.Rules.append((QRegExp(
            r"\b[+-]?[0-9]+[lL]?\b"
            r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
            r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
                                        "number"))
        pythonHighlighter.Rules.append((QRegExp(
            r"\bPyQt4\b|\bQt?[A-Z][a-z]\w+\b"), "pyqt"))
        pythonHighlighter.Rules.append((QRegExp(r"\b@\w+\b"),
                                        "decorator"))
        stringRe = QRegExp(r"""(?:'[^']*'|"[^"]*")""")
        stringRe.setMinimal(True)
        pythonHighlighter.Rules.append((stringRe, "string"))
        self.stringRe = QRegExp(r"""(:?"["]".*"["]"|'''.*''')""")
        self.stringRe.setMinimal(True)
        pythonHighlighter.Rules.append((self.stringRe, "string"))
        self.tripleSingleRe = QRegExp(r"""'''(?!")""")
        self.tripleDoubleRe = QRegExp(r'''"""(?!')''')

    @staticmethod
    def initializeFormats():
        baseFormat = QTextCharFormat()
        baseFormat.setFontFamily("monospaced")
        baseFormat.setFontPointSize(14)
        for name, color in (("normal", Qt.white),
                            ("keyword", '#C86E12'), ("builtin", Qt.white),
                            ("constant", '#C86E12'),
                            ("decorator", '#BFCB46'), ("comment", '#909090'),
                            ("string", '#60A055'), ("number", '#46BECB'),
                            ("error", Qt.darkRed), ("pyqt", Qt.darkCyan)):
            format = QTextCharFormat(baseFormat)
            format.setForeground(QColor(color))
            if name in ("keyword", "decorator"):
                format.setFontWeight(QFont.Bold)
            if name == "comment":
                format.setFontItalic(True)
            pythonHighlighter.Formats[name] = format

    def highlightBlock(self, text):
        NORMAL, TRIPLESINGLE, TRIPLEDOUBLE, ERROR = range(4)

        textLength = len(text)
        prevState = self.previousBlockState()

        self.setFormat(0, textLength,
                       pythonHighlighter.Formats["normal"])

        if text.startswith("Traceback") or text.startswith("Error: "):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           pythonHighlighter.Formats["error"])
            return
        if (prevState == ERROR and
                not (text.startswith(sys.ps1) or text.startswith("#"))):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           pythonHighlighter.Formats["error"])
            return

        for regex, format in pythonHighlighter.Rules:
            i = regex.indexIn(text)
            while i >= 0:
                length = regex.matchedLength()
                self.setFormat(i, length,
                               pythonHighlighter.Formats[format])
                i = regex.indexIn(text, i + length)

        # Slow but good quality highlighting for comments. For more
        # speed, comment this out and add the following to __init__:
        # pythonHighlighter.Rules.append((QRegExp(r"#.*"), "comment"))
        if not text:
            pass
        elif text[0] == "#":
            self.setFormat(0, len(text),
                           pythonHighlighter.Formats["comment"])
        else:
            stack = []
            for i, c in enumerate(text):
                if c in ('"', "'"):
                    if stack and stack[-1] == c:
                        stack.pop()
                    else:
                        stack.append(c)
                elif c == "#" and len(stack) == 0:
                    self.setFormat(i, len(text),
                                   pythonHighlighter.Formats["comment"])
                    break

        self.setCurrentBlockState(NORMAL)

        if self.stringRe.indexIn(text) != -1:
            return
        # This is fooled by triple quotes inside single quoted strings
        for i, state in ((self.tripleSingleRe.indexIn(text),
                          TRIPLESINGLE),
                         (self.tripleDoubleRe.indexIn(text),
                          TRIPLEDOUBLE)):
            if self.previousBlockState() == state:
                if i == -1:
                    i = text.length()
                    self.setCurrentBlockState(state)
                self.setFormat(0, i + 3,
                               pythonHighlighter.Formats["string"])
            elif i > -1:
                self.setCurrentBlockState(state)
                self.setFormat(i, text.length(),
                               pythonHighlighter.Formats["string"])

    def rehighlight(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QSyntaxHighlighter.rehighlight(self)
        QApplication.restoreOverrideCursor()


class NavigationToolbar(NavigationToolbar2QT):
    def __init__(self, *args, **kwargs):
        self.toolitems = [t for t in NavigationToolbar2QT.toolitems if
                          t[0] in ('Home', 'Pan', 'Zoom', 'Save')]
        super(NavigationToolbar, self).__init__(*args, **kwargs)


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


class functionModel(QAbstractTableModel):
    notEmpty = pyqtSignal()

    def __init__(self, parent=None):
        super(functionModel, self).__init__(parent=parent)
        self.rows = 0
        self.cols = 0
        self.functionList = None

    def loadFuncList(self, functionList):
        self.functionList = functionList
        self.rows = len(self.functionList)
        self.cols = 3  # name, param, param_count, filename, dependent
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rows, self.cols))
        if self.rows > 0:
            self.notEmpty.emit()

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
            if modelIndex.column() == 0:  # name
                return str(self.functionList[modelIndex.row()]['name'])
            elif modelIndex.column() == 1:  # params
                return str(self.functionList[modelIndex.row()]['param'])
            elif modelIndex.column() == 2:  # file
                return str(self.functionList[modelIndex.row()]['filename'])
        else:
            return QVariant()

    def headerData(self, section, orientation, role=None):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return ['Function Name', 'param:default', 'Package Name'][section]
        if orientation == Qt.Vertical:
            return [i + 1 for i in range(self.rows)][section]
        return QVariant()

    def flags(self, modelIndex):
        # flags = QAbstractTableModel.flags(self, modelIndex)
        flags = Qt.NoItemFlags
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        return flags

    def update(self):
        self.beginInsertRows(QModelIndex(), self.rows + 1, self.rows + len(self.functionList))
        self.rows += len(self.functionList)
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rows, self.cols))
        self.endInsertRows()
        if self.rows > 0:
            self.notEmpty.emit()


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
    update = pyqtSignal()

    def __init__(self, MLModel: ml_model, MLProject: ml_project, parent=None):
        super(ModelTabWidget, self).__init__(parent=parent)
        self.MLProject = MLProject
        self.MLModel = MLModel
        self.modelInfoDict = dict()
        self.modelParamDict = MLModel.param
        self.modelDataDict = dict()
        self.outLayout = QVBoxLayout(self)
        self.statusFrame = QFrame(self)
        self.statusLayout = QGridLayout(self)
        self.runButton = QPushButton('Run', self)
        self.stopButton = QPushButton('Stop', self)
        self.addButton = QPushButton('Add to queue', self)

        self.settingLayout = QHBoxLayout(self)
        self.modelInfo = QGroupBox(self)
        self.modelParam = QGroupBox(self)
        self.modelData = QGroupBox(self)

        self.modelInfoScroll = QScrollArea(self)
        self.modelParamScroll = QScrollArea(self)
        self.modelDataScroll = QScrollArea(self)

        self.modelInfoLayout = QFormLayout(self)
        self.modelParamStack = QStackedWidget(self)
        self.modelXGBParamLayout = QFormLayout(self)
        self.modelLGBMParamLayout = QFormLayout(self)
        self.modelDataLayout = QFormLayout(self)

        self.trainSet = QLabel(self)
        self.testSet = QLabel(self)
        # local
        self.metric = QComboBox(self)
        self.xgb_metric = ['rmse', 'auc', 'logloss', 'error']
        self.lightGBM_metric = ['', 'mean_absolute_error', 'mean_squared_error', 'root_mean_squared_error', 'quantile',
                                'None', 'auc', 'mean_average_precision', 'binary_logloss', 'binary_error',
                                'mean_absolute_percentage_error']
        self.sklearn_classification_metric = ['accuracy_score', 'auc', 'average_precision_score', 'brier_score_loss',
                                              'classification_report', 'cohen_kappa_score', 'confusion_matrix',
                                              'f1_score',
                                              'fbeta_score', 'hamming_loss', 'log_loss', 'precision_recall_curve',
                                              'precision_recall_fscore_support', 'precision_score', 'recall_score',
                                              'roc_auc_score',
                                              'roc_curve', 'zero_one_loss']
        self.sklearn_regression_metric = ['explained_variance_score', 'mean_absolute_error', 'mean_squared_error',
                                          'mean_squared_log_error', 'median_absolute_error', 'r2_score']
        self.metric_map = {'XGB': self.xgb_metric, 'LGBM': self.lightGBM_metric, 'RandomForest': None}

        self.initUI()
        self.initModelInfo()
        self.initData()
        self.infoQueue = Queue(10)

    def initUI(self):
        self.setLayout(self.outLayout)
        self.outLayout.addWidget(self.statusFrame)
        self.outLayout.addLayout(self.settingLayout)
        self.outLayout.setStretch(0, 1)
        self.outLayout.setStretch(1, 4)
        self.statusFrame.setLayout(self.statusLayout)
        self.statusLayout.addWidget(QLabel('Model Name: ' + self.MLModel.modelName), 0, 0)
        self.statusLayout.addWidget(QLabel('Model Status:'), 1, 0)
        self.statusLayout.addWidget(QLabel('Data: '), 0, 1)
        self.statusLayout.addWidget(self.trainSet, 1, 1)
        self.statusLayout.addWidget(self.testSet, 1, 2)
        self.statusLayout.addWidget(self.runButton, 0, 3)
        self.statusLayout.addWidget(self.stopButton, 1, 3)
        self.statusLayout.addWidget(self.addButton, 2, 3)

        self.statusLayout.setColumnStretch(0, 3)
        self.statusLayout.setColumnStretch(1, 3)
        self.statusLayout.setColumnStretch(2, 4)
        self.statusLayout.setColumnStretch(3, 2)

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
        self.initXGBParam()
        self.initLGBMParam()
        t = QWidget(self)
        t.setLayout(self.modelXGBParamLayout)
        self.modelParamStack.addWidget(t)
        t = QWidget(self)
        t.setLayout(self.modelLGBMParamLayout)
        self.modelParamStack.addWidget(t)
        self.modelParamScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.modelParamScroll.setWidget(self.modelParamStack)

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

        self.runButton.clicked.connect(self.runModel)
        self.stopButton.clicked.connect(self.stopModel)
        self.addButton.clicked.connect(self.add2Queue)

    def initModelInfo(self):
        self.modelInfoLayout.setContentsMargins(15, 20, 15, 10)
        algorithm = QComboBox(self)
        algorithm.addItems(
            ['XGB', 'LGBM', 'RandomForest', 'LinearReg', 'LogisticReg', 'Ridge', 'Lasso', 'ElasticNet'])  # G setting
        algorithm.currentTextChanged.connect(lambda: self.setMetricSet(self.metric_map[algorithm.currentText()]))
        algorithm.currentTextChanged.connect(lambda: self.MLModel.setModelType(algorithm.currentText()))
        algorithm.currentTextChanged.connect(lambda: self.modelParamStack.setCurrentIndex(algorithm.currentIndex()))
        self.modelInfoLayout.addRow('Algorithm: ', algorithm)

        if algorithm.currentText() == 'XGB':
            self.setMetricSet(self.xgb_metric)
            self.modelParamStack.setCurrentIndex(0)
        elif algorithm.currentText() == 'LGBM':
            self.setMetricSet(self.lightGBM_metric)
            self.modelParamStack.setCurrentIndex(1)
        elif algorithm.currentText() == 'RandomForest':
            self.setMetricSet(self.sklearn_classification_metric + self.sklearn_regression_metric)
        else:
            self.metric.currentText('N/A')
        self.modelInfoLayout.addRow('Metric: ', self.metric)
        self.metric.currentTextChanged.connect(lambda: self.MLModel.setMetric(self.metric.currentText()))

        kFold = QSpinBox(self)
        kFold.setRange(0, 10)
        kFold.setSingleStep(1)
        kFold.setValue(5)
        self.modelInfoLayout.addRow('kFold: ', kFold)
        kFold.valueChanged.connect(lambda: self.MLModel.setKFold(kFold.value()))

        resultFile = QLineEdit(self)
        resultFileCheck = QCheckBox(self)
        resultFileCheck.setText('not save result')
        resultFile.setText('model.result')
        self.modelInfoLayout.addRow('result file: ', resultFile)
        self.modelInfoLayout.addRow('', resultFileCheck)
        resultFileCheck.stateChanged.connect(lambda: resultFile.setDisabled(resultFileCheck.checkState()))

    def initXGBParam(self):
        self.modelXGBParamLayout.setContentsMargins(15, 20, 15, 10)
        objective = QComboBox(self)
        objective.addItems(
            ['reg:linear', 'reg:logistic', 'binary:logistic', 'binary:logitraw', 'count:poisson', 'reg:gamma'])
        self.modelXGBParamLayout.addRow('objective: ', objective)
        objective.currentTextChanged.connect(lambda: self.setParam('objective', objective.currentText()))

        learning_rate = QDoubleSpinBox(self)
        learning_rate.setRange(0, 1)
        learning_rate.setValue(self.modelParamDict['eta'])
        learning_rate.setSingleStep(0.01)
        learning_rate.setDecimals(3)
        learning_rate.valueChanged.connect(lambda: self.setParam('learning_rate', learning_rate.value()))
        self.modelXGBParamLayout.addRow('learning_rate: ', learning_rate)

        gamma = QDoubleSpinBox(self)
        gamma.setMinimum(0)
        gamma.setSingleStep(0.1)
        gamma.setDecimals(3)
        gamma.setValue(self.modelParamDict['gamma'])
        gamma.valueChanged.connect(lambda: self.setParam('gamma', gamma.value()))
        self.modelXGBParamLayout.addRow('gamma: ', gamma)

        max_depth = QSpinBox(self)
        max_depth.setMinimum(0)
        max_depth.setValue(self.modelParamDict['max_depth'])
        max_depth.valueChanged.connect(lambda: self.setParam('max_depth', max_depth.value()))
        self.modelXGBParamLayout.addRow('max_depth: ', max_depth)

        min_child_weight = QDoubleSpinBox(self)
        min_child_weight.setMinimum(0)
        min_child_weight.setSingleStep(0.1)
        min_child_weight.setDecimals(3)
        min_child_weight.setValue(self.modelParamDict['min_child_weight'])
        min_child_weight.valueChanged.connect(lambda: self.setParam('min_child_weight', min_child_weight.value()))
        self.modelXGBParamLayout.addRow('min_child_weight: ', min_child_weight)

        max_delta_step = QDoubleSpinBox(self)
        max_delta_step.setMinimum(0)
        max_delta_step.setSingleStep(0.1)
        max_delta_step.setDecimals(3)
        max_delta_step.setValue(self.modelParamDict['max_delta_step'])
        max_delta_step.valueChanged.connect(lambda: self.setParam('max_delta_step', max_delta_step.value()))
        self.modelXGBParamLayout.addRow('max_delta_step: ', max_delta_step)

        subsample = QDoubleSpinBox(self)
        subsample.setMinimum(0.01)
        subsample.setSingleStep(0.1)
        subsample.setDecimals(3)
        subsample.setValue(self.modelParamDict['subsample'])
        subsample.valueChanged.connect(lambda: self.setParam('subsample', subsample.value()))
        self.modelXGBParamLayout.addRow('subsample: ', subsample)

        colsample_bytree = QDoubleSpinBox(self)
        colsample_bytree.setMinimum(0.01)
        colsample_bytree.setSingleStep(0.1)
        colsample_bytree.setDecimals(3)
        colsample_bytree.setValue(self.modelParamDict['colsample_bytree'])
        colsample_bytree.valueChanged.connect(lambda: self.setParam('colsample_bytree', colsample_bytree.value()))
        self.modelXGBParamLayout.addRow('colsample_bytree: ', colsample_bytree)

        colsample_bylevel = QDoubleSpinBox(self)
        colsample_bylevel.setMinimum(0.01)
        colsample_bylevel.setSingleStep(0.1)
        colsample_bylevel.setDecimals(3)
        colsample_bylevel.setValue(self.modelParamDict['colsample_bylevel'])
        colsample_bylevel.valueChanged.connect(lambda: self.setParam('colsample_bylevel', colsample_bylevel.value()))
        self.modelXGBParamLayout.addRow('colsample_bylevel: ', colsample_bylevel)

        reg_lambda = QDoubleSpinBox(self)
        reg_lambda.setMinimum(0)
        reg_lambda.setSingleStep(0.1)
        reg_lambda.setDecimals(3)
        reg_lambda.setValue(self.modelParamDict['reg_lambda'])
        reg_lambda.valueChanged.connect(lambda: self.setParam('reg_lambda', reg_lambda.value()))
        self.modelXGBParamLayout.addRow('reg_lambda: ', reg_lambda)

        reg_alpha = QDoubleSpinBox(self)
        reg_alpha.setMinimum(0)
        reg_alpha.setSingleStep(0.1)
        reg_alpha.setDecimals(3)
        reg_alpha.setValue(self.modelParamDict['reg_alpha'])
        reg_alpha.valueChanged.connect(lambda: self.setParam('reg_alpha', reg_alpha.value()))
        self.modelXGBParamLayout.addRow('reg_alpha: ', reg_alpha)

        tree_method = QComboBox(self)
        tree_method.addItems(['auto', 'exact', 'approx', 'hist', 'gpu_exact', 'gpu_hist'])
        tree_method.setCurrentText(self.modelParamDict['tree_method'])
        tree_method.currentTextChanged.connect(lambda: self.setParam('tree_method', tree_method.currentText()))
        self.modelXGBParamLayout.addRow('tree_method: ', tree_method)

        scale_pos_weight = QDoubleSpinBox(self)
        scale_pos_weight.setMinimum(0)
        scale_pos_weight.setSingleStep(0.1)
        scale_pos_weight.setDecimals(3)
        scale_pos_weight.setValue(self.modelParamDict['scale_pos_weight'])
        scale_pos_weight.valueChanged.connect(lambda: self.setParam('scale_pos_weight', scale_pos_weight.value()))
        self.modelXGBParamLayout.addRow('scale_pos_weight: ', scale_pos_weight)

        predictor = QComboBox(self)
        predictor.addItems(['cpu_predictor', 'gpu_predictor'])
        predictor.currentTextChanged.connect(lambda: self.setParam('predictor', predictor.currentText()))
        self.modelXGBParamLayout.addRow('predictor: ', predictor)

    def initLGBMParam(self):
        self.modelLGBMParamLayout.setContentsMargins(15, 20, 15, 10)

        boosting = QComboBox(self)
        boosting.addItems(
            ['gbdt', 'gbrt', 'rf', 'random_forest', 'dart', 'goss'])
        self.modelLGBMParamLayout.addRow('boosting: ', boosting)
        boosting.currentTextChanged.connect(lambda: self.setParam('boosting', boosting.currentText()))

        max_depth = QSpinBox(self)
        max_depth.setValue(-1)
        max_depth.setMinimum(-1)
        max_depth.setSingleStep(1)
        max_depth.valueChanged.connect(lambda: self.setParam('max_depth', max_depth.value()))
        self.modelLGBMParamLayout.addRow('max_depth: ', max_depth)

        min_data_in_leaf = QSpinBox(self)
        min_data_in_leaf.setValue(20)
        min_data_in_leaf.setMinimum(0)
        min_data_in_leaf.setSingleStep(1)
        min_data_in_leaf.valueChanged.connect(lambda: self.setParam('min_data_in_leaf', min_data_in_leaf.value()))
        self.modelLGBMParamLayout.addRow('min_data_in_leaf: ', min_data_in_leaf)

        min_sum_hessian_in_leaf = QDoubleSpinBox(self)
        min_sum_hessian_in_leaf.setValue(1e-3)
        min_sum_hessian_in_leaf.setMinimum(0)
        min_sum_hessian_in_leaf.setSingleStep(1e-2)
        min_sum_hessian_in_leaf.setDecimals(3)
        min_sum_hessian_in_leaf.valueChanged.connect(
            lambda: self.setParam('min_sum_hessian_in_leaf', min_sum_hessian_in_leaf.value()))
        self.modelLGBMParamLayout.addRow('min_sum_hessian_in_leaf: ', min_sum_hessian_in_leaf)

        subsample = QDoubleSpinBox(self)
        subsample.setValue(1.0)
        subsample.setRange(1e-6, 1)
        subsample.setSingleStep(1e-2)
        subsample.setDecimals(3)
        subsample.valueChanged.connect(lambda: self.setParam('subsample', subsample.value()))
        self.modelLGBMParamLayout.addRow('subsample: ', subsample)

        subsample_freq = QSpinBox(self)
        subsample_freq.setValue(0)
        subsample_freq.setMinimum(0)
        subsample_freq.setSingleStep(1)
        subsample_freq.valueChanged.connect(lambda: self.setParam('subsample_freq', subsample_freq.value()))
        self.modelLGBMParamLayout.addRow('subsample_freq: ', subsample_freq)

        feature_fraction = QDoubleSpinBox(self)
        feature_fraction.setValue(1.0)
        feature_fraction.setRange(1e-6, 1)
        feature_fraction.setSingleStep(1e-2)
        feature_fraction.setDecimals(3)
        feature_fraction.valueChanged.connect(lambda: self.setParam('feature_fraction', feature_fraction.value()))
        self.modelLGBMParamLayout.addRow('feature_fraction: ', feature_fraction)

        early_stopping_round = QSpinBox(self)
        early_stopping_round.setValue(0)
        early_stopping_round.setMinimum(0)
        early_stopping_round.setSingleStep(1)
        early_stopping_round.valueChanged.connect(
            lambda: self.setParam('early_stopping_round', early_stopping_round.value()))
        self.modelLGBMParamLayout.addRow('early_stopping_round: ', early_stopping_round)

        max_delta_step = QDoubleSpinBox(self)  # used to limit the max output of tree leaves
        max_delta_step.setValue(0)  # final max output of leaves is learning_rate * max_delta_step
        max_delta_step.setMinimum(0)
        max_delta_step.setSingleStep(1e-2)
        max_delta_step.setDecimals(3)
        max_delta_step.valueChanged.connect(lambda: self.setParam('max_delta_step', max_delta_step.value()))
        self.modelLGBMParamLayout.addRow('max_delta_step: ', max_delta_step)

        reg_alpha = QDoubleSpinBox(self)
        reg_alpha.setValue(0)
        reg_alpha.setMinimum(0)
        reg_alpha.setSingleStep(1e-2)
        reg_alpha.setDecimals(3)
        reg_alpha.valueChanged.connect(lambda: self.setParam('reg_alpha', reg_alpha.value()))
        self.modelLGBMParamLayout.addRow('reg_alpha: ', reg_alpha)

        reg_lambda = QDoubleSpinBox(self)
        reg_lambda.setValue(0)
        reg_lambda.setMinimum(0)
        reg_lambda.setSingleStep(1e-2)
        reg_lambda.setDecimals(3)
        reg_lambda.valueChanged.connect(lambda: self.setParam('reg_lambda', reg_lambda.value()))
        self.modelLGBMParamLayout.addRow('reg_lambda: ', reg_lambda)

        min_split_gain = QDoubleSpinBox(self)
        min_split_gain.setValue(0)
        min_split_gain.setMinimum(0)
        min_split_gain.setSingleStep(1e-2)
        min_split_gain.setDecimals(3)
        min_split_gain.valueChanged.connect(lambda: self.setParam('min_split_gain', min_split_gain.value()))
        self.modelLGBMParamLayout.addRow('min_split_gain: ', min_split_gain)

        drop_rate = QDoubleSpinBox(self)  # used only in dart
        drop_rate.setValue(0.1)
        drop_rate.setRange(0, 1)
        drop_rate.setSingleStep(1e-2)
        drop_rate.setDecimals(3)
        drop_rate.valueChanged.connect(lambda: self.setParam('drop_rate', drop_rate.value()))
        self.modelLGBMParamLayout.addRow('drop_rate: ', drop_rate)

        max_drop = QSpinBox(self)  # used only in dart
        max_drop.setValue(50)
        max_drop.setMinimum(0)
        max_drop.setSingleStep(5)
        max_drop.valueChanged.connect(lambda: self.setParam('max_drop', max_drop.value()))
        self.modelLGBMParamLayout.addRow('max_drop: ', max_drop)

    def initData(self):
        self.modelDataLayout.setContentsMargins(10, 20, 10, 10)
        trainSetCombo = QComboBox(self)
        trainSetCombo.addItems(self.MLProject.dataFiles_pkl)
        trainSetCombo.addItems(self.MLProject.dataFiles_csv)
        self.modelDataLayout.addRow('Train: ', trainSetCombo)
        trainSetCombo.setCurrentIndex(trainSetCombo.findText(self.MLModel.trainSet))
        trainSetCombo.currentTextChanged.connect(lambda: self.MLModel.setTrainSet(trainSetCombo.currentText()))

        testSetCombo = QComboBox(self)
        testSetCombo.addItems(self.MLProject.dataFiles_pkl)
        testSetCombo.addItems(self.MLProject.dataFiles_csv)
        self.modelDataLayout.addRow('Test: ', testSetCombo)
        testSetCombo.setCurrentIndex(testSetCombo.findText(self.MLModel.testSet))
        testSetCombo.currentTextChanged.connect(lambda: self.MLModel.setTestSet(testSetCombo.currentText()))
        # load data button
        loadDataButton = QPushButton('Load data', self)
        self.modelDataLayout.addRow(loadDataButton)
        # data ID
        self.data_ID = QComboBox(self)
        self.data_ID.setEditable(True)
        self.data_ID.setEnabled(False)
        self.modelDataLayout.addRow('ID:', self.data_ID)
        # data target
        self.data_target = QComboBox(self)
        self.data_target.setEditable(True)
        self.data_target.setEnabled(False)
        self.modelDataLayout.addRow('Target:', self.data_target)

        loadDataButton.clicked.connect(lambda: self.loadData())
        self.data_ID.currentTextChanged.connect(lambda: self.MLModel.setID(self.data_ID.currentText()))
        self.data_target.currentTextChanged.connect(lambda: self.MLModel.setTarget(self.data_target.currentText()))
        loadDataButton.clicked.connect(lambda: self.data_ID.setEnabled(True))
        loadDataButton.clicked.connect(lambda: self.data_target.setEnabled(True))
        loadDataButton.clicked.connect(lambda: self.trainSet.setText(trainSetCombo.currentText()))
        loadDataButton.clicked.connect(lambda: self.testSet.setText(testSetCombo.currentText()))
        self.outputEditor = QTextEdit(self)
        self.modelDataLayout.addRow('', self.outputEditor)

    def loadData(self):
        # load train set
        if self.MLModel.trainSet.endswith('csv'):
            train = pd.read_csv(self.MLModel.trainSet)
        elif self.MLModel.trainSet.endswith('pkl'):
            train = pd.read_pickle(self.MLModel.trainSet)
        # set train list
        id = self.MLModel.ID
        target = self.MLModel.target
        self.data_ID.addItems(train.columns.tolist())
        self.data_target.addItems(train.columns.tolist())
        self.data_ID.setCurrentText(id)
        self.data_target.setCurrentText(target)

    def setParam(self, key, value):
        self.MLModel.param[key] = value
        self.modelParamDict[key] = value
        self.MLModel.update()

    def setMetricSet(self, metrics):
        self.metric.clear()
        if metrics:
            self.metric.addItems(metrics)
        else:
            self.metric.addItems(self.sklearn_regression_metric + self.sklearn_classification_metric)

    def runModel(self):
        self.update.emit()
        model = None
        if self.MLModel.modelType == 'XGB':
            model = xgbModel(self.infoQueue, self.MLModel, 2000, kFold=5)
        # self.MLModel.setCurrentModel(model)
        # create process to run model
        model.start()

        self.my_receiver = MyReceiver(self.infoQueue, model)
        self.my_receiver.mysignal.connect(self.append_text)
        self.my_receiver.start()

    def stopModel(self):
        self.update.emit()

    def add2Queue(self):
        self.update.emit()

    def append_text(self, text):
        self.outputEditor.moveCursor(QTextCursor.End)
        self.outputEditor.insertPlainText(text)

    def closeEvent(self, QCloseEvent):
        self.update.emit()


class ImageDataTabWidget(QWidget):
    Horizontal = 0
    Vertical = 1

    def __init__(self, imageDir):
        super(ImageDataTabWidget, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.mainLayout = QHBoxLayout(self)
        self.mainSplitter = QSplitter(Qt.Horizontal)
        self.toolsetTab = CollapsibleTabWidget(self.Vertical, self)
        self.toolset = QToolBox(self)
        self.mainTabWidget = QTabWidget(self)
        self.imageViewer = ImageViewer(imageDir, self)
        self.initUI()

    def initUI(self):
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.mainSplitter)
        self.toolsetTab.addTab(self.toolset, 'toolSet')
        self.toolsetTab.addTab(QTextEdit(self), 'test2')

        self.mainSplitter.addWidget(self.toolsetTab)
        self.mainSplitter.addWidget(self.mainTabWidget)
        self.mainSplitter.setStretchFactor(0, 1)
        self.mainSplitter.setStretchFactor(1, 35)
        self.mainSplitter.setCollapsible(0, False)
        self.mainSplitter.setCollapsible(1, False)
        self.toolsetTab.setSplitter(self.mainSplitter)
        #
        self.mainTabWidget.addTab(self.imageViewer, 'Image Viewer')


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


class MyReceiver(QThread):
    mysignal = pyqtSignal(str)

    def __init__(self, queue, model):
        super(MyReceiver, self).__init__()
        self.queue = queue
        self.model = model

    def run(self):
        while self.model.is_alive():
            while not self.queue.empty():
                text = self.queue.get()
                self.mysignal.emit(text)
        print('process end')


class customAction(QAction):
    myClicked = pyqtSignal(QPoint)

    def __init__(self, point: QPoint):
        super(customAction, self).__init__()
        self.point = point

    def clicked(self):
        self.myClicked.emit(self.point)


class functionManagerDialog(QDialog):
    def __init__(self, parent):
        super(functionManagerDialog, self).__init__(parent=parent)
        self.MLProject = GENERAL.get_value('PROJECT')
        self.functionList = self.MLProject.functionList
        self.mainLayout = QVBoxLayout(self)
        self.toolBar = QToolBar(self)
        self.mainList = QTableView(self)
        self.tableModel = functionModel(self)
        # local data
        self.importList = None
        self.funcInfoList = None
        # tools
        self.importButton = QAction(QIcon('./res/Open.ico'), 'Import', self)
        self.initUI()

    def initUI(self):
        self.setMinimumSize(600, 400)
        # init tool bar
        self.importButton.triggered.connect(lambda: self.addFuncDialog())
        self.toolBar.addActions([self.importButton])

        self.mainLayout.addWidget(self.toolBar)
        self.mainLayout.addWidget(self.mainList)

        self.mainList.setEditTriggers(QTableView.NoEditTriggers)
        self.mainList.setSelectionBehavior(QTableView.SelectRows)
        self.mainList.setSelectionMode(QTableView.SingleSelection)
        self.mainList.setFocusPolicy(Qt.NoFocus)
        self.mainList.setModel(self.tableModel)
        self.mainList.autoScrollMargin()
        self.tableModel.notEmpty.connect(lambda: self.setTableHeaderStyle())
        self.tableModel.loadFuncList(self.functionList)

    def addFuncDialog(self):
        dialog = QFileDialog()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileTypes = "Python File (*.py)"
        if os.path.exists(os.path.join(self.MLProject.projectDir, self.MLProject.scriptDir)):
            dialog.setDirectory(os.path.join(self.MLProject.projectDir, self.MLProject.scriptDir))
        else:
            dialog.setDirectory(self.MLProject.projectDir)
        importedFile, _ = dialog.getOpenFileNames(self, "Import Function File", "", fileTypes,
                                                  options=options)  # return list
        packageInfo = self.importFromPy(importedFile[0])
        self.addPackage(packageInfo)

    def importFromPy(self, importedFile):
        # parse python file by string
        # get function name and params
        fileName = os.path.basename(importedFile)
        with open(importedFile, 'r') as f:
            packageInfo = dict()
            packageList = list()
            funcList = list()
            lines = f.readlines()
            # get import list
            for l in lines:
                if l.startswith('import '):
                    packageList.append(l.split()[1])
                elif l.startswith('def '):
                    funcInfo = dict()
                    funcName = l[4:l.find('(')]
                    argumentList = l[l.find('(') + 1:l.find(')')]
                    argumentList = [i.strip() for i in argumentList.split(',')]
                    param = dict()
                    for a in argumentList:
                        if '=' in a:
                            paramLine = [i.strip() for i in a.split('=')]
                            paramName = paramLine[0]
                            default = paramLine[1]
                        else:
                            paramName = a
                            default = None
                        param[paramName] = default
                    funcInfo['name'] = funcName
                    funcInfo['param'] = param
                    funcInfo['param_count'] = len(param)
                    funcInfo['filename'] = fileName
                    funcInfo['dependent'] = packageList
                    funcList.append(funcInfo)

            packageInfo['packageName'] = fileName
            packageInfo['funcList'] = funcList
            packageInfo['packageList'] = packageList
        return packageInfo

    def addPackage(self, packageInfo):
        funcList = packageInfo['funcList']
        for f in funcList:
            self.functionList.append(f)
            self.tableModel.update()
        self.MLProject.functionList = self.functionList
        GENERAL.set_value('PROJECT', self.MLProject)

    def setTableHeaderStyle(self):
        self.mainList.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.mainList.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
