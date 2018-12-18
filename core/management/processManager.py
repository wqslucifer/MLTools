import os
import hashlib
import pickle

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QIcon, QCursor, QCloseEvent
from PyQt5.QtCore import Qt, QAbstractTableModel, pyqtSignal, QModelIndex, QVariant, QPoint, QItemSelection

from core.project import ml_project
import GENERAL

GENERAL.init()


class processManagerDialog(QDialog):
    def __init__(self, MLProject: ml_project, parent=None):
        super(processManagerDialog, self).__init__(parent=parent)
        self.installDir = GENERAL.get_value('INSTALL_DIR')
        self.mainLayout = QVBoxLayout(self)
        self.upperLayout = QVBoxLayout(self)
        self.lowerLayout = QVBoxLayout(self)
        self.menuBar = QMenuBar(self)
        self.toolBar = QToolBar(self)
        self.processTable = QTableView(self)
        self.tableModel = functionModel(self)
        self.processTablePopMenu = QMenu(self)
        self.MLProject = MLProject
        # tool bar
        self.addProcessAction = None
        self.importProcessAction = None
        # data
        self.processList = []
        self.processDict = set()
        # self.curDir = GENERAL.get_value('INSTALL_DIR')
        self.initUI()
        self.initRightClickMenu()

    def initUI(self):
        self.setLayout(self.mainLayout)
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.upperLayout.addWidget(self.menuBar)
        self.upperLayout.addWidget(self.toolBar)
        self.lowerLayout.addWidget(self.processTable)
        self.lowerLayout.setContentsMargins(10, 0, 10, 10)
        self.mainLayout.addLayout(self.upperLayout)
        self.mainLayout.addLayout(self.lowerLayout)

        # menu
        fileMenu = QMenu('File', self)
        f1 = QAction('add process', self)
        f1.triggered.connect(self.addProcess)
        fileMenu.addActions([f1])
        self.menuBar.addMenu(fileMenu)

        # toolbar
        self.addProcessAction = QAction(QIcon('./res/add_red_small.ico'), 'add process', self)
        self.addProcessAction.setStatusTip('add process')
        self.addProcessAction.triggered.connect(self.addProcess)

        self.importProcessAction = QAction(QIcon('./res/import.ico'), 'import process', self)
        self.importProcessAction.setStatusTip('import process')
        self.importProcessAction.triggered.connect(self.importProcess)
        self.importProcessAction.setEnabled(False)
        self.toolBar.addActions([self.addProcessAction, self.importProcessAction])

        # table
        self.processTable.setModel(self.tableModel)
        self.processTable.autoScrollMargin()
        self.processTable.setSelectionBehavior(QTableView.SelectRows)
        self.processTable.selectionModel().selectionChanged.connect(self.itemSelected)
        # table double click
        self.processTable.doubleClicked.connect(self.editDescribe)
        self.tableModel.notEmpty.connect(lambda: self.setTableHeaderStyle())
        self.loadProcessList()

    def loadProcessList(self):
        localProcessFile = os.path.join(self.installDir, 'local', 'localProcess.ml')
        if os.path.exists(localProcessFile):
            with open(localProcessFile, 'rb') as f:
                self.processDict, self.processList = pickle.load(f)
                self.tableModel.loadProcessList(self.processList)
        else:
            print('local process file not exist')

    def saveProcessList(self):
        localProcessFile = os.path.join(self.installDir, 'local', 'localProcess.ml')
        with open(localProcessFile, 'wb') as f:
            pickle.dump((self.processDict, self.processList), f)

    def addProcess(self):
        dialog = addProcessDialog(self)
        r = dialog.exec_()
        index = len(self.processList)
        if r == QDialog.Accepted:
            for i, f in enumerate(dialog.functionList):
                f['describe'] = ''
                f['ID'] = hashlib.new('md5', ((f['name'] + f['path']).encode('UTF-8'))).hexdigest()
                if f['ID'] not in self.processDict:
                    self.processList.insert(index + i, f)
                    self.processDict.add(f['ID'])
            self.tableModel.addProcessList(self.processList)
        self.saveProcessList()

    def importProcess(self):
        pass

    def itemSelected(self, selected: QItemSelection, deselected: QItemSelection):
        print(selected, deselected)
        if selected.count() == 0:
            self.importProcessAction.setEnabled(False)
        else:
            self.importProcessAction.setEnabled(True)

    def delProcess(self, point: QPoint):
        if point:
            modelIndexList = self.processTable.selectionModel().selectedRows()
            modelIndex = [modelIndexList[i].row() for i in range(len(modelIndexList))]
        self.tableModel.beginResetModel()
        for row in modelIndex:
            p = self.processList.pop(row)
            self.processDict.remove(p['ID'])
        self.saveProcessList()
        self.tableModel.rows -= len(modelIndex)
        self.tableModel.endResetModel()

    def setTableHeaderStyle(self):
        self.processTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.processTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

    def initRightClickMenu(self):
        self.processTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.processTable.customContextMenuRequested.connect(self.onProcessTableRightClicked)

    def onProcessTableRightClicked(self, point: QPoint):
        self.processTablePopMenu.clear()
        # numeric
        m1 = QAction('delete process', self)
        m1.triggered.connect(lambda: self.delProcess(point))
        m2 = QAction('edit describe', self)
        m2.triggered.connect(lambda: self.editDescribe(point))
        m3 = QAction('edit source file', self)
        m3.triggered.connect(lambda: self.editSource(point))

        processTableActionList = [m1, m2, m3]
        self.processTablePopMenu.addActions(processTableActionList)
        # test action
        t1 = QAction('test', self)
        # t1.triggered.connect()
        self.processTablePopMenu.addAction(t1)
        # pop menu
        self.processTablePopMenu.exec(QCursor.pos())

    def editDescribe(self, point: QPoint):
        if isinstance(point, QPoint):
            row = self.processTable.indexAt(point).row()
        elif isinstance(point, QModelIndex):
            row = point.row()
        dialog = describeEditDialog(self.processList[row]['describe'], self)
        r = dialog.exec_()
        if r == QDialog.Accepted:
            self.processList[row]['describe'] = dialog.describe
            self.tableModel.update()

    def editSource(self, point: QPoint):
        index = self.processTable.indexAt(point)
        print(index.row(), index.column())
        pass

    def closeEvent(self, event: QCloseEvent):
        self.saveProcessList()
        event.accept()


class functionModel(QAbstractTableModel):
    notEmpty = pyqtSignal()

    def __init__(self, parent=None):
        super(functionModel, self).__init__(parent=parent)
        self.rows = 0
        self.cols = 7  # name, param_count, param,dependent, filename, path
        self.processList = None

    def addProcessList(self, processList):
        self.processList = processList
        self.update()

    def loadProcessList(self, processList):
        self.processList = processList
        self.rows = len(self.processList)
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rows, self.cols))
        if self.rows > 0:
            self.notEmpty.emit()

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
            if modelIndex.column() == 0:  # name
                return str(self.processList[modelIndex.row()]['name'])
            elif modelIndex.column() == 1:  # param_count
                return str(self.processList[modelIndex.row()]['param_count'])
            elif modelIndex.column() == 2:  # params
                return str(self.processList[modelIndex.row()]['param'])
            elif modelIndex.column() == 3:  # describe
                return str(self.processList[modelIndex.row()]['describe'])
            elif modelIndex.column() == 4:  # dependent
                return str(self.processList[modelIndex.row()]['dependent'])
            elif modelIndex.column() == 5:  # filename
                return str(self.processList[modelIndex.row()]['filename'])
            elif modelIndex.column() == 6:  # path
                return str(self.processList[modelIndex.row()]['path'])
        else:
            return QVariant()

    def headerData(self, section, orientation, role=None):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return ['Function Name', 'param:count', 'param:default', 'Describe', 'Dependent', 'Package Name', 'Path'][
                section]
        if orientation == Qt.Vertical:
            return [i + 1 for i in range(self.rows)][section]
        return QVariant()

    def flags(self, modelIndex):
        # flags = QAbstractTableModel.flags(self, modelIndex)
        flags = Qt.NoItemFlags
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        return flags

    def update(self):
        self.beginResetModel()
        self.rows = len(self.processList)
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rows, self.cols))
        self.endResetModel()
        if self.rows > 0:
            self.notEmpty.emit()


class addProcessDialog(QDialog):
    def __init__(self, parent=None):
        super(addProcessDialog, self).__init__(parent=parent)
        self.mainLayout = QVBoxLayout(self)
        self.fileLayout = QHBoxLayout(self)
        self.displayTable = QTableWidget(self)
        self.browserButton = QPushButton('Browser', self)
        self.browserButton.clicked.connect(self.onBrowserClicked)
        self.finishButton = QPushButton('Finish', self)
        self.finishButton.clicked.connect(self.onFinishClicked)
        self.lowerLayout = QHBoxLayout(self)
        self.installDir = GENERAL.get_value('INSTALL_DIR')
        self.defaultDir = self.installDir
        self.defaultColNum = 4  # function name, filename, param, location
        self.functionList = []
        self.initUI()

    def initUI(self):
        self.setLayout(self.mainLayout)
        self.setMinimumSize(500, 300)
        self.fileLayout.addWidget(QLabel('Import from File:', self))
        self.fileLayout.setAlignment(Qt.AlignLeft)
        # self.lowerLayout.addSpacing()
        self.lowerLayout.addWidget(self.browserButton)
        self.lowerLayout.addWidget(self.finishButton)
        self.lowerLayout.setAlignment(Qt.AlignRight)

        self.mainLayout.addLayout(self.fileLayout)
        self.mainLayout.addWidget(self.displayTable)
        self.mainLayout.addLayout(self.lowerLayout)

    def onBrowserClicked(self):
        dialog = QFileDialog(self)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialog.setDirectory(self.defaultDir)
        processFiles, _ = dialog.getOpenFileNames(self, "Add Process", "",
                                                  "Process File (*.py);;All Files (*.*)", options=options)
        if len(processFiles):
            self.addFiles(processFiles)

    def addFiles(self, fileList):
        self.displayTable.setRowCount(0)
        self.displayTable.setColumnCount(self.defaultColNum)
        self.displayTable.setHorizontalHeaderLabels(['function name', 'filename', 'param', 'location'])
        for file in fileList:
            packageInfo = self.importFromPy(file)
            self.functionList.extend(packageInfo['funcList'])  # function name, param, param len, filename, dependent
        for f in self.functionList:
            print(f['name'], f['param'], f['filename'], f['path'])
            self.displayTable.insertRow(self.displayTable.rowCount())
            self.displayTable.setItem(self.displayTable.rowCount() - 1, 0, QTableWidgetItem(f['name']))
            self.displayTable.setItem(self.displayTable.rowCount() - 1, 1, QTableWidgetItem(str(f['param'])))
            self.displayTable.setItem(self.displayTable.rowCount() - 1, 2, QTableWidgetItem(f['filename']))
            self.displayTable.setItem(self.displayTable.rowCount() - 1, 3, QTableWidgetItem(f['path']))
        self.displayTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

    def importFromPy(self, importedFile):
        # parse python file by string
        # get function name and params
        fileName = os.path.basename(importedFile)
        filePath = importedFile
        with open(importedFile, 'r') as f:
            packageInfo = dict()
            packageList = list()
            funcList = list()
            lines = f.readlines()
            # get import list
            for l in lines:
                if l.startswith('import '):
                    packageList.append(l.split()[1])
                elif l.startswith('def '):
                    funcInfo = dict()
                    funcName = l[4:l.find('(')]
                    argumentList = l[l.find('(') + 1:l.find(')')]
                    argumentList = [i.strip() for i in argumentList.split(',')]
                    param = dict()
                    for a in argumentList:
                        if '=' in a:
                            paramLine = [i.strip() for i in a.split('=')]
                            paramName = paramLine[0]
                            default = paramLine[1]
                        else:
                            paramName = a
                            default = None
                        param[paramName] = default
                    funcInfo['name'] = funcName
                    funcInfo['param'] = param
                    funcInfo['param_count'] = len(param)
                    funcInfo['filename'] = fileName
                    funcInfo['dependent'] = packageList
                    funcInfo['path'] = filePath
                    funcList.append(funcInfo)

            packageInfo['packageName'] = fileName
            packageInfo['funcList'] = funcList
            packageInfo['packageList'] = packageList
        return packageInfo

    def onFinishClicked(self):
        self.done(QDialog.Accepted)


class describeEditDialog(QDialog):
    def __init__(self, describe, parent=None):
        super(describeEditDialog, self).__init__(parent=parent)
        self.describe = describe
        self.mainLayout = QVBoxLayout(self)
        self.editor = QTextEdit(self)
        self.OKButton = QPushButton('OK', self)
        self.initUI()

    def initUI(self):
        self.setMinimumSize(200, 100)
        self.mainLayout.addWidget(self.editor)
        self.mainLayout.addWidget(self.OKButton, alignment=Qt.AlignRight)
        self.editor.setPlainText(self.describe)
        self.editor.textChanged.connect(lambda: self.saveText(self.editor.toPlainText()))
        self.OKButton.clicked.connect(self.onOkClicked)

    def saveText(self, text):
        self.describe = text

    def onOkClicked(self):
        self.done(QDialog.Accepted)
