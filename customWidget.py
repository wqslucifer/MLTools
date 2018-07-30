import os
import sys
import time
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QApplication, QTabWidget, \
    QTabBar, QToolBar, QPushButton, QVBoxLayout, QTreeWidget, QSizePolicy, QAction, QStackedWidget, QListWidget, \
    QScrollBar, QScrollArea
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath, QStandardItem, QIcon
from model import ml_model


# widgets for main window tabs

class ModelWidget(QWidget):
    # signal
    triggered = pyqtSignal(str)

    def __init__(self, modelFile):
        super(ModelWidget, self).__init__()
        self.setFixedSize(180, 180)
        self.mainLayout = QGridLayout(self)
        self.edge = None
        self.bgColor = None
        self.labelFont = QFont("Arial", 10, QFont.Bold)
        self.MLModel = ml_model.loadModel(modelFile)
        # model type
        self.modelTypeLabel = QLabel(self.MLModel.modelType)
        self.modelTypeLabel.setFont(QFont("Arial", 11, QFont.Bold))
        # model describe
        self.modelDescribeLabel = QLabel("Describe:")
        # local eval
        self.evalMetric = QLabel("AUC: ")
        self.evalScore = QLabel("0.50000")
        # data set
        self.dataSetLabel = QLabel("Data No.001")
        self.dataSetLabel.setFont(QFont("Arial", 10, QFont.Bold))
        # self.dataSetLabel.setToolTip()
        # LB eval score
        self.leaderBoardLabel = QLabel("LB: ")
        self.LBScore = QLabel("0.56788")
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(18, 18, 0, 0)
        self.mainLayout.addWidget(self.modelTypeLabel, 0, 0, Qt.AlignTop)
        # local cv item
        evalLayout = self.createNewHLayout(self.evalMetric, self.evalScore, self.labelFont)
        self.mainLayout.addLayout(evalLayout, 1, 0)
        # LB item
        LBLayout = self.createNewHLayout(self.leaderBoardLabel, self.LBScore, self.labelFont)
        LBLayout.setSpacing(16)
        self.mainLayout.addLayout(LBLayout, 2, 0)
        # data set label
        self.mainLayout.addWidget(self.dataSetLabel, 3, 0)
        # describe label
        self.mainLayout.addWidget(self.modelDescribeLabel, 4, 0, Qt.AlignTop)

        self.mainLayout.setRowStretch(0, 1)
        self.mainLayout.setRowStretch(5, 20)
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

    def mousePressEvent(self, QMouseEvent):
        self.updateBgColor(QColor('#C25015'))

    def mouseReleaseEvent(self, QMouseEvent):
        self.updateBgColor(QColor('#FF6A1D'))
        print("Model tab")
        self.triggered.emit(self.MLModel.modelName)

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

    def mousePressEvent(self, QMouseEvent):
        self.updateBgColor(self.pressColor)

    def mouseReleaseEvent(self, QMouseEvent):
        self.updateBgColor(self.enterColor)
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

    def mousePressEvent(self, QMouseEvent):
        self.updateBgColor(self.pressColor)

    def mouseReleaseEvent(self, QMouseEvent):
        self.updateBgColor(self.enterColor)
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

    def mouseReleaseEvent(self, QMouseEvent):
        self.updateBgColor(self.enterColor)
        self.triggered.emit(self.projectFile)

    def setColorSet(self, normColor, enterColor, pressColor):
        self.normColor = QColor(normColor)
        self.enterColor = QColor(enterColor)
        self.pressColor = QColor(pressColor)


class TitleBar(QWidget):
    left = 0
    up = 1
    right = 2
    down = 3

    def __init__(self, title, parent=None):
        super(TitleBar, self).__init__(parent=parent)
        self.Title = QLabel(title, self)
        self.Icon = QIcon('./res/collapse_left.ico')
        self.Height = 30
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
        self.setHeight(50)
        # self.CollapseButton.clicked.connect(self.onCollapseButtonClicked)

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

    def __init__(self, parent=None):
        super(CollapsibleTabWidget, self).__init__(parent=parent)
        self.frameLayout = None
        self.verticalLayout = None
        self.tabBar = None
        self.orientation = self.Horizontal
        # self.orientation = self.Vertical
        self.stackTitle = None
        self.stackWidget = None

        # local data
        if self.orientation == self.Horizontal:
            self.initHorizontalUI()
            self.titleBarIcon = TitleBar.down
        elif self.orientation == self.Vertical:
            self.initVerticalUI()
            self.titleBarIcon = TitleBar.left

    def initHorizontalUI(self):
        self.frameLayout = QVBoxLayout(self)
        self.tabBar = QHBoxLayout(self)
        self.verticalLayout = QVBoxLayout(self)
        # fill stack
        self.stackTitle = QStackedWidget(self)
        self.stackWidget = QStackedWidget(self)
        self.verticalLayout.addWidget(self.stackTitle)
        self.verticalLayout.addWidget(self.stackWidget)
        # finish
        self.frameLayout.addLayout(self.verticalLayout)
        self.frameLayout.addLayout(self.tabBar)
        self.setLayout(self.frameLayout)

    def initVerticalUI(self):
        self.frameLayout = QHBoxLayout(self)
        self.tabBar = QVBoxLayout(self)
        self.verticalLayout = QVBoxLayout(self)
        # fill stack
        self.stackTitle = QStackedWidget(self)
        self.stackWidget = QStackedWidget(self)
        self.verticalLayout.addWidget(self.stackTitle)
        self.verticalLayout.addWidget(self.stackWidget)
        # finish
        self.frameLayout.addLayout(self.tabBar)
        self.frameLayout.addLayout(self.verticalLayout)
        self.setLayout(self.frameLayout)

    def setOrientation(self, orient):
        self.orientation = orient

    def onTabClicked(self, index):
        pass

    def addTab(self, title, widget: QWidget):
        titleBar = TitleBar(title, self)
        titleBar.setButtonOrient(self.titleBarIcon)
        titleBar.CollapseButton.clicked.connect(self.collapseStacks)
        self.stackTitle.addWidget(titleBar)
        self.stackWidget.addWidget(widget)
        tabButton = QPushButton(title, self)
        tabButton.clicked.connect(self.collapseStacks)
        self.tabBar.addWidget(tabButton, 0, Qt.AlignLeft)

    def collapseStacks(self):
        if self.stackWidget.isVisible():
            self.stackTitle.hide()
            self.stackWidget.hide()
        else:
            self.stackTitle.show()
            self.stackWidget.show()


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


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QVBoxLayout(self)
        self.setFixedSize(800, 500)
        self.setLayout(self.mainLayout)
        self.item = CollapsibleTabWidget(self)
        self.item.addTab('item1', QLabel('mainWidget', self))
        self.mainLayout.addWidget(self.item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = testDialog()
    test.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
