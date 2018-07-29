'''
create model file *.md
create model based on model type
'''

import os
import sys
import pandas as pd
from PyQt5.QtWidgets import QWidget, QDialog, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, \
    QApplication, QDockWidget, QLabel,QAction,QToolButton,QScrollArea,QScrollBar,QTabWidget,QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QIcon
from project import ml_project
from customWidget import ModelWidget, DataWidget, ProjectWidget, ScriptWidget
from customLayout import FlowLayout
from SwitchButton import switchButton


# widget for tab
class CreateModel(QWidget):
    def __init__(self, parent=None):
        super(CreateModel, self).__init__(parent=parent)
        self.outLayout = QHBoxLayout(self)
        self.insideLayout = QHBoxLayout(self)
        self.scrollArea = QScrollArea(self)
        self.infoTabWindow = QTabWidget(self)
        self.modelFrame = QFrame(self)
        self.displayWidget = QWidget(self)

    def initUI(self):
        self.scrollArea.setWidgetResizable(True)
        scrollbar = QScrollBar(self)
        # add scroll area to tab window
        self.tabWindow.addTab(self.scrollarea, os.path.basename(dataFile))
        self.tabWindow.setCurrentIndex(self.tabWindow.indexOf(scrollarea))
        # add tab detail widget to scroll area
        self.scrollarea.setWidget(dw)
        self.scrollarea.setVerticalScrollBar(scrollbar)
        self.scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = CreateModel()
    test.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
