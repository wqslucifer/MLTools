import os
import sys
import json
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QIcon
from project import ml_project
from customWidget import ModelWidget, DataWidget, ProjectWidget
from customLayout import FlowLayout
from dataWidget import DataTabWidget


class MainFrame(QMainWindow):
    def __init__(self, parent=None):
        super(MainFrame, self).__init__(parent)
        self.ui = loadUi('MainFrame.ui', self)
        self.setWindowIcon(QIcon('./MLTool.ico'))
        self.trayIcon = QSystemTrayIcon(QIcon('./MLTool.ico'))
        # main window tools
        self.toolBar = QToolBar(self)
        self.statusBar = QStatusBar(self)

        self.openAction = QAction(QIcon('./res/Open.ico'), 'Open', self)
        self.openAction.setStatusTip('Open')
        self.toolBar.addAction(self.openAction)
        self.addToolBar(self.toolBar)
        self.statusBar.setContentsMargins(10, 0, 0, 10)
        self.setStatusBar(self.statusBar)
        self.count = 0
        # local data
        self.MLProject = None
        self.fullProjectDir = None
        # start tab
        self.startTab = None
        self.startTabLayout = FlowLayout()
        # setting file
        self.settingFile = None
        self.projectOpenHistory = dict()
        self.defaultDir = 'E:/project'

        self.mainWidget = QWidget(self)
        self.mainLayout = QGridLayout(self.mainWidget)
        self.explorer = QTabWidget(self)
        self.tabWindow = QTabWidget(self)
        self.fileExplorer = QTreeWidget(self)
        # init ui for mainframe
        self.initUI()
        self.initTabAndExplorer()
        self.initSetting()

    def initUI(self):
        # set main layout and splitter
        splitterMain = QSplitter(Qt.Horizontal)
        leftWidget = QWidget(splitterMain)
        leftLayout = QVBoxLayout(leftWidget)
        leftLayout.addWidget(self.explorer)

        rightWidget = QWidget(splitterMain)
        rightLayout = QVBoxLayout(rightWidget)
        rightLayout.addWidget(self.tabWindow)

        self.mainLayout.addWidget(splitterMain)
        self.setCentralWidget(self.mainWidget)

        splitterMain.setStretchFactor(0, 1)
        splitterMain.setStretchFactor(1, 10)
        splitterMain.setCollapsible(0, False)
        splitterMain.setCollapsible(1, False)

        # set menu
        openProjectMenu = self.ui.actionOpen_Project
        openProjectMenu.triggered.connect(self.openProjectDialog)
        addFilesMenu = self.ui.actionAddFile
        addFilesMenu.triggered.connect(self.addFiles)
        createProjectMenu = self.ui.actionCreate_Project
        createProjectMenu.triggered.connect(self.createProject)

    def createProject(self):
        c = CreateProjectDialog()
        c.setModal(True)
        c.show()
        r = c.exec_()
        if r == QDialog.Accepted:
            self.fullProjectDir = c.fullProjectDir
            # create project dirs
            os.mkdir(self.fullProjectDir)
            for d in ['data', 'log', 'models', 'script', 'results']:
                tmpDir = os.path.join(self.fullProjectDir, d)
                if not os.path.exists(tmpDir):
                    os.mkdir(tmpDir)
            self.MLProject = ml_project.initProject(self.fullProjectDir)
            self.MLProject.projectName = c.projectName
            self.MLProject.projectDir = self.fullProjectDir
            self.MLProject.projectFile = os.path.abspath(
                os.path.join(self.fullProjectDir, self.MLProject.projectName + '.mlproj'))
            # create project file
            self.MLProject.dumpProject(self.MLProject.projectName + '.mlproj')
            # create project open history
            if os.path.exists(os.path.join('./', 'setting.ml')):
                self.loadSetting(os.path.join('./', 'setting.ml'))
            else:
                with open(os.path.join('./', 'setting.ml'), 'w') as _:
                    self.settingFile = os.path.join('./', 'setting.ml')

    def openProjectDialog(self):
        dialog = QFileDialog(self)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialog.setDirectory(self.defaultDir)
        projectFile, _ = dialog.getOpenFileName(self, "Open Project", "",
                                                "Project File (*.mlproj);;All Files (*.*)", options=options)
        if len(projectFile):
            self.openProject(projectFile)

    def addFiles(self):
        dialog = AddFileDialog(self.MLProject)
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
        self.MLProject = dialog.MLProject

    def initTabAndExplorer(self):
        # create scroll area
        scrollarea = QScrollArea(self)
        scrollarea.setWidgetResizable(True)
        scrollbar = QScrollBar(self)
        # create widget
        self.startTab = QWidget(scrollarea)
        self.startTab.setLayout(self.startTabLayout)
        # add scroll area to tab window
        self.tabWindow.addTab(scrollarea, 'Start')
        # add tab detail widget to scroll area
        scrollarea.setWidget(self.startTab)
        scrollarea.setVerticalScrollBar(scrollbar)
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.addOpenHistory()
        # init explore tab
        self.explorer.addTab(self.fileExplorer, 'File')
        self.explorer.setMinimumWidth(200)

    def initProjectTab(self):
        # create scroll area
        scrollarea = QScrollArea(self)
        scrollarea.setWidgetResizable(True)
        scrollbar = QScrollBar(self)
        # clean start tab and layout
        del self.startTab, self.startTabLayout
        self.startTabLayout = FlowLayout()
        # create widget
        self.startTab = QWidget(scrollarea)
        self.startTab.setLayout(self.startTabLayout)
        # add scroll area to tab window
        self.tabWindow.addTab(scrollarea, 'Project')
        # add tab detail widget to scroll area
        scrollarea.setWidget(self.startTab)
        scrollarea.setVerticalScrollBar(scrollbar)
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # add model data and results
        if self.MLProject.dataFiles_csv:
            for d in self.MLProject.dataFiles_csv:
                dw = DataWidget('csv', d, self)
                dw.triggered.connect(self.addDataTab)
                self.startTabLayout.addWidget(dw)

    def addModelTab(self):
        if os.path.exists(self.fullProjectDir):
            raise Exception("project dir exist")

    def addOpenHistory(self):
        # add item to tab
        projectOpenHistory = self.getSetting('projectOpenHistory')
        for d in projectOpenHistory.items():
            projectItem = ProjectWidget(d[0], d[1])
            projectItem.triggered.connect(self.openProject)
            self.startTabLayout.addWidget(projectItem)

    def openProject(self, projectFile):
        self.MLProject = ml_project.loadProject(projectFile)
        self.initUI_Project()
        # save open history
        projectOpenHistory = self.getSetting('projectOpenHistory')
        openTime = time.ctime()
        projectOpenHistory[self.MLProject.projectName] = [openTime, self.MLProject.projectDir,
                                                          self.MLProject.projectFile]
        self.updateSetting('projectOpenHistory', projectOpenHistory)
        # clean start tab, switch to project start page
        self.tabWindow.removeTab(0)
        self.initProjectTab()

    def initUI_Project(self):
        # init models
        windowTitle = self.MLProject.projectName + '[' + self.MLProject.projectDir + '] -- MLTools'
        self.setWindowTitle(windowTitle)

    def updateSetting(self, key, value):
        with open('setting.ml', 'r') as f:
            setting = json.load(f)
        setting[key] = value
        with open('setting.ml', 'w') as f:
            json.dump(setting, f)

    def getSetting(self, key):
        if os.path.exists('setting.ml'):
            with open('setting.ml', 'r') as f:
                setting = json.load(f)
                return setting[key]
        else:
            raise Exception('no setting file')

    def initSetting(self):
        if not os.path.exists('setting.ml'):
            setting = dict()
            setting['projectOpenHistory'] = dict()  # element: {'projectName':[time, projectDir, projectFile]}
            with open('setting.ml', 'w') as f:
                json.dump(setting, f)

    def addDataTab(self, dataFile):
        scrollarea = QScrollArea(self)
        scrollarea.setWidgetResizable(True)
        scrollbar = QScrollBar(self)
        # add scroll area to tab window
        self.tabWindow.addTab(scrollarea, os.path.basename(dataFile))
        self.tabWindow.setCurrentIndex(self.tabWindow.indexOf(scrollarea))
        # add tab detail widget to scroll area
        scrollarea.setWidget(DataTabWidget(dataFile))
        scrollarea.setVerticalScrollBar(scrollbar)
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)


class CreateProjectDialog(QDialog):
    def __init__(self):
        super(CreateProjectDialog, self).__init__()
        self.defaultLocation = 'E:/project'
        self.defaultName = 'Undefined'
        self.defaultDir = 'E:/project'
        self.projectLocation = self.defaultLocation
        self.projectName = self.defaultName
        self.fullProjectDir = os.path.abspath(os.path.join(self.defaultLocation, self.defaultName))

        self.ui = loadUi('CreateProject.ui', self)
        self.mainLayout = QGridLayout(self)
        self.setLayout(self.mainLayout)
        self.setFixedSize(650, 400)

        # project name layout
        self.projectnameLayout = QHBoxLayout(self)
        self.projectnameLayout.addWidget(QLabel("Project Name: "))
        self.projectnameLayout.addSpacing(1)
        self.projectnameEdit = QLineEdit(self)
        self.projectnameEdit.setText(self.defaultName)
        self.projectnameEdit.textChanged.connect(self.updateEdit)
        self.projectnameLayout.addWidget(self.projectnameEdit)
        self.projectnameLayout.addSpacing(81)

        # location layout
        self.locationLayout = QHBoxLayout(self)
        self.locationLayout.addWidget(QLabel("Location: "))
        self.locationLayout.addSpacing(25)
        self.locationEdit = QLineEdit(self)
        self.locationEdit.setText(os.path.abspath(os.path.join(self.defaultLocation, self.defaultName)))
        self.locBrowseButton = QPushButton("Browse", self)
        self.locationLayout.addWidget(self.locationEdit)
        self.locationLayout.addWidget(self.locBrowseButton)
        self.locBrowseButton.clicked.connect(self.locationDialog)

        # file layout
        self.addFileLayout = QHBoxLayout(self)
        self.addFileLayout.addWidget(QLabel("Files: "))
        self.addFileLayout.addSpacing(44)
        self.addFileEdit = QLineEdit(self)
        self.addFileBrowseButton = QPushButton("Browse", self)
        self.addFileLayout.addWidget(self.addFileEdit)
        self.addFileLayout.addWidget(self.addFileBrowseButton)

        # main layout
        self.mainLayout.addLayout(self.projectnameLayout, 1, 0, Qt.AlignTop)
        self.mainLayout.addLayout(self.locationLayout, 2, 0, Qt.AlignTop)
        self.mainLayout.addLayout(self.addFileLayout, 3, 0, Qt.AlignTop)
        buttonlayout = QHBoxLayout(self)
        buttonlayout.addWidget(self.ui.pushButtonOK)
        buttonlayout.addWidget(self.ui.pushButtonCancel)
        buttonlayout.setContentsMargins(0, 0, 10, 10)
        self.initExistCheck = QCheckBox('init using exist project', self)
        self.mainLayout.addWidget(self.initExistCheck, 4, 0, Qt.AlignLeft | Qt.AlignTop)
        self.mainLayout.addLayout(buttonlayout, 5, 0, Qt.AlignRight)
        self.initExistCheck.setFont(QFont("Arial", 10, QFont.Times))

        self.mainLayout.setRowStretch(0, 1)
        self.mainLayout.setRowStretch(1, 3)
        self.mainLayout.setRowStretch(2, 3)
        self.mainLayout.setRowStretch(3, 3)
        self.mainLayout.setRowStretch(4, 20)

        # button OK
        self.ui.pushButtonOK.clicked.connect(self.checkExist)
        self.ui.pushButtonCancel.clicked.connect(self.cancelDialog)

    def checkExist(self):
        self.fullProjectDir = os.path.abspath(os.path.join(self.projectLocation, self.projectName))
        print(self.fullProjectDir)
        if os.path.exists(self.fullProjectDir):
            QMessageBox.information(self, 'Project Exist', 'Project Exist, select other directory')
        else:
            self.done(QDialog.Accepted)

    def cancelDialog(self):
        self.done(QDialog.Rejected)

    def locationDialog(self):
        dialog = QFileDialog(self)
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        self.projectLocation = dialog.getExistingDirectory(self, "Project Location", self.defaultDir, options=options)
        self.locationEdit.setText(os.path.abspath(os.path.join(self.projectLocation, self.projectName)))

    def updateEdit(self, context: str):
        self.locationEdit.setText(os.path.abspath(os.path.join(self.projectLocation, context)))
        self.projectName = context


class AddFileDialog(QDialog):
    def __init__(self, MLProject):
        super(AddFileDialog, self).__init__()
        self.mainLayout = QGridLayout(self)
        self.setLayout(self.mainLayout)
        self.setFixedSize(650, 400)
        self.MLProject = MLProject
        # add data
        self.addDataLayout = QHBoxLayout(self)
        self.addDataLayout.setContentsMargins(0, 10, 0, 0)
        self.addDataLayout.addWidget(QLabel("Data: "))
        self.addDataLayout.addSpacing(25)
        self.addDataEdit = QLineEdit(self)
        self.addDataButton = QPushButton("Browse", self)
        self.addDataLayout.addWidget(self.addDataEdit)
        self.addDataLayout.addWidget(self.addDataButton)
        self.addDataButton.clicked.connect(self.addDataDialog)
        # add model
        self.addModelLayout = QHBoxLayout(self)
        self.addModelLayout.addWidget(QLabel("Model: "))
        self.addModelLayout.addSpacing(20)
        self.addModelEdit = QLineEdit(self)
        self.addModelButton = QPushButton("Browse", self)
        self.addModelLayout.addWidget(self.addModelEdit)
        self.addModelLayout.addWidget(self.addModelButton)
        self.addModelButton.clicked.connect(self.addModelDialog)
        # Ok button
        self.buttonBoxLayout = QHBoxLayout(self)
        self.okButton = QPushButton('Ok', self)
        self.cancelButton = QPushButton('Cancel', self)

        self.okButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.cancelButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.okButton.setFixedSize(80, 25)
        self.cancelButton.setFixedSize(80, 25)
        self.buttonBoxLayout.addStretch(10)
        self.buttonBoxLayout.addWidget(self.okButton, Qt.AlignRight)
        self.buttonBoxLayout.addWidget(self.cancelButton)
        self.buttonBoxLayout.setSpacing(10)
        self.buttonBoxLayout.setContentsMargins(0, 0, 0, 10)
        # main layout
        self.mainLayout.addLayout(self.addDataLayout, 0, 0)
        self.mainLayout.addLayout(self.addModelLayout, 1, 0)
        self.mainLayout.addLayout(self.buttonBoxLayout, 2, 0, Qt.AlignBottom)
        self.mainLayout.setRowStretch(0, 3)
        self.mainLayout.setRowStretch(1, 3)
        self.mainLayout.setRowStretch(2, 10)

        self.okButton.clicked.connect(self.confirm)
        self.cancelButton.clicked.connect(self.cancel)
        # set follow in confirm dialog
        self.dataFiles = None
        self.modelFiles = None

    def addDataDialog(self):
        if not self.MLProject:
            QMessageBox.information(None, "No Project Found", "Please Open A Project", QMessageBox.Ok)
            return
        dialog = QFileDialog()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileTypes = "CSV File (*.csv);;" \
                    "Pickle File (*.pkl)"
        if os.path.exists(os.path.join(self.MLProject.projectDir, 'data')):
            dialog.setDirectory(os.path.join(self.MLProject.projectDir, 'data'))
        else:
            dialog.setDirectory(self.MLProject.projectDir)
        self.dataFiles, _ = dialog.getOpenFileNames(self, "Add Data Files", "", fileTypes,
                                                    options=options)  # return list
        s = ''
        for f in self.dataFiles:
            s += (os.path.basename(f) + ',')
        s = s[:-1]
        self.addDataEdit.setText(s)

    def addModelDialog(self):
        if not self.MLProject:
            QMessageBox.information(None, "No Project Found", "Please Open A Project", QMessageBox.Ok)
            return
        dialog = QFileDialog()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileTypes = "Model File (*.md);;"
        if os.path.exists(os.path.join(self.MLProject.projectDir, 'model')):
            dialog.setDirectory(os.path.join(self.MLProject.projectDir, 'model'))
        else:
            dialog.setDirectory(self.MLProject.projectDir)
        self.modelFiles, _ = dialog.getOpenFileNames(self, "Add Model Files", "", fileTypes,
                                                     options=options)  # return list
        s = ''
        for f in self.modelFiles:
            s += (os.path.basename(f) + ',')
        s = s[:-1]
        self.addModelEdit.setText(s)

    def confirm(self):
        if self.dataFiles:
            for file in self.dataFiles:
                if file.endswith('csv'):
                    self.MLProject.dataFiles_csv.append(file)
                elif file.endswith('pkl'):
                    self.MLProject.dataFiles_pkl.append(file)
        if self.modelFiles:
            for file in self.modelFiles:
                if file.endswith('md'):
                    self.MLProject.modelFiles.append(file)
        self.done(QDialog.Accepted)
        self.MLProject.dumpProject(self.MLProject.projectFile)

    def cancel(self):
        self.done(QDialog.Rejected)


def something():
    print("ERROR ERROR ERROR")


class ExceptionHandler(QtCore.QObject):
    errorSignal = QtCore.pyqtSignal()

    def __init__(self):
        super(ExceptionHandler, self).__init__()

    def handler(self, exctype, value, traceback):
        self.errorSignal.emit()
        sys._excepthook(exctype, value, traceback)


exceptionHandler = ExceptionHandler()
sys._excepthook = sys.excepthook
sys.excepthook = exceptionHandler.handler

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainFrame()
    window.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
