import os
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QListWidget, QToolBox, \
    QTabWidget, QTextEdit, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath
from PyQt5 import QtWidgets
import pandas as pd


class DataTabWidget(QWidget):
    def __init__(self, filename):
        super(DataTabWidget, self).__init__()
        # local data
        self.dataFrame = None
        self.verticalHeaderWidth = 50
        # init widgets
        self.mainLayout = QGridLayout(self)
        self.rightLayout = QVBoxLayout(self)
        self.toolset = QToolBox(self)
        self.tools_process = QWidget(self)
        self.tools_visualize = QWidget(self)

        self.dataWindow = QWidget(self)
        self.dataWindowLayout = QVBoxLayout(self)
        self.dataExplorer = QTableWidget(self)
        self.statistic = QTableWidget(self)

        self.mainTab = QTabWidget(self)
        self.outputTab = QTabWidget(self)
        self.outputEdit = QTextEdit(self)
        # init UI
        self.initUI()
        self.initDataExplorer(filename)
        self.initStatistic()

    def initUI(self):
        self.toolset.addItem(self.tools_process, 'Data Process')
        self.toolset.addItem(self.tools_visualize, 'Data Visualize')
        # init data window
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

    def initDataExplorer(self, filename):
        # load data
        self.dataFrame = pd.read_csv(filename)
        # init table
        self.dataExplorer.setRowCount(self.dataFrame.shape[0])
        self.dataExplorer.setColumnCount(self.dataFrame.shape[1])
        self.dataExplorer.setHorizontalHeaderLabels(self.dataFrame.columns.tolist())
        self.dataExplorer.verticalHeader().setFixedWidth(self.verticalHeaderWidth)
        for index, line in self.dataFrame.iterrows():
            for col, cell in enumerate(line):
                self.dataExplorer.setItem(index, col, QTableWidgetItem(str(cell)))

    def initStatistic(self):
        rowCount = 0
        self.statistic.insertRow(rowCount)
        self.statistic.setColumnCount(self.dataFrame.shape[1])
        self.statistic.setVerticalHeaderLabels(['Count'])
        self.statistic.verticalHeader().setFixedWidth(self.verticalHeaderWidth)
        self.statistic.setHorizontalHeaderLabels(self.dataFrame.columns.tolist())
        self.statistic.setItem(rowCount, 0, QTableWidgetItem(str(self.dataFrame['Id'].count())))
        rowCount+=1

class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QGridLayout(self)
        self.setFixedSize(800, 500)
        self.setLayout(self.mainLayout)
        self.item = DataTabWidget()
        self.mainLayout.addWidget(self.item, 0, 0)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    sys.exit(app.exec_())
