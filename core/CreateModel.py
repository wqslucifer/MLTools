from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from core.project import ml_project
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
        self.curIndex = 0
        self.stackedList = []
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
        self.guide.setLabelColor(self.curIndex)

        stackedWidget_1 = createModel_1(self)
        self.stackedLayout.addWidget(stackedWidget_1)
        self.stackedList.append(stackedWidget_1)
        stackedWidget_2 = createModel_2(self)
        self.stackedLayout.addWidget(stackedWidget_2)
        self.stackedList.append(stackedWidget_2)
        stackedWidget_3 = createModel_3(self)
        self.stackedLayout.addWidget(stackedWidget_3)
        self.stackedList.append(stackedWidget_3)
        stackedWidget_4 = createModel_4(self)
        self.stackedLayout.addWidget(stackedWidget_4)
        self.stackedList.append(stackedWidget_4)
        stackedWidget_5 = createModel_5(self)
        self.stackedLayout.addWidget(stackedWidget_5)
        self.stackedList.append(stackedWidget_5)
        stackedWidget_6 = createModel_6(self)
        self.stackedLayout.addWidget(stackedWidget_6)
        self.stackedList.append(stackedWidget_6)

        self.nextButton.clicked.connect(self.nextButtonClicked)

    def nextButtonClicked(self):
        self.curIndex += 1
        self.guide.setLabelColor(self.curIndex)
        self.stackedLayout.setCurrentIndex(self.curIndex)


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
        self.widget = QWidget(self)
        self.mainLayout.addSpacing(50)
        self.mainLayout.addWidget(self.widget)
        self.mainLayout.addWidget(QLabel('1'))
        self.widget.setStyleSheet('background-color:#ffffff;')


class createModel_2(QWidget):
    def __init__(self, parent):
        super(createModel_2, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widget = QWidget(self)
        self.mainLayout.addSpacing(50)
        self.mainLayout.addWidget(self.widget)
        self.mainLayout.addWidget(QLabel('2'))
        self.widget.setStyleSheet('background-color:#ffffff;')


class createModel_3(QWidget):
    def __init__(self, parent):
        super(createModel_3, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widget = QWidget(self)
        self.mainLayout.addSpacing(50)
        self.mainLayout.addWidget(self.widget)
        self.mainLayout.addWidget(QLabel('3'))
        self.widget.setStyleSheet('background-color:#ffffff;')


class createModel_4(QWidget):
    def __init__(self, parent):
        super(createModel_4, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widget = QWidget(self)
        self.mainLayout.addSpacing(50)
        self.mainLayout.addWidget(self.widget)
        self.mainLayout.addWidget(QLabel('4'))
        self.widget.setStyleSheet('background-color:#ffffff;')


class createModel_5(QWidget):
    def __init__(self, parent):
        super(createModel_5, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widget = QWidget(self)
        self.mainLayout.addSpacing(50)
        self.mainLayout.addWidget(self.widget)
        self.mainLayout.addWidget(QLabel('5'))
        self.widget.setStyleSheet('background-color:#ffffff;')


class createModel_6(QWidget):
    def __init__(self, parent):
        super(createModel_6, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.widget = QWidget(self)
        self.mainLayout.addSpacing(50)
        self.mainLayout.addWidget(self.widget)
        self.mainLayout.addWidget(QLabel('6'))
        self.widget.setStyleSheet('background-color:#ffffff;')
