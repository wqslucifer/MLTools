import os
import sys
import time
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QApplication, QTabWidget, \
    QTabBar, QToolBar, QPushButton, QVBoxLayout, QTreeWidget, QSizePolicy, QAction, QStackedWidget, QListWidget, \
    QScrollBar, QScrollArea, QTextEdit, QTreeView, QTreeWidgetItem, QSplitter
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal, QTimer, QThread, QSortFilterProxyModel, \
    QModelIndex, QAbstractItemModel, QObject
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath, QStandardItem, QIcon, \
    QMouseEvent, QStandardItemModel

from PyQt5.QtQuick import QQuickView, QQuickItem
from PyQt5.QtQuickWidgets import QQuickWidget
from PyQt5.QtCore import QUrl, pyqtSlot
from PyQt5.QtGui import QGuiApplication

from model import ml_model, modelResult


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

    def __init__(self, title, parent=None):
        super(TitleBar, self).__init__(parent=parent)
        self.Title = QLabel(title, self)
        self.Icon = QIcon('./res/collapse_left.ico')
        self.Height = 40
        self.currentOrient = self.left
        self.font = QFont('Arial', 12, QFont.Bold)
        self.CollapseButton = QPushButton(self.Icon, '', self)
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

    def __init__(self, parent=None):
        super(CollapsibleTabWidget, self).__init__(parent=parent)
        self.frameLayout = None
        self.verticalLayout = None
        self.tabBar = None
        self.tabBarWidget = QWidget(self)
        self.orientation = self.Horizontal
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
        self.tabBarWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

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

    def initVerticalUI(self):
        self.frameLayout = QHBoxLayout(self)
        self.tabBar = QVBoxLayout(self)
        self.tabBarWidget.setLayout(self.tabBar)
        self.tabBar.setAlignment(Qt.AlignTop)
        self.verticalLayout = QVBoxLayout(self)
        # fill stack
        self.stackTitle = QStackedWidget(self)
        self.stackWidget = QStackedWidget(self)
        self.verticalLayout.addWidget(self.stackTitle)
        self.verticalLayout.addWidget(self.stackWidget)
        # finish
        self.frameLayout.addLayout(self.tabBar)
        self.frameLayout.addWidget(self.tabBarWidget)
        self.setLayout(self.frameLayout)

    def setOrientation(self, orient):
        self.orientation = orient

    def onTabClicked(self, index):
        pass

    def addTab(self, widget: QWidget, title:str):
        titleBar = TitleBar(title, self)
        titleBar.setButtonOrient(self.titleBarIcon)
        titleBar.CollapseButton.clicked.connect(self.collapseStacks)
        self.stackTitle.addWidget(titleBar)
        self.stackWidget.addWidget(widget)
        tabButton = customPushButton(title, len(self.tabBarList), self)
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
            self.splitter.setSizes([10000, 0])
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

    def __init__(self, label, index, parent=None):
        super(customPushButton, self).__init__(parent=parent)
        self.setText(label)
        self.index = index

    def mouseReleaseEvent(self, event):
        self.clicked_index.emit(self.index)
        QPushButton.mouseReleaseEvent(self, event)


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
        qml = queueTabWidget(self)
        self.mainLayout.addWidget(qml)
        r = qml.rootObject()
        for i in range(20):
            r.testPrint('test1name', 'alg_xgb', 'param_asdf')
        pass


class queueTabWidget(QQuickWidget):
    chartCleared = pyqtSignal()

    def __init__(self, parent=None):
        super(queueTabWidget, self).__init__(parent=parent)
        self.setSource(QUrl.fromLocalFile('queueTab.qml'))
        self.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.rootContext().setContextProperty('queueTabWidget', self)

    @pyqtSlot(str)
    def myprint(self, value):
        print(value)
        self.chartCleared.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = testDialog()
    test.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
