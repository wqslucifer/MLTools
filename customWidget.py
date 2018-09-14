import os
import sys
import gc
import time
import pandas as pd
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QApplication, QTabWidget, \
    QTabBar, QToolBar, QPushButton, QVBoxLayout, QTreeWidget, QSizePolicy, QAction, QStackedWidget, QListWidget, \
    QScrollBar, QScrollArea, QTextEdit, QTreeView, QTreeWidgetItem, QSplitter, QStylePainter, QStyle, \
    QStyleOptionButton, QTableView, QListWidgetItem, QProgressBar
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal, QTimer, QThread, QSortFilterProxyModel, \
    QModelIndex, QAbstractItemModel, QObject, QMimeData, QAbstractTableModel, QVariant
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath, QStandardItem, QIcon, \
    QMouseEvent, QStandardItemModel, QPaintEvent, QImage, QPixmap, QDrag, QDragEnterEvent, QDragMoveEvent, QTextOption, \
    QDropEvent

from PyQt5.QtQuick import QQuickView, QQuickItem
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.QtCore import QUrl, pyqtSlot
from PyQt5.QtGui import QGuiApplication
from PyQt5 import QtGui
from customLayout import FlowLayout
from process import processQueue, QtReceiver

from model import ml_model, modelResult
import GENERAL


# widgets for main window tabs
class ModelWidget(QWidget):
    # signal
    triggered = pyqtSignal(ml_model)

    def __init__(self, modelFile):
        super(ModelWidget, self).__init__()
        self.setFixedSize(180, 180)
        self.mainLayout = QGridLayout(self)
        self.edge = None
        self.bgColor = None
        self.labelFont = QFont("Arial", 10, QFont.Times)
        self.MLModel = ml_model.loadModel(modelFile)
        # model name
        self.modelName = QLabel(self.MLModel.modelName)
        self.modelName.setFont(QFont("Arial", 11, QFont.Bold))
        # model type
        self.modelTypeLabel = QLabel('Type:' + self.MLModel.modelType, self)
        self.modelTypeLabel.setFont(QFont("Arial", 11, QFont.Times))
        # model describe
        self.modelDescribeLabel = QLabel("Describe:")
        # local eval
        self.evalMetric = QLabel((self.MLModel.metric if self.MLModel.metric is not '' else 'Default Metric') + ': ',
                                 self)
        self.evalScore = QLabel(str(self.MLModel.localScore))
        # data set
        self.trainSet = QLabel('trainSet: ' + os.path.basename(self.MLModel.trainSet), self)
        self.testSet = QLabel('testSet: ' + os.path.basename(self.MLModel.testSet), self)

        # LB eval score
        self.leaderBoardLabel = QLabel("LB: ")
        self.LBScore = QLabel(str(self.MLModel.LBScore), self)
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(18, 18, 0, 0)
        self.mainLayout.addWidget(self.modelName, 0, 0, Qt.AlignTop)
        self.mainLayout.addWidget(self.modelTypeLabel, 1, 0, Qt.AlignTop)
        # local cv item
        evalLayout = self.createNewHLayout(self.evalMetric, self.evalScore, self.labelFont)
        self.mainLayout.addLayout(evalLayout, 2, 0)
        # LB item
        LBLayout = self.createNewHLayout(self.leaderBoardLabel, self.LBScore, self.labelFont)
        LBLayout.setSpacing(16)
        self.mainLayout.addLayout(LBLayout, 3, 0)
        # data set label
        self.mainLayout.addWidget(self.trainSet, 4, 0)
        self.mainLayout.addWidget(self.testSet, 5, 0)
        # describe label
        self.mainLayout.addWidget(self.modelDescribeLabel, 6, 0, Qt.AlignTop)

        self.mainLayout.setRowStretch(0, 1)
        self.mainLayout.setRowStretch(7, 20)
        self.bgColor = QColor('#FFA779')
        self.edge = QRectF(5, 5, 170, 170)
        # bg translucent
        self.setStyleSheet("background-color: rgba(0,0,0,0)")

    def paintEvent(self, ev):
        path = QPainterPath()
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 0, 0, 127), 6))
        painter.setRenderHint(QPainter.Antialiasing)

        path.addRoundedRect(self.edge, 15, 15)
        painter.drawPath(path)
        painter.fillPath(path, self.bgColor)

    def updateBgColor(self, color):
        self.bgColor = color
        self.update()

    def enterEvent(self, QEvent):
        self.updateBgColor(QColor('#FF8546'))

    def leaveEvent(self, QEvent):
        self.updateBgColor(QColor('#FFA779'))

    def mousePressEvent(self, MouseEvent):
        self.updateBgColor(QColor('#C25015'))

    def mouseReleaseEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(QColor('#FF6A1D'))
        print("Model tab")
        if MouseEvent.button() == Qt.RightButton:
            print('right click menu')
        elif MouseEvent.button() == Qt.LeftButton:
            self.triggered.emit(self.MLModel)

    def setModel(self, ModelType, Describe=None):
        if isinstance(ModelType, str):
            self.modelTypeLabel.setText(ModelType)
            if Describe:
                self.modelDescribeLabel.setText(Describe)
            else:
                self.modelDescribeLabel.setText('N/A')
        else:
            raise TypeError

    def setEval(self, evalMetric: str, evalScore: float):
        if isinstance(evalMetric, str) and isinstance(evalScore, float):
            self.evalMetric.setText('%s: ' % evalMetric)
            self.evalScore.setText('%.4f' % evalScore)
        else:
            raise TypeError

    def setLBScore(self, LBScore: float):
        if isinstance(LBScore, float):
            self.LBScore.setText('%.4f' % LBScore)
        else:
            raise TypeError

    def createNewHLayout(self, label, value, font, color='0B73F7'):
        newLayout = QHBoxLayout(self)
        newLayout.addWidget(label)
        newLayout.addWidget(value, Qt.AlignLeft)
        label.setFont(font)
        value.setFont(font)
        value.setStyleSheet("color:#%s;" % color)
        return newLayout


class DataWidget(QWidget):
    # signal
    triggered = pyqtSignal(str)

    def __init__(self, dataType, fileName, parent=None):
        super(DataWidget, self).__init__(parent=parent)
        self.setFixedSize(180, 180)
        self.mainLayout = QGridLayout(self)
        self.edge = None
        self.labelFont = QFont("Arial", 10, QFont.Bold)
        self.bgColor = None
        self.normColor = None
        self.enterColor = None
        self.pressColor = None
        self.csvColorSet = {'normColor': '#AFFFAA', 'enterColor': '#67F95E', 'pressColor': '#5EDC56'}
        self.pklColorSet = {'normColor': '#AAFFD6', 'enterColor': '#5EF9AE', 'pressColor': '#56DC9B'}
        # Data type
        self.fileName = fileName
        self.DataType = dataType
        self.DataLabel = QLabel(dataType)
        self.DataLabel.setFont(QFont("Arial", 11, QFont.Bold))
        # Data File name
        self.DataFile = QLabel(os.path.basename(fileName))
        self.DataFile.setFont(QFont("Arial", 9, QFont.Bold))
        # Data shape
        self.DataShape = QLabel('')
        self.DataShape.setFont(QFont("Arial", 9, QFont.Times))
        # Data describe
        self.DataDescribe = QLabel('')
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(18, 18, 0, 0)
        self.mainLayout.addWidget(self.DataLabel, 0, 0, Qt.AlignTop)
        self.mainLayout.addWidget(self.DataFile, 1, 0)
        shape = self.createNewHLayout(QLabel('Shape: '), self.DataShape, QFont("Arial", 9, QFont.Times))
        self.mainLayout.addLayout(shape, 2, 0)
        self.mainLayout.addWidget(self.DataDescribe, 3, 0)
        self.mainLayout.setRowStretch(4, 10)

        # set color set
        if self.DataType == 'csv':
            self.setColorSet(**self.csvColorSet)
        elif self.DataType == 'pkl':
            self.setColorSet(**self.pklColorSet)
        self.bgColor = self.normColor
        self.edge = QRectF(5, 5, 170, 170)
        # bg translucent
        self.setStyleSheet("background-color: rgba(0,0,0,0)")

    def paintEvent(self, ev):
        path = QPainterPath()
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 0, 0, 127), 6))
        painter.setRenderHint(QPainter.Antialiasing)
        path.addRoundedRect(self.edge, 15, 15)
        painter.drawPath(path)
        painter.fillPath(path, self.bgColor)

    def updateBgColor(self, color):
        self.bgColor = color
        self.update()

    def enterEvent(self, QEvent):
        self.updateBgColor(self.enterColor)

    def leaveEvent(self, QEvent):
        self.updateBgColor(self.normColor)

    def mousePressEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(self.pressColor)

    def mouseReleaseEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(self.enterColor)
        if MouseEvent.button() == Qt.RightButton:
            print('right click menu')
        elif MouseEvent.button() == Qt.LeftButton:
            self.triggered.emit(self.fileName)

    def setColorSet(self, normColor, enterColor, pressColor):
        self.normColor = QColor(normColor)
        self.enterColor = QColor(enterColor)
        self.pressColor = QColor(pressColor)

    def createNewHLayout(self, label, value, font, color='0B73F7'):
        newLayout = QHBoxLayout(self)
        newLayout.addWidget(label)
        newLayout.addWidget(value, Qt.AlignLeft)
        label.setFont(font)
        value.setFont(font)
        value.setStyleSheet("color:#%s;" % color)
        return newLayout


class ImageDataWidget(QWidget):
    # signal
    triggered = pyqtSignal(str)

    def __init__(self, dataType, imageCount, ImageDir, parent=None):
        super(ImageDataWidget, self).__init__(parent=parent)
        self.setFixedSize(180, 180)
        self.mainLayout = QGridLayout(self)
        self.edge = None
        self.labelFont = QFont("Arial", 10, QFont.Bold)
        self.bgColor = None
        self.normColor = None
        self.enterColor = None
        self.pressColor = None
        self.imageColorSet = {'normColor': '#AFFFAA', 'enterColor': '#67F95E', 'pressColor': '#5EDC56'}
        # Data type
        self.ImageDir = ImageDir
        self.ImageCount = QLabel(str(imageCount), self)
        self.DataType = QLabel(dataType, self)
        self.DataType.setFont(QFont("Arial", 9, QFont.Bold))
        # Data File name
        self.ImageDataDir = QLabel('Image Dir: ' + os.path.basename(ImageDir))
        self.ImageDataDir.setFont(QFont("Arial", 11, QFont.Bold))

        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(18, 18, 0, 0)
        self.mainLayout.addWidget(self.ImageDataDir, 0, 0, Qt.AlignTop)
        self.mainLayout.addWidget(self.DataType, 1, 0)
        count = self.createNewHLayout(QLabel('Count: '), self.ImageCount, QFont("Arial", 9, QFont.Times))
        self.mainLayout.addLayout(count, 2, 0)
        self.mainLayout.setRowStretch(3, 10)

        # set color set
        self.setColorSet(**self.imageColorSet)
        self.bgColor = self.normColor
        self.edge = QRectF(5, 5, 170, 170)
        # bg translucent
        self.setStyleSheet("background-color: rgba(0,0,0,0)")

    def paintEvent(self, ev):
        path = QPainterPath()
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 0, 0, 127), 6))
        painter.setRenderHint(QPainter.Antialiasing)
        path.addRoundedRect(self.edge, 15, 15)
        painter.drawPath(path)
        painter.fillPath(path, self.bgColor)

    def updateBgColor(self, color):
        self.bgColor = color
        self.update()

    def enterEvent(self, QEvent):
        self.updateBgColor(self.enterColor)

    def leaveEvent(self, QEvent):
        self.updateBgColor(self.normColor)

    def mousePressEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(self.pressColor)

    def mouseReleaseEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(self.enterColor)
        if MouseEvent.button() == Qt.RightButton:
            print('right click menu')
        elif MouseEvent.button() == Qt.LeftButton:
            self.triggered.emit(self.ImageDir)

    def setColorSet(self, normColor, enterColor, pressColor):
        self.normColor = QColor(normColor)
        self.enterColor = QColor(enterColor)
        self.pressColor = QColor(pressColor)

    def createNewHLayout(self, label, value, font, color='0B73F7'):
        newLayout = QHBoxLayout(self)
        newLayout.addWidget(label)
        newLayout.addWidget(value, Qt.AlignLeft)
        label.setFont(font)
        value.setFont(font)
        value.setStyleSheet("color:#%s;" % color)
        return newLayout


class ScriptWidget(QWidget):
    # signal
    triggered = pyqtSignal(str)

    def __init__(self, scriptType, fileName, parent=None):
        super(ScriptWidget, self).__init__(parent=parent)
        self.setFixedSize(180, 180)
        self.mainLayout = QGridLayout(self)
        self.edge = None
        self.labelFont = QFont("Arial", 10, QFont.Bold)
        self.bgColor = None
        self.normColor = None
        self.enterColor = None
        self.pressColor = None
        self.pyColorSet = {'normColor': '#AAD2FF', 'enterColor': '#5EA7F9', 'pressColor': '#5695DC'}
        self.ipynbColorSet = {'normColor': '#B8AAFF', 'enterColor': '#785EF9', 'pressColor': '#6C56DC'}
        # Data type
        self.fileName = fileName
        self.ScriptType = scriptType
        self.ScriptLabel = QLabel(scriptType)
        self.ScriptLabel.setFont(QFont("Arial", 11, QFont.Bold))
        # Data File name
        self.ScriptFile = QLabel(os.path.basename(fileName))
        self.ScriptFile.setFont(QFont("Arial", 9, QFont.Bold))
        # Data describe
        self.ScriptDescribe = QLabel('')
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(18, 18, 0, 0)
        self.mainLayout.addWidget(self.ScriptLabel, 0, 0, Qt.AlignTop)
        self.mainLayout.addWidget(self.ScriptFile, 1, 0)
        self.mainLayout.addWidget(self.ScriptDescribe, 2, 0)
        self.mainLayout.setRowStretch(3, 10)

        # set color set
        if self.ScriptType == 'py':
            self.setColorSet(**self.pyColorSet)
        elif self.ScriptType == 'ipynb':
            self.setColorSet(**self.ipynbColorSet)
        self.bgColor = self.normColor
        self.edge = QRectF(5, 5, 170, 170)
        # bg translucent
        self.setStyleSheet("background-color: rgba(0,0,0,0)")

    def paintEvent(self, ev):
        path = QPainterPath()
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 0, 0, 127), 6))
        painter.setRenderHint(QPainter.Antialiasing)
        path.addRoundedRect(self.edge, 15, 15)
        painter.drawPath(path)
        painter.fillPath(path, self.bgColor)

    def updateBgColor(self, color):
        self.bgColor = color
        self.update()

    def enterEvent(self, QEvent):
        self.updateBgColor(self.enterColor)

    def leaveEvent(self, QEvent):
        self.updateBgColor(self.normColor)

    def mousePressEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(self.pressColor)

    def mouseReleaseEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(self.enterColor)
        if MouseEvent.button() == Qt.RightButton:
            print('right click menu')
        elif MouseEvent.button() == Qt.LeftButton:
            self.triggered.emit(self.fileName)

    def setColorSet(self, normColor, enterColor, pressColor):
        self.normColor = QColor(normColor)
        self.enterColor = QColor(enterColor)
        self.pressColor = QColor(pressColor)

    def createNewHLayout(self, label, value, font, color='0B73F7'):
        newLayout = QHBoxLayout(self)
        newLayout.addWidget(label)
        newLayout.addWidget(value, Qt.AlignLeft)
        label.setFont(font)
        value.setFont(font)
        value.setStyleSheet("color:#%s;" % color)
        return newLayout


class ProjectWidget(QWidget):
    # signal
    triggered = pyqtSignal(str)

    def __init__(self, projectName, projectInfo):
        super(ProjectWidget, self).__init__()
        self.setFixedSize(180, 180)
        self.mainLayout = QGridLayout(self)
        self.edge = None
        self.labelFont = QFont("Arial", 10, QFont.Bold)
        self.bgColor = None
        self.normColor = None
        self.enterColor = None
        self.pressColor = None
        self.ColorSet = {'normColor': '#BBAAFF', 'enterColor': '#7D5EF9', 'pressColor': '#7056DC'}

        # project info
        self.projectName = QLabel(projectName)
        self.projectLocation = QLabel(projectInfo[1])
        self.lastOpenTime = QLabel(projectInfo[0])
        self.projectFile = projectInfo[2]
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(18, 18, 0, 0)
        self.mainLayout.addWidget(self.projectName, 0, 0, Qt.AlignTop)
        self.mainLayout.addWidget(self.projectLocation, 1, 0)
        self.mainLayout.addWidget(self.lastOpenTime, 2, 0)
        self.mainLayout.setRowStretch(3, 10)
        # set color set
        self.setColorSet(**self.ColorSet)

        self.bgColor = self.normColor
        self.edge = QRectF(5, 5, 170, 170)
        # bg translucent
        self.setStyleSheet("background-color: rgba(0,0,0,0)")

    def paintEvent(self, ev):
        path = QPainterPath()
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 0, 0, 127), 6))
        painter.setRenderHint(QPainter.Antialiasing)
        path.addRoundedRect(self.edge, 15, 15)
        painter.drawPath(path)
        painter.fillPath(path, self.bgColor)

    def updateBgColor(self, color):
        self.bgColor = color
        self.update()

    def enterEvent(self, QEvent):
        self.updateBgColor(self.enterColor)

    def leaveEvent(self, QEvent):
        self.updateBgColor(self.normColor)

    def mousePressEvent(self, QMouseEvent):
        self.updateBgColor(self.pressColor)

    def mouseReleaseEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(self.enterColor)
        if MouseEvent.button() == Qt.RightButton:
            print('right click menu')
        elif MouseEvent.button() == Qt.LeftButton:
            self.triggered.emit(self.projectFile)

    def setColorSet(self, normColor, enterColor, pressColor):
        self.normColor = QColor(normColor)
        self.enterColor = QColor(enterColor)
        self.pressColor = QColor(pressColor)


class ResultWidget(QWidget):
    # signal
    triggered = pyqtSignal(str)

    def __init__(self, fileName, parent=None):
        super(ResultWidget, self).__init__(parent=parent)
        self.setFixedSize(180, 180)
        self.mainLayout = QGridLayout(self)
        self.edge = None
        self.labelFont = QFont("Arial", 10, QFont.Bold)
        self.bgColor = None
        self.normColor = None
        self.enterColor = None
        self.pressColor = None
        self.ColorSet = {'normColor': '#FFAAFF', 'enterColor': '#F95EF9', 'pressColor': '#DC56DC'}
        # Data type
        self.fileName = fileName
        self.MLResult = modelResult.loadResult(self.fileName)
        # self.resultFile = QLabel(os.path.basename(self.fileName), self)
        self.modelName = QLabel(self.MLResult.modelName, self)
        self.algorithm = QLabel(self.MLResult.algorithm, self)
        self.modelScore = QLabel('Score:' + str(self.MLResult.score), self)
        self.date = QLabel(self.MLResult.startTime, self)
        self.modelName.setFont(QFont("Arial", 11, QFont.Bold))
        self.algorithm.setFont(QFont("Arial", 11, QFont.Bold))
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(18, 18, 0, 0)
        # self.mainLayout.addWidget(self.resultFile, 0, 0, Qt.AlignTop)
        self.mainLayout.addWidget(self.modelName, 0, 0, Qt.AlignTop)
        self.mainLayout.addWidget(self.algorithm, 1, 0)
        self.mainLayout.addWidget(self.modelScore, 2, 0)
        self.mainLayout.addWidget(self.date, 3, 0)
        self.mainLayout.setRowStretch(4, 10)

        # set color set
        self.setColorSet(**self.ColorSet)
        self.bgColor = self.normColor
        self.edge = QRectF(5, 5, 170, 170)
        # bg translucent
        self.setStyleSheet("background-color: rgba(0,0,0,0)")

    def paintEvent(self, ev):
        path = QPainterPath()
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 0, 0, 127), 6))
        painter.setRenderHint(QPainter.Antialiasing)
        path.addRoundedRect(self.edge, 15, 15)
        painter.drawPath(path)
        painter.fillPath(path, self.bgColor)

    def updateBgColor(self, color):
        self.bgColor = color
        self.update()

    def enterEvent(self, QEvent):
        self.updateBgColor(self.enterColor)

    def leaveEvent(self, QEvent):
        self.updateBgColor(self.normColor)

    def mousePressEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(self.pressColor)

    def mouseReleaseEvent(self, MouseEvent: QMouseEvent):
        self.updateBgColor(self.enterColor)
        if MouseEvent.button() == Qt.RightButton:
            print('right click menu')
        elif MouseEvent.button() == Qt.LeftButton:
            self.triggered.emit(self.fileName)

    def setColorSet(self, normColor, enterColor, pressColor):
        self.normColor = QColor(normColor)
        self.enterColor = QColor(enterColor)
        self.pressColor = QColor(pressColor)

    def createNewHLayout(self, label, value, font, color='0B73F7'):
        newLayout = QHBoxLayout(self)
        newLayout.addWidget(label)
        newLayout.addWidget(value, Qt.AlignLeft)
        label.setFont(font)
        value.setFont(font)
        value.setStyleSheet("color:#%s;" % color)
        return newLayout


class TitleBar(QWidget):
    left = 0
    up = 1
    right = 2
    down = 3

    Horizontal = 0
    Vertical = 1

    def __init__(self, title, parent=None):
        super(TitleBar, self).__init__(parent=parent)
        self.Title = QLabel(title, self)
        self.Icon = QIcon('./res/collapse_left.ico')
        self.Height = 40
        self.currentOrient = self.left
        self.font = QFont('Arial', 12, QFont.Bold)
        self.CollapseButton = QPushButton(self.Icon, '', self)
        self.mainLayout = None
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.addWidget(self.Title, 1, Qt.AlignLeft)
        self.mainLayout.addStretch(1)
        self.mainLayout.addWidget(self.CollapseButton, 1, Qt.AlignRight)
        self.setLayout(self.mainLayout)
        self.Title.setFont(self.font)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(self.Height)

    def setTitle(self, title):
        self.Title.setText(title)

    def setIcon(self, icon: QIcon):
        self.Icon = icon

    def setButtonOrient(self, orient):
        if orient == self.left:
            self.Icon = QIcon('./res/collapse_left.ico')
        elif orient == self.up:
            self.Icon = QIcon('./res/collapse_up.ico')
        elif orient == self.right:
            self.Icon = QIcon('./res/collapse_right.ico')
        elif orient == self.down:
            self.Icon = QIcon('./res/collapse_down.ico')
        self.CollapseButton.setIcon(self.Icon)
        self.currentOrient = orient

    def setHeight(self, size):
        self.Height = size
        self.setFixedHeight(self.Height)

    def onCollapseButtonClicked(self):
        if self.currentOrient == self.left:
            self.setButtonOrient(self.right)
        elif self.currentOrient == self.right:
            self.setButtonOrient(self.left)
        elif self.currentOrient == self.up:
            self.setButtonOrient(self.down)
        elif self.currentOrient == self.down:
            self.setButtonOrient(self.up)


class CollapsibleTabWidget(QWidget):
    Horizontal = 0
    Vertical = 1
    doCollapse = pyqtSignal()

    def __init__(self, orientation=0, parent=None):
        super(CollapsibleTabWidget, self).__init__(parent=parent)
        self.frameLayout = None
        self.verticalLayout = None
        self.tabBar = None
        self.tabBarWidget = QWidget(self)
        self.orientation = orientation
        # self.orientation = self.Vertical
        self.splitter = None
        self.splitterPos = None
        self.splitterLower = None
        self.stackTitle = None
        self.stackWidget = None
        self.tabBarList = []

        # local data
        if self.orientation == self.Horizontal:
            self.initHorizontalUI()
            self.titleBarIcon = TitleBar.down
        elif self.orientation == self.Vertical:
            self.initVerticalUI()
            self.titleBarIcon = TitleBar.left

        self.tabBarWidget.setStyleSheet('background-color: #B2B2B2;')
        self.stackTitle.setStyleSheet('background-color: #B2B2B2;')

    def initHorizontalUI(self):
        self.frameLayout = QVBoxLayout(self)
        self.tabBar = QHBoxLayout(self)
        self.tabBarWidget.setLayout(self.tabBar)
        self.tabBar.setAlignment(Qt.AlignLeft)
        self.verticalLayout = QVBoxLayout(self)
        # fill stack
        self.stackTitle = QStackedWidget(self)
        self.stackWidget = QStackedWidget(self)
        self.verticalLayout.addWidget(self.stackTitle)
        self.verticalLayout.addWidget(self.stackWidget)
        # finish
        self.frameLayout.addLayout(self.verticalLayout)
        self.frameLayout.addWidget(self.tabBarWidget)
        self.setLayout(self.frameLayout)
        self.tabBarWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

    def initVerticalUI(self):
        self.frameLayout = QHBoxLayout(self)
        self.verticalLayout = QVBoxLayout(self)
        # tab bar
        self.tabBar = QVBoxLayout(self)
        self.tabBarWidget.setLayout(self.tabBar)
        self.tabBar.setAlignment(Qt.AlignTop)
        # fill stack
        self.stackTitle = QStackedWidget(self)
        self.stackWidget = QStackedWidget(self)

        self.verticalLayout.addWidget(self.stackTitle)
        self.verticalLayout.addWidget(self.stackWidget)

        self.stackWidget.addWidget(QLabel('asdf', self))
        # finish
        self.frameLayout.addWidget(self.tabBarWidget)
        self.frameLayout.addLayout(self.verticalLayout)
        self.setLayout(self.frameLayout)
        self.tabBarWidget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)

    def setOrientation(self, orient):
        self.orientation = orient

    def onTabClicked(self, index):
        pass

    def addTab(self, widget: QWidget, title: str):
        titleBar = TitleBar(title, self)
        titleBar.setButtonOrient(self.titleBarIcon)
        titleBar.CollapseButton.clicked.connect(self.collapseStacks)
        self.stackTitle.addWidget(titleBar)
        self.stackWidget.addWidget(widget)
        tabButton = customPushButton(title, len(self.tabBarList), self.orientation, self)
        self.tabBarList.append(tabButton)

        tabButton.clicked.connect(self.collapseStacks)
        tabButton.clicked_index.connect(self.setCurStack)
        self.tabBar.addWidget(tabButton, 0, Qt.AlignLeft)

        self.stackTitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stackTitle.setFixedHeight(titleBar.Height)

    def collapseStacks(self):
        if self.stackWidget.isVisible():
            self.splitterPos = self.splitter.sizes()
            self.stackTitle.hide()
            self.stackWidget.hide()
            if self.orientation == self.Horizontal:
                self.splitter.setSizes([10000, 0])
            if self.orientation == self.Vertical:
                self.splitter.setSizes([0, 10000])
            self.splitter.handle(1).setDisabled(True)
        else:
            self.splitter.setSizes(self.splitterPos)
            self.stackTitle.show()
            self.stackWidget.show()
            self.splitter.handle(1).setDisabled(False)
        self.doCollapse.emit()

    def setCurStack(self, index):
        self.stackTitle.setCurrentIndex(index)
        self.stackWidget.setCurrentIndex(index)

    def setSplitter(self, splitter: QSplitter):
        self.splitter = splitter
        self.splitter.splitterMoved.connect(self.setSplitterRate)

    def setSplitterRate(self, pos, index):
        self.splitterLower = self.splitter.sizes()[1]


class customPushButton(QPushButton):
    clicked_index = pyqtSignal(int)
    Horizontal = 0
    Vertical = 1

    def __init__(self, label, index, orientation=0, parent=None):
        super(customPushButton, self).__init__(parent=parent)
        self.setText(label)
        self.index = index
        self.orientation = orientation
        if orientation == self.Vertical:
            self.setFixedWidth(25)
        if orientation == self.Horizontal:
            self.setFixedHeight(25)

    def mouseReleaseEvent(self, event):
        self.clicked_index.emit(self.index)
        QPushButton.mouseReleaseEvent(self, event)

    def paintEvent(self, event: QPaintEvent):
        painter = QStylePainter(self)
        if self.orientation == self.Vertical:
            painter.rotate(270)
            painter.translate(-1 * self.height(), 0)
        painter.drawControl(QStyle.CE_PushButton, self.getStyleOptions())

    def minimumSizeHint(self):
        size = super(customPushButton, self).minimumSizeHint()
        if self.orientation == self.Vertical:
            size.transpose()
        return size

    def sizeHint(self):
        size = super(customPushButton, self).sizeHint()
        if self.orientation == self.Vertical:
            size.transpose()
        return size

    def getStyleOptions(self):
        options = QStyleOptionButton()
        options.initFrom(self)
        size = options.rect.size()
        if self.orientation == self.Vertical:
            size.transpose()
        options.rect.setSize(size)
        options.features = QStyleOptionButton.None_
        if self.isFlat():
            options.features |= QStyleOptionButton.Flat
        if self.menu():
            options.features |= QStyleOptionButton.HasMenu
        if self.autoDefault() or self.isDefault():
            options.features |= QStyleOptionButton.AutoDefaultButton
        if self.isDefault():
            options.features |= QStyleOptionButton.DefaultButton
        if self.isDown() or (self.menu() and self.menu().isVisible()):
            options.state |= QStyle.State_Sunken
        if self.isChecked():
            options.state |= QStyle.State_On
        if not self.isFlat() and not self.isDown():
            options.state |= QStyle.State_Raised

        options.text = self.text()
        options.icon = self.icon()
        options.iconSize = self.iconSize()
        return options


class HistoryWidget(QWidget):
    def __init__(self, parent=None):
        super(HistoryWidget, self).__init__(parent=parent)
        self.historyView = QTreeView(self)
        self.proxyModel = HistorySortModel(self)
        self.sourceModel = QStandardItemModel()
        self.initUI()

    def initUI(self):
        self.historyView.setRootIsDecorated(False)
        self.historyView.setAlternatingRowColors(True)
        self.historyView.setModel(self.proxyModel)
        self.historyView.setSortingEnabled(True)
        self.historyView.sortByColumn(1, Qt.AscendingOrder)

        self.historyView.setFixedWidth(750)

        self.sourceModel = QStandardItemModel(0, 6, self)
        self.sourceModel.setHeaderData(0, Qt.Horizontal, "Model Name")
        self.sourceModel.setHeaderData(1, Qt.Horizontal, "Algorithm")
        self.sourceModel.setHeaderData(2, Qt.Horizontal, "Score")
        self.sourceModel.setHeaderData(3, Qt.Horizontal, "TrainSet")
        self.sourceModel.setHeaderData(4, Qt.Horizontal, "Running Time")
        self.sourceModel.setHeaderData(5, Qt.Horizontal, "Param")
        self.proxyModel.setSourceModel(self.sourceModel)
        self.historyView.setModel(self.sourceModel)

    def addItem(self, result: modelResult):
        self.sourceModel.insertRow(self.sourceModel.rowCount())

        self.sourceModel.setData(self.sourceModel.index(0, 0), result.modelName)  # string
        self.sourceModel.setData(self.sourceModel.index(0, 1), result.algorithm)  # string
        self.sourceModel.setData(self.sourceModel.index(0, 2), result.score)  # float
        self.sourceModel.setData(self.sourceModel.index(0, 3), result.trainSet)  # string
        self.sourceModel.setData(self.sourceModel.index(0, 4), result.runTime)  # second
        self.sourceModel.setData(self.sourceModel.index(0, 5), result.param)  # dict


class HistorySortModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(HistorySortModel, self).__init__(parent=parent)

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        leftData = self.sourceModel().data(left)
        rightData = self.sourceModel().data(right)
        return True


class HistoryItem(QWidget):
    def __init__(self, parent=None):
        super(HistoryItem, self).__init__(parent=parent)
        self.mainLayout = QHBoxLayout(self)
        self.modelInfoLayout = QVBoxLayout(self)
        self.modelResultLayout = QVBoxLayout(self)
        self.buttonLayout = QVBoxLayout(self)
        self.modelName = QLabel('model name', self)
        self.createTime = QLabel('xxxx-xx-xx xx:xx:xx', self)
        self.runTime = QLabel('xxxx-xx-xx xx:xx:xx', self)
        self.modelID = QLabel('No.xxx', self)
        self.score = QLabel(str(999.09999), self)
        self.modelType = QLabel('asss', self)
        self.param = QLabel(str(dict()), self)
        self.trainSet = QLabel('adsfasdf', self)

        self.openModelButton = QPushButton('Open', self)

        self.setLayout(self.mainLayout)
        self.initUI()

    def initUI(self):
        self.modelInfoLayout.addWidget(self.modelName)
        self.modelInfoLayout.addWidget(self.modelID)
        self.modelInfoLayout.addWidget(self.createTime)
        self.modelInfoLayout.addWidget(self.runTime)

        self.modelResultLayout.addWidget(self.score)
        self.modelResultLayout.addWidget(self.modelType)
        self.modelResultLayout.addWidget(self.param)
        self.modelResultLayout.addWidget(self.trainSet)

        self.buttonLayout.addWidget(self.openModelButton)

        self.mainLayout.addLayout(self.modelInfoLayout)
        self.mainLayout.addLayout(self.modelResultLayout)
        self.mainLayout.addLayout(self.buttonLayout)

        self.mainLayout.setStretch(0, 1)
        self.mainLayout.setStretch(1, 2)
        self.mainLayout.setStretch(2, 1)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(100)


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QVBoxLayout(self)
        self.setFixedSize(800, 500)
        self.setLayout(self.mainLayout)
        # q = queueTabWidget(self)
        # self.mainLayout.addWidget(q)
        # q.addItem('name1', 'describe1')


class ImageViewer(QWidget):
    def __init__(self, imageDir, parent=None):
        super(ImageViewer, self).__init__(parent=parent)
        self.imageDir = imageDir
        self.mainLayout = QVBoxLayout(self)
        self.toolBar = QToolBar(self)
        self.viewerLayout = FlowLayout()
        self.imageWidgetList = list()

        self.initUI()

    def initUI(self):
        self.setLayout(self.mainLayout)
        # scroll viewer
        viewerWidget = QWidget(self)
        viewerWidget.setLayout(self.viewerLayout)
        scrollarea = QScrollArea(self)
        scrollarea.setWidgetResizable(True)
        scrollbar = QScrollBar(self)
        scrollarea.setWidget(viewerWidget)
        scrollarea.setVerticalScrollBar(scrollbar)
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # add widget to main layout
        # future feature:  add tool bar
        self.mainLayout.addWidget(scrollarea)
        self.loadImage()

    def loadImage(self):
        imageList = os.listdir(self.imageDir)
        # future feature:  random select image from image list
        # future feature:  limited number of loaded image
        for image in imageList:
            imageFullPath = os.path.join(self.imageDir, image)
            imageCell = ImageCell(imageFullPath, self)
            self.imageWidgetList.append(imageCell)
            self.viewerLayout.addWidget(imageCell)


class ImageCell(QWidget):
    def __init__(self, imageFile, parent=None):
        super(ImageCell, self).__init__(parent=parent)
        self.imageFile = imageFile
        self.imageHolder = QLabel(self)
        self.imageName = QLabel(os.path.basename(imageFile), self)
        self.imageName.setAlignment(Qt.AlignCenter)
        self.mainLayout = QVBoxLayout(self)
        # init image
        self.image = QImage(self.imageFile)
        self.imagePixMap = QPixmap.fromImage(self.image)
        self.imageHolder.setPixmap(QPixmap(self.imageFile))
        self.imageHolder.resize(self.image.size())
        # set main layout
        self.mainLayout.addWidget(self.imageHolder)
        self.mainLayout.addWidget(self.imageName)
        # init layout
        self.setLayout(self.mainLayout)
        self.resize(self.imageHolder.size().width() + self.imageName.size().width(),
                    self.imageHolder.size().height() + self.imageName.size().height())

    def enterEvent(self, QEvent):
        self.updateBgColor(QColor('#8598FF'))

    def leaveEvent(self, QEvent):
        self.updateBgColor(Qt.transparent)

    def updateBgColor(self, color):
        self.imageName.setAutoFillBackground(True)
        palette = self.imageName.palette()
        palette.setColor(self.imageName.backgroundRole(), color)
        self.imageName.setPalette(palette)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), color)
        self.setPalette(palette)

        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        pass

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        print('open image in other dialog')

    def mouseReleaseEvent(self, event: QMouseEvent):
        pass


class DragTableView(QTableView):
    def __init__(self, parent=None):
        super(DragTableView, self).__init__(parent=parent)
        self.setAcceptDrops(True)

        self.model = None
        self.ifValidPress = False
        self.startRow = 0
        self.targetRow = 0
        self.dragStartPoint = None
        self.dragPointAtItem = None
        self.dragText = None
        self.itemRowHeight = 30
        self.headerHeight = 0
        self.lineLabel = QLabel(self)
        self.lineLabel.setFixedHeight(2)
        self.lineLabel.setGeometry(1, 0, self.width(), 2)
        self.lineLabel.setStyleSheet("border: 1px solid #8B7500;")
        self.lineLabel.hide()
        self.curRow = 0

        self.setDropIndicatorShown(True)

    def setModel(self, model):
        QTableView.setModel(self, model)
        self.model = model
        self.model.notEmpty.connect(self.updateModelInfo)
        self.itemRowHeight = self.rowHeight(0) if not self.model.checkEmpty() else None
        self.headerHeight = self.horizontalHeader().sectionSizeFromContents(0).height()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                self.ifValidPress = True
                self.dragStartPoint = event.pos()
                self.dragText = '%s %s %s' % (self.model.data(self.model.index(index.row(), 0), Qt.DisplayRole),
                                              self.model.data(self.model.index(index.row(), 1), Qt.DisplayRole),
                                              self.model.data(self.model.index(index.row(), 2), Qt.DisplayRole))
                self.dragPointAtItem = self.dragStartPoint - QPoint(0, index.row() * self.itemRowHeight)
                self.startRow = index.row()
        QTableView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.ifValidPress:
            return
        if not event.buttons() & Qt.LeftButton:
            return
        if (event.pos() - self.dragStartPoint).manhattanLength() < QApplication.startDragDistance():
            return

        self.lineLabel.show()
        self.doDrag()
        self.lineLabel.hide()
        self.ifValidPress = False

    def doDrag(self):
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(self.dragText)
        drag.setMimeData(mimeData)

        drag_img = QPixmap(self.width(), self.itemRowHeight)
        drag_img.fill(QColor(255, 255, 255, 100))
        painter = QPainter(drag_img)
        painter.setPen(QColor(0, 0, 0, 200))
        painter.drawText(QRectF(40, 0, self.width(), self.itemRowHeight), self.dragText, QTextOption(Qt.AlignVCenter))
        painter.end()

        drag.setPixmap(drag_img)
        drag.setHotSpot(self.dragPointAtItem)
        if drag.exec(Qt.MoveAction) == Qt.MoveAction:
            print('drag')

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
            QTableView.dragEnterEvent(self, event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasText():
            self.curRow = 0
            index = self.indexAt(event.pos())
            if index.isValid():
                if event.pos().y() - index.row() * self.itemRowHeight >= self.itemRowHeight / 2:
                    self.curRow = index.row() + 1
                else:
                    self.curRow = index.row()
            else:
                self.curRow = self.model.rowCount()

            self.targetRow = self.curRow
            self.lineLabel.setGeometry(1, self.headerHeight + self.targetRow * self.itemRowHeight, self.width() - 2,
                                       2)
            event.acceptProposedAction()
            return
        event.ignore()
        QTableView.dragMoveEvent(self, event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasText():
            if self.startRow != self.targetRow - 1 and self.startRow != self.targetRow:
                print('move ', self.startRow, ' to ', self.targetRow)
                if self.targetRow > self.startRow:
                    self.model.moveProcess(self.startRow, self.targetRow - 1)
                else:
                    self.model.moveProcess(self.startRow, self.targetRow)
            event.acceptProposedAction()
            return
        event.ignore()
        QTableView.dropEvent(self, event)

    def updateModelInfo(self):
        # update height when adding rows to empty model
        self.itemRowHeight = self.rowHeight(0) if not self.model.checkEmpty() else None
        self.headerHeight = self.horizontalHeader().sectionSizeFromContents(0).height()


class customProcessModel(QAbstractTableModel):
    notEmpty = pyqtSignal()

    def __init__(self, parent=None):
        super(customProcessModel, self).__init__(parent=parent)
        self.rows = 0
        self.cols = 3  # No. | Process Name | Describe
        self.processQ = list()
        self.processInfo = dict()
        self.empty = True

    def checkEmpty(self):
        self.empty = True if self.rows == 0 else False
        return self.empty

    def loadQueue(self, PQ: processQueue):
        self.beginResetModel()
        self.processQ = PQ.processQ
        self.processInfo = PQ.processInfo
        self.rows = PQ.count
        self.endResetModel()

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
            p_id = self.processQ[modelIndex.row()][0]
            p_info = self.processInfo[p_id]
            if modelIndex.column() == 0:
                return 'No. %d' % modelIndex.row()
            elif modelIndex.column() == 1:
                return '%s' % p_info[0]
            elif modelIndex.column() == 2:
                return '%s' % p_info[1]
        else:
            return QVariant()

    def headerData(self, section, orientation, role=None):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return ['No.', 'Process Name', 'Process Describe'][section]
        if orientation == Qt.Vertical:
            return [i + 1 for i in range(self.rows)]
        return QVariant()

    def flags(self, modelIndex):
        # flags = QAbstractTableModel.flags(self, modelIndex)
        flags = Qt.NoItemFlags
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        return flags

    def moveProcess(self, cur, target):
        self.processQ.insert(target, self.processQ.pop(cur))
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rows - 1, self.cols - 1))

    def addProcess(self):
        # self.layoutAboutToBeChanged.emit()
        flag = False
        if self.rows == 0:
            flag = True
        self.rows += 1
        self.beginInsertRows(QModelIndex(), self.rows, self.rows)
        self.dataChanged.emit(self.createIndex(self.rows - 1, 0), self.createIndex(self.rows - 1, self.cols - 1))
        # self.layoutChanged.emit()
        self.endInsertRows()
        if flag:
            self.notEmpty.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = testDialog()
    test.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
