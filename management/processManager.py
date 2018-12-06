from PyQt5.QtWidgets import *

from core.project import ml_project
import GENERAL

GENERAL.init()


class processManagerDialog(QDialog):
    def __init__(self, MLProject: ml_project, parent=None):
        super(processManagerDialog, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.upperLayout = QVBoxLayout(self)
        self.lowerLayout = QVBoxLayout(self)
        self.menuBar = QMenuBar(self)
        self.toolBar = QToolBar(self)
        self.processList = QTableWidget(self)
        self.initUI()

    def initUI(self):
        self.setLayout(self.mainLayout)
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.upperLayout.addWidget(self.menuBar)
        self.upperLayout.addWidget(self.toolBar)
        self.lowerLayout.addWidget(self.processList)
        self.lowerLayout.setContentsMargins(10, 0, 10, 10)
        self.mainLayout.addLayout(self.upperLayout)
        self.mainLayout.addLayout(self.lowerLayout)

        # menu
        fileMenu = QMenu('File', self)
        f1 = QAction('add process', self)
        # g1.triggered.connect(lambda: self.nanPlot(point))
        fileMenu.addActions([f1])

        self.menuBar.addMenu(fileMenu)

        # toolbar

    def loadProcessList(self):
        pass
