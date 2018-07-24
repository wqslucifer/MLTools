import os
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath
from PyQt5 import QtWidgets


class ModelWidget(QWidget):
    # signal
    triggered = pyqtSignal()
    def __init__(self):
        super(ModelWidget, self).__init__()
        self.setFixedSize(180, 180)
        self.mainLayout = QGridLayout(self)
        self.edge = None
        self.bgColor = None
        self.labelFont = QFont("Arial", 10, QFont.Bold)

        # model type
        self.modelTypeLabel = QLabel("xgboost")
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
        self.triggered.emit()

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


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QGridLayout(self)
        self.setFixedSize(800, 500)
        self.setLayout(self.mainLayout)
        self.item = DataWidget('csv')
        self.item.setDataFile('test.csv')
        self.mainLayout.addWidget(self.item, 0, 0)



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


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    sys.exit(app.exec_())
