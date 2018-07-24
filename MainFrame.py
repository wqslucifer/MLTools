# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainFrame.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1263, 711)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1263, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile_F = QtWidgets.QMenu(self.menubar)
        self.menuFile_F.setObjectName("menuFile_F")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionOpen_Project = QtWidgets.QAction(MainWindow)
        self.actionOpen_Project.setObjectName("actionOpen_Project")
        self.actionOpen_File = QtWidgets.QAction(MainWindow)
        self.actionOpen_File.setObjectName("actionOpen_File")
        self.actionCreate_Project = QtWidgets.QAction(MainWindow)
        self.actionCreate_Project.setObjectName("actionCreate_Project")
        self.menuFile_F.addAction(self.actionCreate_Project)
        self.menuFile_F.addAction(self.actionOpen_Project)
        self.menuFile_F.addAction(self.actionOpen_File)
        self.menubar.addAction(self.menuFile_F.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.menuFile_F.setTitle(_translate("MainWindow", "File(&F)"))
        self.actionOpen_Project.setText(_translate("MainWindow", "Open Project"))
        self.actionOpen_File.setText(_translate("MainWindow", "Add File"))
        self.actionCreate_Project.setText(_translate("MainWindow", "Create Project"))

