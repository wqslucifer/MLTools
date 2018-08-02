import os
import sys
import json
import time
import subprocess
import signal
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QIcon
from customWidget import ModelWidget, DataWidget, ProjectWidget, ScriptWidget, CollapsibleTabWidget
from customLayout import FlowLayout
from tabWidget import DataTabWidget, IpythonTabWidget, process_thread_pipe, IpythonWebView, log, ModelTabWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from SwitchButton import switchButton
from model import ml_model
from project import ml_project
from multiprocessing import Queue

class MainFrame(QMainWindow):
    subprocessEnd = pyqtSignal()
    def __init__(self, parent=None):
        super(MainFrame, self).__init__(parent)
        self.ui = loadUi('MainFrame.ui', self)
        self.setWindowIcon(QIcon('./MLTool.ico'))
        self.trayIcon = QSystemTrayIcon(QIcon('./MLTool.ico'))
        self.setAttribute(Qt.WA_DeleteOnClose)
        # main window tools
        self.toolBar = QToolBar(self)
        self.statusBar = QStatusBar(self)
        self.statusBar.setContentsMargins(10, 0, 0, 10)
        self.addToolBar(self.toolBar)
        self.setStatusBar(self.statusBar)
        # init tool bar
        self.openAction = None
        self.modelAction = None
        # local data
        self.MLProject = None
        self.fullProjectDir = None
        self.MLModels = list()
        self.localsetting = dict()
        # start tab
        self.startTab = None
        self.startTabLayout = FlowLayout()
        # setting file
        self.popNewIpythonTab = False
        self.settingFile = None
        self.projectOpenHistory = dict()
        self.defaultDir = 'E:/project'

        self.mainWidget = QWidget(self)
        self.mainLayout = QGridLayout(self.mainWidget)
        self.explorer = QTabWidget(self)
        self.tabWindow = QTabWidget(self)
        self.tabList = list()
        self.fileExplorer = QTreeWidget(self)
        # init ui for mainframe
        self.initSetting()
        self.initUI()
        self.initTabAndExplorer()

    def initUI(self):
        # set main layout and splitter
        splitterMain = QSplitter(Qt.Horizontal)
        leftWidget = QWidget(splitterMain)
        leftLayout = QVBoxLayout(leftWidget)
        leftLayout.addWidget(self.explorer)
        self.explorer.setTabPosition(QTabWidget.West)

        rightWidget = QWidget(splitterMain)
        rightLayout = QVBoxLayout(rightWidget)
        self.tabWindow.setTabsClosable(True)
        self.tabWindow.tabCloseRequested.connect(self.closeTab)
        rightLayout.addWidget(self.tabWindow)

        self.mainLayout.addWidget(splitterMain)
        self.setCentralWidget(self.mainWidget)

        splitterMain.setStretchFactor(0, 1)
        splitterMain.setStretchFactor(1, 10)
        splitterMain.setCollapsible(0, False)
        splitterMain.setCollapsible(1, False)
        # tool bar
        # open
        self.openAction = QAction(QIcon('./res/Open.ico'), 'Open Project', self)
        self.openAction.setStatusTip('Open Project')
        self.openAction.triggered.connect(self.openProjectDialog)
        self.toolBar.addAction(self.openAction)
        # model
        self.modelAction = QAction(QIcon('./res/Model.ico'), 'Create Model', self)
        self.modelAction.setStatusTip('Create Model')
        self.modelAction.triggered.connect(self.createModel)
        self.toolBar.addAction(self.modelAction)
        # set menu
        openProjectMenu = self.ui.actionOpen_Project
        openProjectMenu.triggered.connect(self.openProjectDialog)
        addFilesMenu = self.ui.actionAddFile
        addFilesMenu.triggered.connect(self.addFiles)
        createProjectMenu = self.ui.actionCreate_Project
        createProjectMenu.triggered.connect(self.createProject)
        settingMenu = self.ui.actionSetting
        settingMenu.triggered.connect(self.setting)

    def createProject(self):
        c = CreateProjectDialog()
        c.setModal(True)
        c.show()
        r = c.exec_()
        if r == QDialog.Accepted:
            self.fullProjectDir = c.fullProjectDir
            # create project dirs
            if not os.path.exists(self.fullProjectDir):
                os.mkdir(self.fullProjectDir)
            for d in ['data', 'log', 'model', 'script', 'result']:
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
                # self.loadSetting(os.path.join('./', 'setting.ml'))
                pass
            else:
                with open(os.path.join('./', 'setting.ml'), 'w') as _:
                    self.settingFile = os.path.join('./', 'setting.ml')
        self.openProject(self.MLProject.projectFile)

    def openProjectDialog(self):
        dialog = QFileDialog(self)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialog.setDirectory(self.defaultDir)
        projectFile, _ = dialog.getOpenFileName(self, "Open Project", "",
                                                "Project File (*.mlproj);;All Files (*.*)", options=options)
        if len(projectFile):
            self.openProject(projectFile)

    def setting(self):
        settingLayout = QGridLayout(self)
        settingDialog = QDialog(self)
        settingDialog.setFixedSize(400, 250)
        settingDialog.setLayout(settingLayout)
        # set pop ipython
        ifpopLayout = QHBoxLayout(self)
        ifpopLayout.addWidget(QLabel('Pop Ipython Dialog', self))
        switch = switchButton()
        switch.toggled.connect(self.onPopNewIpythonTab)
        ifpopLayout.addWidget(switch)
        switch.setToggle(self.popNewIpythonTab)

        # add widget
        settingLayout.addLayout(ifpopLayout, 0, 0)
        settingDialog.exec()

    def addFiles(self):
        if not self.MLProject:
            QMessageBox.information(None, "No Project Found", "Please Open A Project", QMessageBox.Ok)
            return
        dialog = AddFileDialog(self.MLProject)
        dialog.setModal(True)
        dialog.show()
        dialog.exec_()
        self.MLProject = dialog.MLProject
        self.openProject(self.MLProject.projectFile)

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
        currentIndex = None
        scrollarea = QScrollArea(self)
        scrollarea.setWidgetResizable(True)
        scrollbar = QScrollBar(self)
        # clean start tab and layout
        if len(self.tabList):
            currentIndex = self.tabWindow.currentIndex() + 1
            self.tabList.remove(self.startTab)
            del self.startTab, self.startTabLayout
        self.startTabLayout = FlowLayout()
        # create widget
        self.startTab = QWidget(scrollarea)
        self.startTab.setLayout(self.startTabLayout)
        # add scroll area to tab window
        self.tabWindow.insertTab(0, scrollarea, 'Project')
        if currentIndex:
            self.tabWindow.setCurrentIndex(currentIndex)
        # add tab detail widget to scroll area\
        self.tabList.insert(0, self.startTab)
        scrollarea.setWidget(self.startTab)
        scrollarea.setVerticalScrollBar(scrollbar)
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # add model data and result
        if self.MLProject.dataFiles_csv:
            for d in self.MLProject.dataFiles_csv:
                dw = DataWidget('csv', d, self)
                dw.triggered.connect(self.addDataTab)
                self.startTabLayout.addWidget(dw)
        if self.MLProject.scriptFiles:
            for d in self.MLProject.scriptFiles:
                if d.endswith('py'):
                    sw = ScriptWidget('py', d, self)
                elif d.endswith('ipynb'):
                    sw = ScriptWidget('ipynb', d, self)
                sw.triggered.connect(self.addScriptTab)
                self.startTabLayout.addWidget(sw)
        if self.MLProject.modelFiles:
            for d in self.MLProject.modelFiles:
                mw = ModelWidget(d)
                mw.triggered.connect(self.addModelTab)
                self.startTabLayout.addWidget(mw)

    def addModelTab(self, MLModel: ml_model):
        modelTab = ModelTabWidget(MLModel, self.MLProject, self)
        self.tabWindow.addTab(modelTab, MLModel.modelName)
        self.tabWindow.setCurrentIndex(self.tabWindow.indexOf(modelTab))
        self.tabList.append(modelTab)

    def addDataTab(self, dataFile):
        scrollarea = QScrollArea(self)
        scrollarea.setWidgetResizable(True)
        scrollbar = QScrollBar(self)
        # add scroll area to tab window
        self.tabWindow.addTab(scrollarea, os.path.basename(dataFile))
        self.tabWindow.setCurrentIndex(self.tabWindow.indexOf(scrollarea))
        # add tab detail widget to scroll area
        dw = DataTabWidget(dataFile)
        self.tabList.append(dw)
        scrollarea.setWidget(dw)
        scrollarea.setVerticalScrollBar(scrollbar)
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def addScriptTab(self, scriptFile: str):
        scrollarea = QScrollArea(self)
        scrollarea.setWidgetResizable(True)
        scrollbar = QScrollBar(self)
        # add scroll area to tab window
        self.tabWindow.addTab(scrollarea, os.path.basename(scriptFile))
        self.tabWindow.setCurrentIndex(self.tabWindow.indexOf(scrollarea))
        # add tab detail widget to scroll area
        if scriptFile.endswith('.ipynb'):
            ipythonTab = IpythonTabWidget(self.fullProjectDir, self)
            ipythonTab.basewebview.newIpython.connect(self.newIpython)
            self.subprocessEnd.connect(ipythonTab.delProcess)
            scrollarea.setWidget(ipythonTab)
            self.tabList.append(ipythonTab)
        elif scriptFile.endswith('.py'):
            # self.tabList.append()
            pass
            # scrollarea.setWidget(ScriptTabWidget(scriptFile))
        scrollarea.setVerticalScrollBar(scrollbar)
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def newIpython(self, newview: QWebEngineView):
        if not self.popNewIpythonTab:
            scrollarea = QScrollArea(self)
            scrollarea.setWidgetResizable(True)
            scrollbar = QScrollBar(self)
            self.tabWindow.addTab(scrollarea, os.path.basename('newIp'))
            self.tabWindow.setCurrentIndex(self.tabWindow.indexOf(scrollarea))
            self.tabList.append(newview)
            scrollarea.setWidget(newview)
            scrollarea.setVerticalScrollBar(scrollbar)
            scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def addOpenHistory(self):
        # add item to tab
        projectOpenHistory = self.getSetting('projectOpenHistory')
        NotExistProjects = []
        if projectOpenHistory:
            for d in projectOpenHistory.items():
                if os.path.exists(d[1][2]):
                    projectItem = ProjectWidget(d[0], d[1])
                    projectItem.triggered.connect(self.openProject)
                    self.startTabLayout.addWidget(projectItem)
                else:
                    NotExistProjects.append(d[0])
        else:
            # add create project button to tab
            pass
        if NotExistProjects:
            for d in NotExistProjects:
                projectOpenHistory.pop(d)
            with open('setting.ml', 'w') as f:
                json.dump(self.localsetting, f)

    def openProject(self, projectFile):
        self.MLProject = ml_project.loadProject(projectFile)
        # init local variable
        self.fullProjectDir = self.MLProject.projectDir
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
                self.localsetting = json.load(f)
                return self.localsetting[key]
        else:
            return None

    def initSetting(self):
        if not os.path.exists('setting.ml'):
            self.localsetting = dict()
            self.localsetting['projectOpenHistory'] = dict()  # element: {'projectName':[time, projectDir, projectFile]}
            with open('setting.ml', 'w') as f:
                json.dump(self.localsetting, f)

    def closeEvent(self, *args, **kwargs):
        del self.trayIcon
        self.subprocessEnd.emit()

    def closeTab(self, index):
        if not index == 0:
            if isinstance(self.tabList[index], IpythonTabWidget):
                if len(self.tabList[index].windows):
                    r = QMessageBox.information(self, 'Close Tab', 'If Colse sub tabs',
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if r == QMessageBox.No:
                        return
                    else:
                        # remove all sub tab
                        while True:
                            f = True
                            for subIndex in range(len(self.tabList)):
                                if isinstance(self.tabList[subIndex], QWebEngineView):
                                    self.tabList[subIndex].close()
                                    self.tabList.remove(self.tabList[subIndex])
                                    self.tabWindow.removeTab(subIndex)
                                    f = False
                                    break
                            if f:
                                break
            elif isinstance(self.tabList[index], QWebEngineView):
                pass
            self.tabList[index].close()
            self.tabList.remove(self.tabList[index])
            self.tabWindow.removeTab(index)

    def onPopNewIpythonTab(self, value):
        self.popNewIpythonTab = value

    def createModel(self):
        if not self.MLProject:
            QMessageBox.information(None, "No Project Found", "Please Open A Project", QMessageBox.Ok)
            return
        dialog = createModelDialog(self.MLProject)
        r = dialog.exec_()
        if r == QDialog.Accepted:
            newModel = ml_model(dialog.modelType, dialog.modelName, dialog.modelLocation)
            self.MLModels.append(newModel)
            newModel.dumpModel()
            self.MLProject.modelFiles.append(newModel.modelFile)
            self.MLProject.dumpProject(self.MLProject.projectFile)
            # add tab and jump to it
            c = ModelTabWidget(newModel, self.MLProject)
            self.tabWindow.addTab(c, dialog.modelName)
            self.tabWindow.setCurrentIndex(len(self.tabList))
            self.tabList.append(c)


class createModelDialog(QDialog):
    def __init__(self, MLProject: ml_project):
        super(createModelDialog, self).__init__()
        self.setWindowIcon(QIcon('MLTool.ico'))
        self.modelTypeList = ['XGB', 'LGBM', 'RandomForest', 'LinearReg', 'LogisticReg', 'Ridge', 'Lasso', 'ElasticNet']
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedSize(600, 400)
        self.dialogLayout = QVBoxLayout(self)
        self.dialogLayout.setAlignment(Qt.AlignTop)
        self.setLayout(self.dialogLayout)
        self.dialogLayout.setSpacing(10)
        self.MLProject = MLProject
        # model type
        self.comboBoxLayout = QHBoxLayout(self)
        self.comboBox = QComboBox(self)
        self.comboBox.addItem('xgboost', 'xgboost_model')
        self.comboBox.addItem('lightgbm', 'lightgbm_model')
        self.comboBox.addItem('linear model', 'linear_model')
        self.comboBoxLayout.addWidget(QLabel('Model Type: ', self), 1)
        self.comboBoxLayout.addWidget(self.comboBox, 5)
        self.modelType = self.modelTypeList[self.comboBox.currentIndex()]
        # model name
        self.modelName = self.comboBox.currentData() + '.md'
        self.modelNameLayout = QHBoxLayout(self)
        self.modelNameEditor = QLineEdit(self)
        self.modelNameEditor.setText(self.modelName)
        self.modelNameLayout.addWidget(QLabel('Model Name: ', self), 1)
        self.modelNameLayout.addWidget(self.modelNameEditor, 5)
        # model save location
        self.modelLocation = os.path.join(self.MLProject.projectDir, self.MLProject.modelDir)
        self.modelLocationLayout = QHBoxLayout(self)
        self.modelLocationEdit = QLineEdit(self)
        self.modelLocationEdit.setText(os.path.join(self.modelLocation, self.modelName))
        self.modelLocationBrowse = QPushButton('Browse', self)
        self.modelLocationLayout.addWidget(QLabel('Model Location: ', self), 2)
        self.modelLocationLayout.addWidget(self.modelLocationEdit, 8)
        self.modelLocationLayout.addWidget(self.modelLocationBrowse, 2)
        # confirm button
        self.confirmButton = QPushButton('Confirm', self)
        self.cancelButton = QPushButton('Cancel', self)
        self.buttonLayout = QHBoxLayout(self)
        self.buttonLayout.setAlignment(Qt.AlignRight)
        self.buttonLayout.addWidget(self.confirmButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.setContentsMargins(0, 0, 20, 20)

        self.dialogLayout.addLayout(self.comboBoxLayout)
        self.dialogLayout.addLayout(self.modelNameLayout)
        self.dialogLayout.addLayout(self.modelLocationLayout)
        self.dialogLayout.addStretch(10)
        self.dialogLayout.addLayout(self.buttonLayout)

        self.modelNameEditor.textChanged.connect(self.updateModelName)
        self.modelLocationBrowse.clicked.connect(self.modelLocationDialog)
        self.comboBox.currentIndexChanged.connect(self.updateDefaultModelName)
        self.confirmButton.clicked.connect(self.onConfirm)
        self.cancelButton.clicked.connect(self.onCancel)

    def onConfirm(self):
        self.done(QDialog.Accepted)

    def onCancel(self):
        self.done(QDialog.Rejected)

    def updateModelName(self, newModelName):
        self.modelName = newModelName
        self.modelLocationEdit.setText(os.path.join(self.modelLocation, self.modelName))

    def updateDefaultModelName(self, index):
        self.modelName = self.comboBox.itemData(index) + '.md'
        self.modelNameEditor.setText(self.modelName)
        self.modelType = self.modelTypeList[index]

    def modelLocationDialog(self):
        dialog = QFileDialog(self)
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        self.modelLocation = dialog.getExistingDirectory(self, "Modle Location",
                                                         os.path.join(self.MLProject.projectDir,
                                                                      self.MLProject.modelDir),
                                                         options=options)
        self.modelLocationEdit.setText(os.path.abspath(os.path.join(self.MLProject.projectDir, self.modelName)))


class CreateProjectDialog(QDialog):
    def __init__(self):
        super(CreateProjectDialog, self).__init__()
        self.defaultLocation = 'E:/project'
        self.defaultName = 'Undefined'
        self.defaultDir = 'E:/project'
        self.setWindowIcon(QIcon('MLTool.ico'))
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
        if os.path.exists(os.path.join(self.fullProjectDir, self.projectName)):
            QMessageBox.information(self, 'Project Exist', 'Project Exist, select other directory')
            self.done(QDialog.Rejected)
        elif os.path.exists(self.fullProjectDir):
            QMessageBox.information(self, 'ProjectDir Exist', 'Create project uses exist dir')
            self.done(QDialog.Accepted)
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
        self.setWindowIcon(QIcon('MLTool.ico'))
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
        # add script
        self.addScriptLayout = QHBoxLayout(self)
        self.addScriptLayout.addWidget(QLabel("Script: "))
        self.addScriptLayout.addSpacing(20)
        self.addScriptEdit = QLineEdit(self)
        self.addScriptButton = QPushButton("Browse", self)
        self.addScriptLayout.addWidget(self.addScriptEdit)
        self.addScriptLayout.addWidget(self.addScriptButton)
        self.addScriptButton.clicked.connect(self.addScriptDialog)
        # add result
        self.addResultLayout = QHBoxLayout(self)
        self.addResultLayout.addWidget(QLabel("Result: "))
        self.addResultLayout.addSpacing(20)
        self.addResultEdit = QLineEdit(self)
        self.addResultButton = QPushButton("Browse", self)
        self.addResultLayout.addWidget(self.addResultEdit)
        self.addResultLayout.addWidget(self.addResultButton)
        self.addResultButton.clicked.connect(self.addResultDialog)
        # add log
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
        self.mainLayout.addLayout(self.addScriptLayout, 2, 0)
        self.mainLayout.addLayout(self.addResultLayout, 3, 0)
        self.mainLayout.addLayout(self.buttonBoxLayout, 4, 0, Qt.AlignBottom)
        self.mainLayout.setRowStretch(0, 3)
        self.mainLayout.setRowStretch(1, 3)
        self.mainLayout.setRowStretch(2, 3)
        self.mainLayout.setRowStretch(3, 3)
        self.mainLayout.setRowStretch(4, 10)

        self.okButton.clicked.connect(self.confirm)
        self.cancelButton.clicked.connect(self.cancel)
        # set follow in confirm dialog
        self.dataFiles = None
        self.modelFiles = None
        self.scriptFiles = None
        self.resultFiles = None

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
        fileTypes = "Model File (*.md)"
        if os.path.exists(os.path.join(self.MLProject.projectDir, 'model')):
            dialog.setDirectory(os.path.join(self.MLProject.projectDir, 'model'))
        else:
            dialog.setDirectory(self.MLProject.projectDir)
        self.modelFiles, _ = dialog.getOpenFileNames(self, "Add Model Files", "", fileTypes,
                                                     options=options)  # return list
        s = ''
        for f in self.modelFiles:
            s += (os.path.basename(f) + ',')
            self.MLProject.modelFiles.append(f)
        s = s[:-1]
        self.addModelEdit.setText(s)

    def addScriptDialog(self):
        if not self.MLProject:
            QMessageBox.information(None, "No Project Found", "Please Open A Project", QMessageBox.Ok)
            return
        dialog = QFileDialog()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileTypes = "Python File (*.py);; Jupyter NoteBook (*.ipynb);; Script File (*.py *.ipynb)"
        if os.path.exists(os.path.join(self.MLProject.projectDir, 'script')):
            dialog.setDirectory(os.path.join(self.MLProject.projectDir, 'script'))
        else:
            dialog.setDirectory(self.MLProject.projectDir)
        self.scriptFiles, _ = dialog.getOpenFileNames(self, "Add script Files", "", fileTypes,
                                                      options=options)  # return list
        s = ''
        for f in self.scriptFiles:
            s += (os.path.basename(f) + ',')
        s = s[:-1]
        self.addScriptEdit.setText(s)

    def addResultDialog(self):
        if not self.MLProject:
            QMessageBox.information(None, "No Project Found", "Please Open A Project", QMessageBox.Ok)
            return
        dialog = QFileDialog()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileTypes = "Result File (*.mlr)"
        if os.path.exists(os.path.join(self.MLProject.projectDir, 'result')):
            dialog.setDirectory(os.path.join(self.MLProject.projectDir, 'result'))
        else:
            dialog.setDirectory(self.MLProject.projectDir)
        self.resultFiles, _ = dialog.getOpenFileNames(self, "Add result Files", "", fileTypes,
                                                      options=options)  # return list
        s = ''
        for f in self.resultFiles:
            s += (os.path.basename(f) + ',')
        s = s[:-1]
        self.addResultEdit.setText(s)

    def confirm(self):
        if self.dataFiles:
            for file in self.dataFiles:
                if file.endswith('csv') and file not in self.MLProject.dataFiles_csv:
                    self.MLProject.dataFiles_csv.append(file)
                elif file.endswith('pkl') and file not in self.MLProject.dataFiles_pkl:
                    self.MLProject.dataFiles_pkl.append(file)
        if self.modelFiles:
            for file in self.modelFiles:
                if file.endswith('md') and file not in self.MLProject.modelFiles:
                    self.MLProject.modelFiles.append(file)
        if self.scriptFiles:
            for file in self.scriptFiles:
                if file not in self.MLProject.scriptFiles:
                    self.MLProject.scriptFiles.append(file)
        if self.resultFiles:
            for file in self.resultFiles:
                if file not in self.MLProject.resultFiles:
                    self.MLProject.resultFiles.append(file)

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
