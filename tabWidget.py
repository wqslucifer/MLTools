import os
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QListWidget, QToolBox, \
    QTabWidget, QTextEdit, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QSpinBox, \
    QDoubleSpinBox, QFrame, QSizePolicy, QHeaderView, QTableView, QApplication, QScrollArea, QScrollBar, QSplitter, \
    QSplitterHandle, QComboBox, QGroupBox, QFormLayout, QCheckBox, QMenu, QAction, QWidgetAction
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, QSettings, QTimer, QUrl, QDir, \
    QAbstractTableModel, QEvent, QObject, QModelIndex, QVariant, QThread, QObject
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath, QStandardItemModel, QTextCursor, \
    QCursor
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from customWidget import CollapsibleTabWidget
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

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns

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
        self.tableModel = customTableModel(self)
        self.dataExplorer.setModel(self.tableModel)
        self.statistic = QTableWidget(self)

        self.mainTab = QTabWidget(self)
        self.outputTab = QTabWidget(self)
        self.outputEdit = QTextEdit(self)
        # init UI
        self.initUI()
        self.initStatistic()
        # right click menu
        self.dataExplorer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dataExplorer.customContextMenuRequested.connect(self.onDataExplorerRightClicked)
        self.dataExplorerPopMenu = QMenu(self)
        # plot tab setting
        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        self.plotLayout = FlowLayout()
        plotWidget = QWidget(self)
        plotWidget.setLayout(self.plotLayout)
        scrollArea.setWidget(plotWidget)
        self.mainTab.addTab(scrollArea, 'plot')
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
            meta.columns = ['index','meta']
        else:
            meta = self.dataFrame.iloc[:, index.column()].dropna()
            meta_index = meta.index
            meta = pd.DataFrame([meta_index, meta]).transpose()
            meta.columns = ['index','meta']

        # create plot
        fig = Figure(figsize=(5, 4))
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
        fig = Figure(figsize=(5, 4))
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
        fig = Figure(figsize=(5, 4))
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
        fig = Figure(figsize=(5, 4))
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
        fig = Figure(figsize=(6, 5))
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
        fig = Figure(figsize=(6, 6))
        fig.set_tight_layout(True)
        canvas = FigureCanvas(fig)
        ax = fig.subplots()
        # set color
        # sns.set(palette="muted", color_codes=True)
        sns.set(style="whitegrid")
        # plot
        if len(X):
            Y1 = np.sum(self.dataFrame[X].isnull())
            Y2 = Y1 * 0 + self.dataFrame.shape[0]
            sns.set_color_codes("pastel")
            sns.barplot(x=Y2, y=X, ax=ax, color="b")
            sns.set_color_codes("muted")
            plot = sns.barplot(x=Y1, y=X, ax=ax, color="r")
            labels = ax.get_xticks()
            plot.set_xticklabels(labels, rotation=45)
            labels = plot.get_yticklabels()
            plot.set_yticklabels(labels, rotation=50)

            sns.set_palette(sns.cubehelix_palette(8))
            ax.axvline(self.dataFrame.shape[0] * 0.8, color='#856798', clip_on=False)

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
        if filename.endswith('csv'):
            self.dataFrame = pd.read_csv(filename)
        elif filename.endswith('pkl'):
            self.dataFrame = pd.read_pickle(filename)
        # init table
        self.dataExplorer.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.dataExplorer.verticalHeader().setFixedWidth(self.verticalHeaderWidth)
        self.tableModel.loadCSV(self.dataFrame)

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

        dataExplorerActionList = [a1, a2, a3, a4]
        numericMenu.addActions(dataExplorerActionList)
        self.dataExplorerPopMenu.addMenu(numericMenu)

        # category
        categoryMenu = QMenu('Category', self)
        b1 = QAction('count plot', self)
        b1.triggered.connect(lambda: self.countPlot(point))

        dataExplorerActionList = [b1]
        categoryMenu.addActions(dataExplorerActionList)
        self.dataExplorerPopMenu.addMenu(categoryMenu)

        # test action
        test = QAction('test plot', self)
        test.triggered.connect(lambda: self.nanPlot(point))
        self.dataExplorerPopMenu.addAction(test)
        # pop menu
        self.dataExplorerPopMenu.exec(QCursor.pos())


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
        self.modelInfoDict = dict()
        self.modelParamDict = MLModel.param
        self.modelDataDict = dict()
        self.outLayout = QVBoxLayout(self)
        self.statusFrame = QFrame(self)
        self.statusLayout = QGridLayout(self)
        self.runButton = QPushButton('Run', self)
        self.stopButton = QPushButton('Stop', self)
        self.addButton = QPushButton('Add', self)

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
        self.initXGBParam()
        self.initData()
        self.infoQueue = Queue(10)

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

        self.runButton.clicked.connect(self.runModel)

    def initModelInfo(self):
        self.modelInfoLayout.setContentsMargins(15, 20, 15, 10)
        algorithm = QComboBox(self)
        algorithm.addItems(
            ['XGB', 'LGBM', 'RandomForest', 'LinearReg', 'LogisticReg', 'Ridge', 'Lasso', 'ElasticNet'])  # G setting
        algorithm.currentTextChanged.connect(lambda: self.setMetricSet(self.metric_map[algorithm.currentText()]))
        algorithm.currentTextChanged.connect(lambda: self.MLModel.setModelType(algorithm.currentText()))
        self.modelInfoLayout.addRow('Algorithm: ', algorithm)

        if algorithm.currentText() == 'XGB':
            self.setMetricSet(self.xgb_metric)
        elif algorithm.currentText() == 'LGBM':
            self.setMetricSet(self.lightGBM_metric)
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
        self.modelParamLayout.setContentsMargins(15, 20, 15, 10)
        objective = QComboBox(self)
        objective.addItems(
            ['reg:linear', 'reg:logistic', 'binary:logistic', 'binary:logitraw', 'count:poisson', 'reg:gamma'])
        self.modelParamLayout.addRow('objective: ', objective)
        objective.currentTextChanged.connect(lambda: self.setParam('objective', objective.currentText()))

        learning_rate = QDoubleSpinBox(self)
        learning_rate.setRange(0, 1)
        learning_rate.setValue(self.modelParamDict['eta'])
        learning_rate.setSingleStep(0.01)
        learning_rate.valueChanged.connect(lambda: self.setParam('learning_rate', learning_rate.value()))
        self.modelParamLayout.addRow('learning_rate: ', learning_rate)

        gamma = QDoubleSpinBox(self)
        gamma.setMinimum(0)
        gamma.setSingleStep(0.1)
        gamma.setValue(self.modelParamDict['gamma'])
        gamma.valueChanged.connect(lambda: self.setParam('gamma', gamma.value()))
        self.modelParamLayout.addRow('gamma: ', gamma)

        max_depth = QSpinBox(self)
        max_depth.setMinimum(0)
        max_depth.setValue(self.modelParamDict['max_depth'])
        max_depth.valueChanged.connect(lambda: self.setParam('max_depth', max_depth.value()))
        self.modelParamLayout.addRow('max_depth: ', max_depth)

        min_child_weight = QDoubleSpinBox(self)
        min_child_weight.setMinimum(0)
        min_child_weight.setSingleStep(0.1)
        min_child_weight.setValue(self.modelParamDict['min_child_weight'])
        min_child_weight.valueChanged.connect(lambda: self.setParam('min_child_weight', min_child_weight.value()))
        self.modelParamLayout.addRow('min_child_weight: ', min_child_weight)

        max_delta_step = QDoubleSpinBox(self)
        max_delta_step.setMinimum(0)
        max_delta_step.setSingleStep(0.1)
        max_delta_step.setValue(self.modelParamDict['max_delta_step'])
        max_delta_step.valueChanged.connect(lambda: self.setParam('max_delta_step', max_delta_step.value()))
        self.modelParamLayout.addRow('max_delta_step: ', max_delta_step)

        subsample = QDoubleSpinBox(self)
        subsample.setMinimum(0.01)
        subsample.setSingleStep(0.1)
        subsample.setValue(self.modelParamDict['subsample'])
        subsample.valueChanged.connect(lambda: self.setParam('subsample', subsample.value()))
        self.modelParamLayout.addRow('subsample: ', subsample)

        colsample_bytree = QDoubleSpinBox(self)
        colsample_bytree.setMinimum(0.01)
        colsample_bytree.setSingleStep(0.1)
        colsample_bytree.setValue(self.modelParamDict['colsample_bytree'])
        colsample_bytree.valueChanged.connect(lambda: self.setParam('colsample_bytree', colsample_bytree.value()))
        self.modelParamLayout.addRow('colsample_bytree: ', colsample_bytree)

        colsample_bylevel = QDoubleSpinBox(self)
        colsample_bylevel.setMinimum(0.01)
        colsample_bylevel.setSingleStep(0.1)
        colsample_bylevel.setValue(self.modelParamDict['colsample_bylevel'])
        colsample_bylevel.valueChanged.connect(lambda: self.setParam('colsample_bylevel', colsample_bylevel.value()))
        self.modelParamLayout.addRow('colsample_bylevel: ', colsample_bylevel)

        reg_lambda = QDoubleSpinBox(self)
        reg_lambda.setMinimum(0)
        reg_lambda.setSingleStep(0.1)
        reg_lambda.setValue(self.modelParamDict['reg_lambda'])
        reg_lambda.valueChanged.connect(lambda: self.setParam('reg_lambda', reg_lambda.value()))
        self.modelParamLayout.addRow('reg_lambda: ', reg_lambda)

        reg_alpha = QDoubleSpinBox(self)
        reg_alpha.setMinimum(0)
        reg_alpha.setSingleStep(0.1)
        reg_alpha.setValue(self.modelParamDict['reg_alpha'])
        reg_alpha.valueChanged.connect(lambda: self.setParam('reg_alpha', reg_alpha.value()))
        self.modelParamLayout.addRow('reg_alpha: ', reg_alpha)

        tree_method = QComboBox(self)
        tree_method.addItems(['auto', 'exact', 'approx', 'hist', 'gpu_exact', 'gpu_hist'])
        tree_method.setCurrentText(self.modelParamDict['tree_method'])
        tree_method.currentTextChanged.connect(lambda: self.setParam('tree_method', tree_method.currentText()))
        self.modelParamLayout.addRow('tree_method: ', tree_method)

        scale_pos_weight = QDoubleSpinBox(self)
        scale_pos_weight.setMinimum(0)
        scale_pos_weight.setSingleStep(0.1)
        scale_pos_weight.setValue(self.modelParamDict['scale_pos_weight'])
        scale_pos_weight.valueChanged.connect(lambda: self.setParam('scale_pos_weight', scale_pos_weight.value()))
        self.modelParamLayout.addRow('scale_pos_weight: ', scale_pos_weight)

        predictor = QComboBox(self)
        predictor.addItems(['cpu_predictor', 'gpu_predictor'])
        predictor.currentTextChanged.connect(lambda: self.setParam('predictor', predictor.currentText()))
        self.modelParamLayout.addRow('predictor: ', predictor)

    def initData(self):
        self.modelDataLayout.setContentsMargins(10, 20, 10, 10)
        trainSet = QComboBox(self)
        trainSet.addItems(self.MLProject.dataFiles_pkl)
        trainSet.addItems(self.MLProject.dataFiles_csv)
        self.modelDataLayout.addRow('Train: ', trainSet)
        trainSet.setCurrentText(os.path.basename(self.MLModel.trainSet))
        trainSet.currentTextChanged.connect(lambda: self.MLModel.setTrainSet(trainSet.currentText()))

        testSet = QComboBox(self)
        testSet.addItems(self.MLProject.dataFiles_pkl)
        testSet.addItems(self.MLProject.dataFiles_csv)
        self.modelDataLayout.addRow('Test: ', testSet)
        testSet.setCurrentText(os.path.basename(self.MLModel.testSet))
        testSet.currentTextChanged.connect(lambda: self.MLModel.setTestSet(testSet.currentText()))
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

        loadDataButton.clicked.connect(lambda: self.data_ID.setEnabled(True))
        loadDataButton.clicked.connect(lambda: self.data_target.setEnabled(True))
        loadDataButton.clicked.connect(lambda: self.loadData())
        self.data_ID.currentTextChanged.connect(lambda: self.MLModel.setID(self.data_ID.currentText()))
        self.data_target.currentTextChanged.connect(lambda: self.MLModel.setTarget(self.data_target.currentText()))

        self.outputEditor = QTextEdit(self)
        self.modelDataLayout.addRow('', self.outputEditor)

    def loadData(self):
        # load train set
        if self.MLModel.trainSet.endswith('csv'):
            train = pd.read_csv(self.MLModel.trainSet)
        elif self.MLModel.trainSet.endswith('pkl'):
            train = pd.read_pickle(self.MLModel.trainSet)
        # set train list
        self.data_ID.addItems(train.columns.tolist())
        self.data_target.addItems(train.columns.tolist())

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
        pass

    def append_text(self, text):
        self.outputEditor.moveCursor(QTextCursor.End)
        self.outputEditor.insertPlainText(text)


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


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
