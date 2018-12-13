from PyQt5.QtWidgets import QLabel, QGridLayout, QDialog, QHBoxLayout, QTextEdit, QVBoxLayout, QPushButton, QLineEdit, \
    QApplication, QGroupBox, QRadioButton, QButtonGroup, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import logging

from core.process import processQueue

logfileformat = '[%(levelname)s] (%(threadName)-10s) %(message)s'
logging.basicConfig(level=logging.DEBUG, format=logfileformat)


def log(message):
    logging.debug(message)


def process_thread_pipe(process):
    while process.poll() is None:  # while process is still alive
        log(str(process.stderr.readline()))


class fillNADialog(QDialog):
    def __init__(self, PQ: processQueue, columns=None, parent=None):
        super(fillNADialog, self).__init__(parent=parent)
        # local data
        self.processQ = PQ
        self.value = None
        self.applyAllFeatures = True
        self.applyFeatures = None
        self.applyAllRows = True
        self.applyRows = None
        self.param = dict()
        self.method = None
        self.columns = columns
        # widgets
        self.mainLayout = QVBoxLayout(self)
        self.downLayout = QHBoxLayout(self)
        self.leftLayout = QVBoxLayout(self)
        self.rightLayout = QVBoxLayout(self)

        self.titleLabel = QLabel('Fill NA', self)
        # features
        self.featureGroup = QGroupBox('Features', self)
        self.featureButtonGroup = QButtonGroup(self)
        self.checkAllFeatures = QRadioButton(self)
        self.checkNumericFeatures = QRadioButton(self)
        self.checkCategoricalFeatures = QRadioButton(self)
        self.checkCustomFeatures = QRadioButton(self)
        self.featureMethod = None
        self.featureList = QTextEdit(self)
        # rows
        self.rowGroup = QGroupBox('Rows', self)
        self.rowButtonGroup = QButtonGroup(self)
        self.checkAllRows = QRadioButton(self)
        self.checkCustomRows = QRadioButton(self)
        self.rowList = QTextEdit(self)
        # filling method
        # FILL_VALUE, IGNORE, DELETE,FILL_MEAN, FILL_CLASS_MEAN, FILL_MEDIAN, FILL_BAYESIAN
        self.methodGroup = QGroupBox('Filling Method', self)
        self.fillValueEditor = QLineEdit(self)
        self.methodButtonGroup = QButtonGroup(self)
        self.method_FILL_VALUE = QRadioButton(self)
        self.method_FILL_MEAN = QRadioButton(self)
        self.method_FILL_CLASS_MEAN = QRadioButton(self)
        self.method_FILL_MEDIAN = QRadioButton(self)
        self.method_FILL_BAYESIAN = QRadioButton(self)
        self.method_IGNORE = QRadioButton(self)
        self.method_DELETE = QRadioButton(self)
        # confirm
        self.addToQueueButton = QPushButton('Add To Queue', self)
        self.initUI()

    def initUI(self):
        self.setFixedSize(800, 600)

        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.mainLayout.addLayout(self.downLayout, 10)
        self.downLayout.addLayout(self.leftLayout, 1)
        self.downLayout.addLayout(self.rightLayout, 3)
        # titleLabel
        self.titleLabel.setFont(QFont('Arial', 15, QFont.Times))
        self.titleLabel.setStyleSheet('QLabel {background-color : #A9A9A9; color: #FFFFFF}')
        self.titleLabel.setFixedHeight(40)
        self.titleLabel.setContentsMargins(30, 0, 0, 0)

        # feature
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.checkAllFeatures)
        vbox.addWidget(self.checkNumericFeatures)
        vbox.addWidget(self.checkCategoricalFeatures)
        vbox.addWidget(self.checkCustomFeatures)
        vbox.addWidget(self.featureList)
        self.featureList.setEnabled(False)
        self.featureGroup.setLayout(vbox)
        self.featureButtonGroup.addButton(self.checkAllFeatures)
        self.featureButtonGroup.addButton(self.checkNumericFeatures)
        self.featureButtonGroup.addButton(self.checkCategoricalFeatures)
        self.featureButtonGroup.addButton(self.checkCustomFeatures)
        # checkAllFeatures
        self.checkAllFeatures.setText('Fill All Features')
        self.checkAllFeatures.setFixedHeight(20)
        self.checkAllFeatures.setFont(QFont('Arial', 10, QFont.Times))
        self.checkAllFeatures.toggled.connect(self.setFeatures)
        self.checkAllFeatures.setChecked(True)
        # checkNumericFeatures
        self.checkNumericFeatures.setText('Fill All Numeric Features')
        self.checkNumericFeatures.setFixedHeight(20)
        self.checkNumericFeatures.toggled.connect(self.setFeatures)
        self.checkNumericFeatures.setFont(QFont('Arial', 10, QFont.Times))
        # checkCategoricalFeatures
        self.checkCategoricalFeatures.setText('Fill All Categorical Features')
        self.checkCategoricalFeatures.setFixedHeight(20)
        self.checkCategoricalFeatures.toggled.connect(self.setFeatures)
        self.checkCategoricalFeatures.setFont(QFont('Arial', 10, QFont.Times))
        # checkCustomFeatures
        self.checkCustomFeatures.setText('Fill Custom Features')
        self.checkCustomFeatures.setFixedHeight(20)
        self.checkCustomFeatures.setFont(QFont('Arial', 10, QFont.Times))
        self.checkCustomFeatures.toggled.connect(self.featureList.setEnabled)
        # row
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.checkAllRows)
        vbox.addWidget(self.checkCustomRows)
        vbox.addWidget(self.rowList)
        self.rowList.setEnabled(False)
        self.rowGroup.setLayout(vbox)
        self.rowButtonGroup.addButton(self.checkAllRows)
        self.rowButtonGroup.addButton(self.checkCustomRows)
        self.checkAllRows.setChecked(True)
        for checkRow_ in [self.checkAllRows, self.checkCustomRows]:
            checkRow_.setFixedHeight(20)
            checkRow_.setFont(QFont('Arial', 10, QFont.Times))
        # checkAllRows
        self.checkAllRows.setText('Fill All Rows')
        self.checkAllRows.toggled.connect(self.setApplyAllRows)
        # checkCustomRows
        self.checkCustomRows.setText('Fill custom Rows')
        self.checkCustomRows.toggled.connect(self.rowList.setEnabled)
        # row list
        self.leftLayout.addWidget(self.featureGroup, alignment=Qt.AlignTop)
        self.leftLayout.addWidget(self.rowGroup, alignment=Qt.AlignTop)
        self.leftLayout.addStretch(1)
        # method
        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout(self)
        hbox.addWidget(self.method_FILL_VALUE)
        hbox.addWidget(self.fillValueEditor)
        self.fillValueEditor.setEnabled(False)
        vbox.addLayout(hbox)
        vbox.addWidget(self.method_FILL_MEAN)
        vbox.addWidget(self.method_FILL_CLASS_MEAN)
        vbox.addWidget(self.method_FILL_MEDIAN)
        vbox.addWidget(self.method_FILL_BAYESIAN)
        vbox.addWidget(self.method_IGNORE)
        vbox.addWidget(self.method_DELETE)
        self.methodGroup.setLayout(vbox)
        self.methodButtonGroup.addButton(self.method_FILL_VALUE)
        self.methodButtonGroup.addButton(self.method_FILL_MEAN)
        self.methodButtonGroup.addButton(self.method_FILL_CLASS_MEAN)
        self.methodButtonGroup.addButton(self.method_FILL_MEDIAN)
        self.methodButtonGroup.addButton(self.method_FILL_BAYESIAN)
        self.methodButtonGroup.addButton(self.method_IGNORE)
        self.methodButtonGroup.addButton(self.method_DELETE)
        # method_FILL_VALUE
        for method_ in [self.method_FILL_VALUE, self.method_FILL_MEAN, self.method_FILL_CLASS_MEAN,
                        self.method_FILL_MEDIAN, self.method_FILL_BAYESIAN, self.method_IGNORE, self.method_DELETE]:
            method_.setFixedHeight(20)
            method_.setFont(QFont('Arial', 10, QFont.Times))
        # method_FILL_VALUE
        self.method_FILL_VALUE.setText('Fill NA with value')
        self.method_FILL_VALUE.toggled.connect(self.fillValueEditor.setEnabled)
        self.method_FILL_VALUE.toggled.connect(lambda: self.setMethod('FILL_VALUE'))
        # method_FILL_MEAN
        self.method_FILL_MEAN.setText('Fill NA with mean')
        self.method_FILL_MEAN.toggled.connect(lambda: self.setMethod('FILL_MEAN'))
        # method_FILL_CLASS_MEAN
        self.method_FILL_CLASS_MEAN.setText('Fill NA with mean of same class')
        self.method_FILL_CLASS_MEAN.toggled.connect(lambda: self.setMethod('FILL_CLASS_MEAN'))
        # method_FILL_MEDIAN
        self.method_FILL_MEDIAN.setText('Fill NA with median')
        self.method_FILL_MEDIAN.toggled.connect(lambda: self.setMethod('FILL_MEDIAN'))
        # method_FILL_BAYESIAN
        self.method_FILL_BAYESIAN.setText('Fill NA with Bayesian method')
        self.method_FILL_BAYESIAN.toggled.connect(lambda: self.setMethod('FILL_BAYESIAN'))
        # method_IGNORE
        self.method_IGNORE.setText('Ignore NA rows')
        self.method_IGNORE.toggled.connect(lambda: self.setMethod('IGNORE'))
        # method_DELETE
        self.method_DELETE.setText('Delete NA rows(Apply to whole dataframe)')
        self.method_DELETE.toggled.connect(lambda: self.setMethod('DELETE'))

        # add to queue button
        self.addToQueueButton.setFixedSize(100, 35)
        self.addToQueueButton.clicked.connect(self.addToQueue)
        buttonLayout = QHBoxLayout(self)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.addToQueueButton)
        # right layout
        self.rightLayout.addWidget(self.methodGroup)
        self.rightLayout.addStretch(1)
        self.rightLayout.addLayout(buttonLayout)

        # init columns
        if self.columns:
            self.checkCustomFeatures.setChecked(True)
            for i in self.columns:
                self.featureList.append(self.processQ.features[i])

    def addToQueue(self):
        self.prepareData()
        if self.method:
            if self.method == 'FILL_VALUE':
                if self.value is None:
                    QMessageBox.warning(self, 'warning', 'Please set a filling value', QMessageBox.Ok)
                    return
            self.accept()
        else:
            QMessageBox.warning(self, 'warning', 'Please select a filling method', QMessageBox.Ok)

    def setApplyAllRows(self, value):
        self.applyAllRows = value

    def setFeatures(self):
        self.featureList.clear()
        if self.checkAllFeatures.isChecked():
            self.applyAllFeatures = True
            self.featureMethod = 'ALL Features'
            for f in self.processQ.features:
                self.featureList.append(f)
        else:
            self.applyAllFeatures = False
        if self.checkNumericFeatures.isChecked():
            self.featureMethod = 'Numeric Features'
            for f in self.processQ.numericFeatures:
                self.featureList.append(f)
        if self.checkCategoricalFeatures.isChecked():
            self.featureMethod = 'Categorical Features'
            for f in self.processQ.categoricalFeatures:
                self.featureList.append(f)

    def setMethod(self, value):
        self.method = value

    def prepareData(self):
        if self.checkAllFeatures.isChecked():
            self.applyFeatures = self.processQ.features
        elif self.checkNumericFeatures.isChecked():
            self.applyFeatures = self.processQ.numericFeatures
        elif self.checkCategoricalFeatures.isChecked():
            self.applyFeatures = self.processQ.categoricalFeatures
        else:
            s = self.featureList.toPlainText()
            if ',' in s:
                self.applyFeatures = [i.strip('\'') for i in s.split(',')]
            elif '\n' in s:
                self.applyFeatures = [i.strip('\'') for i in s.split('\n')]
            else:
                self.applyFeatures = [s]

        if not self.checkAllRows:
            s = self.rowList.toPlainText()
            self.applyRows = [int(i) for i in s.split(',')]
        else:
            self.applyRows = self.processQ.trainSet.index.tolist()

        if self.method_FILL_VALUE.isChecked():
            tmp = self.fillValueEditor.text()
            try:
                self.value = float(tmp)
            except ValueError:
                self.value = tmp

        self.param['applyFeatures'] = self.applyFeatures
        self.param['applyRows'] = self.applyRows
        self.param['method'] = self.method
        self.param['value'] = self.value

    def addProcess(self):
        describe = {
            'FILL_VALUE': 'Fill ' + self.featureMethod + ' NA with value (' + str(self.value) + ')',
            'FILL_MEAN': 'Fill ' + self.featureMethod + ' NA with mean of column',
            'FILL_CLASS_MEAN': 'Fill ' + self.featureMethod + ' NA with mean of column while belong to same class',
            'FILL_MEDIAN': 'Fill ' + self.featureMethod + ' NA with median of column',
            'FILL_BAYESIAN': 'Fill ' + self.featureMethod + ' NA with Bayesian method',
            'IGNORE': 'Ignore ' + self.featureMethod + ' NA, Do Nothing',
            'DELETE': 'Delete ' + self.featureMethod + ' rows with NA'
        }
        # index = self.processQ.addProcess(self.processQ.fillNA, param=self.param)
        # self.processQ.addDescribe(index, 'fillNA', describe[self.method])
        return self.processQ.fillNA, self.param, 'fillNA', describe[self.method]


class logTransformDialog(QDialog):
    def __init__(self, PQ: processQueue, columns=None, parent=None):
        super(logTransformDialog, self).__init__(parent=parent)
        # local data
        self.processQ = PQ
        self.applyAllFeatures = True
        self.applyFeatures = None
        self.applyAllRows = True
        self.applyRows = None
        self.param = dict()
        self.method = None
        self.columns = columns
        # widgets
        self.mainLayout = QVBoxLayout(self)
        self.downLayout = QHBoxLayout(self)
        self.leftLayout = QVBoxLayout(self)
        self.rightLayout = QVBoxLayout(self)

        self.titleLabel = QLabel('Transformation', self)
        # features
        self.featureGroup = QGroupBox('Features', self)
        self.featureButtonGroup = QButtonGroup(self)
        self.checkNumericFeatures = QRadioButton(self)
        self.checkCustomFeatures = QRadioButton(self)
        self.featureList = QTextEdit(self)
        # rows
        self.rowGroup = QGroupBox('Rows', self)
        self.rowButtonGroup = QButtonGroup(self)
        self.checkAllRows = QRadioButton(self)
        self.checkCustomRows = QRadioButton(self)
        self.rowList = QTextEdit(self)
        # filling method
        # FILL_VALUE, IGNORE, DELETE,FILL_MEAN, FILL_CLASS_MEAN, FILL_MEDIAN, FILL_BAYESIAN
        self.methodGroup = QGroupBox('Transform Function', self)
        self.methodButtonGroup = QButtonGroup(self)
        self.method_RECIPROCAL = QRadioButton(self)
        self.method_LOG_10 = QRadioButton(self)
        self.method_LOG_E = QRadioButton(self)
        self.method_LOG_2 = QRadioButton(self)
        self.method_SQUARE_ROOT = QRadioButton(self)
        self.method_CUBE_ROOT = QRadioButton(self)
        # confirm
        self.addToQueueButton = QPushButton('Add To Queue', self)
        self.initUI()

    def initUI(self):
        self.setFixedSize(800, 600)

        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.mainLayout.addLayout(self.downLayout, 10)
        self.downLayout.addLayout(self.leftLayout, 1)
        self.downLayout.addLayout(self.rightLayout, 3)
        # titleLabel
        self.titleLabel.setFont(QFont('Arial', 15, QFont.Times))
        self.titleLabel.setStyleSheet('QLabel {background-color : #A9A9A9; color: #FFFFFF}')
        self.titleLabel.setFixedHeight(40)
        self.titleLabel.setContentsMargins(30, 0, 0, 0)

        # feature
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.checkNumericFeatures)
        vbox.addWidget(self.checkCustomFeatures)
        vbox.addWidget(self.featureList)
        self.featureList.setEnabled(False)
        self.featureGroup.setLayout(vbox)
        self.featureButtonGroup.addButton(self.checkNumericFeatures)
        self.featureButtonGroup.addButton(self.checkCustomFeatures)
        # checkNumericFeatures
        self.checkNumericFeatures.setText('Transform All Numeric Features')
        self.checkNumericFeatures.setFixedHeight(20)
        self.checkNumericFeatures.setFont(QFont('Arial', 10, QFont.Times))
        self.checkNumericFeatures.setChecked(True)
        # checkCustomFeatures
        self.checkCustomFeatures.setText('Fill Custom Features')
        self.checkCustomFeatures.setFixedHeight(20)
        self.checkCustomFeatures.setFont(QFont('Arial', 10, QFont.Times))
        self.checkCustomFeatures.toggled.connect(self.featureList.setEnabled)
        # row
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.checkAllRows)
        vbox.addWidget(self.checkCustomRows)
        vbox.addWidget(self.rowList)
        self.rowList.setEnabled(False)
        self.rowGroup.setLayout(vbox)
        self.rowButtonGroup.addButton(self.checkAllRows)
        self.rowButtonGroup.addButton(self.checkCustomRows)
        self.checkAllRows.setChecked(True)
        for checkRow_ in [self.checkAllRows, self.checkCustomRows]:
            checkRow_.setFixedHeight(20)
            checkRow_.setFont(QFont('Arial', 10, QFont.Times))
        # checkAllRows
        self.checkAllRows.setText('Fill All Rows')
        self.checkAllRows.toggled.connect(self.setApplyAllRows)
        # checkCustomRows
        self.checkCustomRows.setText('Fill custom Rows')
        self.checkCustomRows.toggled.connect(self.rowList.setEnabled)
        # row list
        self.leftLayout.addWidget(self.featureGroup, alignment=Qt.AlignTop)
        self.leftLayout.addWidget(self.rowGroup, alignment=Qt.AlignTop)
        self.leftLayout.addStretch(1)
        # method
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.method_RECIPROCAL)
        vbox.addWidget(self.method_LOG_10)
        vbox.addWidget(self.method_LOG_E)
        vbox.addWidget(self.method_LOG_2)
        vbox.addWidget(self.method_SQUARE_ROOT)
        vbox.addWidget(self.method_CUBE_ROOT)
        self.methodGroup.setLayout(vbox)
        self.methodButtonGroup.addButton(self.method_RECIPROCAL)
        self.methodButtonGroup.addButton(self.method_LOG_10)
        self.methodButtonGroup.addButton(self.method_LOG_E)
        self.methodButtonGroup.addButton(self.method_LOG_2)
        self.methodButtonGroup.addButton(self.method_SQUARE_ROOT)
        self.methodButtonGroup.addButton(self.method_CUBE_ROOT)

        # method_FILL_VALUE
        for method_ in [self.method_RECIPROCAL, self.method_LOG_10, self.method_LOG_E,
                        self.method_LOG_2, self.method_SQUARE_ROOT, self.method_CUBE_ROOT]:
            method_.setFixedHeight(20)
            method_.setFont(QFont('Arial', 10, QFont.Times))
        # method_LOG_10
        self.method_RECIPROCAL.setText('T=1/x')
        self.method_RECIPROCAL.toggled.connect(lambda: self.setMethod('RECIPROCAL'))
        # method_RECIPROCAL
        self.method_LOG_10.setText('T=log10(x)')
        self.method_LOG_10.toggled.connect(lambda: self.setMethod('LOG_10'))
        # method_RECIPROCAL
        self.method_LOG_2.setText('T=log2(x)')
        self.method_LOG_2.toggled.connect(lambda: self.setMethod('LOG_2'))
        # method_RECIPROCAL
        self.method_LOG_E.setText('T=ln(x)')
        self.method_LOG_E.toggled.connect(lambda: self.setMethod('LOG_E'))
        # method_RECIPROCAL
        self.method_SQUARE_ROOT.setText('T=x**1/2')
        self.method_SQUARE_ROOT.toggled.connect(lambda: self.setMethod('SQUARE_ROOT'))
        # method_RECIPROCAL
        self.method_CUBE_ROOT.setText('T=x**1/3')
        self.method_CUBE_ROOT.toggled.connect(lambda: self.setMethod('CUBE_ROOT'))

        # add to queue button
        self.addToQueueButton.setFixedSize(100, 35)
        self.addToQueueButton.clicked.connect(self.addToQueue)
        buttonLayout = QHBoxLayout(self)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.addToQueueButton)
        # right layout
        self.rightLayout.addWidget(self.methodGroup)
        self.rightLayout.addStretch(1)
        self.rightLayout.addLayout(buttonLayout)

        # init columns
        if self.columns:
            self.checkCustomFeatures.setChecked(True)
            for i in self.columns:
                self.featureList.append(self.processQ.features[i])

    def addToQueue(self):
        if self.method:
            self.prepareData()
            self.accept()
        else:
            QMessageBox.warning(self, 'warning', 'Please select a filling method', QMessageBox.Ok)

    def setApplyAllRows(self, value):
        self.applyAllRows = value

    def setFeatures(self):
        self.featureList.clear()
        if self.checkAllFeatures.isChecked():
            self.applyAllFeatures = True
            self.featureMethod = 'ALL Features'
            for f in self.processQ.features:
                self.featureList.append(f)
        else:
            self.applyAllFeatures = False
        if self.checkNumericFeatures.isChecked():
            self.featureMethod = 'Numeric Features'
            for f in self.processQ.numericFeatures:
                self.featureList.append(f)
        if self.checkCategoricalFeatures.isChecked():
            self.featureMethod = 'Categorical Features'
            for f in self.processQ.categoricalFeatures:
                self.featureList.append(f)

    def setMethod(self, value):
        self.method = value

    def prepareData(self):
        if self.checkNumericFeatures.isChecked():
            self.applyFeatures = self.processQ.numericFeatures
        else:
            s = self.featureList.toPlainText()
            if ',' in s:
                self.applyFeatures = [i.strip('\'') for i in s.split(',')]
            elif '\n' in s:
                self.applyFeatures = [i.strip('\'') for i in s.split('\n')]
            else:
                self.applyFeatures = [s]

        if not self.checkAllRows:
            s = self.rowList.toPlainText()
            self.applyRows = [int(i) for i in s.split(',')]
        else:
            self.applyRows = self.processQ.trainSet.index.tolist()

        self.param['applyFeatures'] = self.applyFeatures
        self.param['applyRows'] = self.applyRows
        self.param['method'] = self.method

    def addProcess(self):
        describe = {
            'RECIPROCAL': 'Transform column using Reciprocal t=1/x',
            'LOG_10': 'Transform column using LOG_10 t=log10(x)',
            'LOG_2': 'Transform column using LOG_2 t=log2(x)',
            'LOG_E': 'Transform column using LOG_E t=ln(x)',
            'SQUARE_ROOT': 'Transform column using SQUARE_ROOT t=x**1/2',
            'CUBE_ROOT': 'Transform column using CUBE_ROOT t=x**1/3',
        }
        transformName = {
            'RECIPROCAL': 'Transform: t=1/x',
            'LOG_10': 'Transform: t=log10(x)',
            'LOG_2': 'Transform: t=log2(x)',
            'LOG_E': 'Transform: t=ln(x)',
            'SQUARE_ROOT': 'Transform: t=x**1/2',
            'CUBE_ROOT': 'Transform: t=x**1/3',
        }
        # index = self.processQ.addProcess(self.processQ.fillNA, param=self.param)
        # self.processQ.addDescribe(index, 'fillNA', describe[self.method])
        return self.processQ.fillNA, self.param, transformName[self.method], describe[self.method]


class encodeDialog(QDialog):
    def __init__(self, PQ: processQueue, columns=None, parent=None):
        super(encodeDialog, self).__init__(parent=parent)
        # local data
        self.processQ = PQ
        self.value = None
        self.applyAllFeatures = True
        self.applyFeatures = None
        self.applyAllRows = True
        self.applyRows = None
        self.param = dict()
        self.method = None
        self.columns = columns
        # widgets
        self.mainLayout = QVBoxLayout(self)
        self.downLayout = QHBoxLayout(self)
        self.leftLayout = QVBoxLayout(self)
        self.rightLayout = QVBoxLayout(self)

        self.titleLabel = QLabel('Encode Categorical Feature', self)
        # features
        self.featureGroup = QGroupBox('Features', self)
        self.featureButtonGroup = QButtonGroup(self)
        self.checkAllCategoricalFeatures = QRadioButton(self)
        self.checkCustomFeatures = QRadioButton(self)
        self.featureMethod = None
        self.featureList = QTextEdit(self)
        # rows
        self.rowGroup = QGroupBox('Rows', self)
        self.rowButtonGroup = QButtonGroup(self)
        self.checkAllRows = QRadioButton(self)
        self.checkCustomRows = QRadioButton(self)
        self.rowList = QTextEdit(self)
        # Encode method
        self.methodGroup = QGroupBox('Encode Method', self)
        self.methodButtonGroup = QButtonGroup(self)
        self.method_ENCODE = QRadioButton(self)
        self.method_ONEHOTCODE = QRadioButton(self)
        # confirm
        self.addToQueueButton = QPushButton('Add To Queue', self)
        self.initUI()

    def initUI(self):
        self.setFixedSize(800, 600)

        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.mainLayout.addLayout(self.downLayout, 10)
        self.downLayout.addLayout(self.leftLayout, 1)
        self.downLayout.addLayout(self.rightLayout, 3)
        # titleLabel
        self.titleLabel.setFont(QFont('Arial', 15, QFont.Times))
        self.titleLabel.setStyleSheet('QLabel {background-color : #A9A9A9; color: #FFFFFF}')
        self.titleLabel.setFixedHeight(40)
        self.titleLabel.setContentsMargins(30, 0, 0, 0)
        # feature
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.checkAllCategoricalFeatures)
        vbox.addWidget(self.checkCustomFeatures)
        vbox.addWidget(self.featureList)
        self.featureList.setEnabled(False)
        self.featureGroup.setLayout(vbox)
        self.featureButtonGroup.addButton(self.checkAllCategoricalFeatures)
        self.featureButtonGroup.addButton(self.checkCustomFeatures)
        # checkCategoricalFeatures
        self.checkAllCategoricalFeatures.setText('Fill All Categorical Features')
        self.checkAllCategoricalFeatures.setFixedHeight(20)
        self.checkAllCategoricalFeatures.toggled.connect(self.setFeatures)
        self.checkAllCategoricalFeatures.setFont(QFont('Arial', 10, QFont.Times))
        self.checkAllCategoricalFeatures.setChecked(True)
        # checkCustomFeatures
        self.checkCustomFeatures.setText('Fill Custom Features')
        self.checkCustomFeatures.setFixedHeight(20)
        self.checkCustomFeatures.setFont(QFont('Arial', 10, QFont.Times))
        self.checkCustomFeatures.toggled.connect(self.featureList.setEnabled)
        # row
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.checkAllRows)
        vbox.addWidget(self.checkCustomRows)
        vbox.addWidget(self.rowList)
        self.rowList.setEnabled(False)
        self.rowGroup.setLayout(vbox)
        self.rowButtonGroup.addButton(self.checkAllRows)
        self.rowButtonGroup.addButton(self.checkCustomRows)
        self.checkAllRows.setChecked(True)
        for checkRow_ in [self.checkAllRows, self.checkCustomRows]:
            checkRow_.setFixedHeight(20)
            checkRow_.setFont(QFont('Arial', 10, QFont.Times))
        # checkAllRows
        self.checkAllRows.setText('Fill All Rows')
        self.checkAllRows.toggled.connect(self.setApplyAllRows)
        # checkCustomRows
        self.checkCustomRows.setText('Fill custom Rows')
        self.checkCustomRows.toggled.connect(self.rowList.setEnabled)
        # row list
        self.leftLayout.addWidget(self.featureGroup, alignment=Qt.AlignTop)
        self.leftLayout.addWidget(self.rowGroup, alignment=Qt.AlignTop)
        self.leftLayout.addStretch(1)
        # method
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.method_ENCODE)
        vbox.addWidget(self.method_ONEHOTCODE)
        self.methodGroup.setLayout(vbox)
        self.methodButtonGroup.addButton(self.method_ENCODE)
        self.methodButtonGroup.addButton(self.method_ONEHOTCODE)

        for method_ in [self.method_ENCODE, self.method_ONEHOTCODE]:
            method_.setFixedHeight(20)
            method_.setFont(QFont('Arial', 10, QFont.Times))
        # method_ENCODE
        self.method_ENCODE.setText('Encode Category')
        self.method_ENCODE.toggled.connect(lambda: self.setMethod('ENCODE'))
        # method_ONEHOTCODE
        self.method_ONEHOTCODE.setText('Encode Category using One-Hot-Code')
        self.method_ONEHOTCODE.toggled.connect(lambda: self.setMethod('ONEHOTCODE'))

        # add to queue button
        self.addToQueueButton.setFixedSize(100, 35)
        self.addToQueueButton.clicked.connect(self.addToQueue)
        buttonLayout = QHBoxLayout(self)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.addToQueueButton)
        # right layout
        self.rightLayout.addWidget(self.methodGroup)
        self.rightLayout.addStretch(1)
        self.rightLayout.addLayout(buttonLayout)

        # init columns
        if self.columns:
            self.checkCustomFeatures.setChecked(True)
            for i in self.columns:
                self.featureList.append(self.processQ.features[i])

    def addToQueue(self):
        self.prepareData()
        if self.method:
            if self.method == 'FILL_VALUE':
                if self.value is None:
                    QMessageBox.warning(self, 'warning', 'Please set a filling value', QMessageBox.Ok)
                    return
            self.accept()
        else:
            QMessageBox.warning(self, 'warning', 'Please select a filling method', QMessageBox.Ok)

    def setApplyAllRows(self, value):
        self.applyAllRows = value

    def setFeatures(self):
        self.featureList.clear()
        if self.checkAllCategoricalFeatures.isChecked():
            self.featureMethod = 'Categorical Features'
            for f in self.processQ.categoricalFeatures:
                self.featureList.append(f)

    def setMethod(self, value):
        self.method = value

    def prepareData(self):
        if self.checkAllCategoricalFeatures.isChecked():
            self.applyFeatures = self.processQ.categoricalFeatures
        else:
            s = self.featureList.toPlainText()
            if ',' in s:
                self.applyFeatures = [i.strip('\'') for i in s.split(',')]
            elif '\n' in s:
                self.applyFeatures = [i.strip('\'') for i in s.split('\n')]
            else:
                self.applyFeatures = [s]

        if not self.checkAllRows:
            s = self.rowList.toPlainText()
            self.applyRows = [int(i) for i in s.split(',')]
        else:
            self.applyRows = self.processQ.trainSet.index.tolist()

        self.param['applyFeatures'] = self.applyFeatures
        self.param['applyRows'] = self.applyRows
        self.param['method'] = self.method

    def addProcess(self):
        describe = {
            'ENCODE': 'Encode and replace' + self.featureMethod + '',
            'ONEHOTCODE': 'Encode and replace' + self.featureMethod + ' using OntHotCode'
        }
        # index = self.processQ.addProcess(self.processQ.fillNA, param=self.param)
        # self.processQ.addDescribe(index, 'fillNA', describe[self.method])
        return self.processQ.encodeCategory, self.param, 'encode', describe[self.method]


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QGridLayout(self)
        self.setFixedSize(800, 500)
        self.setLayout(self.mainLayout)
        self.item = logTransformDialog(self)
        self.mainLayout.addWidget(self.item)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    # exceptionHandler.errorSignal.connect(something)
    sys.exit(app.exec_())
