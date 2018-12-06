# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'CreateProject.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_createProjectDialog(object):
    def setupUi(self, createProjectDialog):
        createProjectDialog.setObjectName("createProjectDialog")
        createProjectDialog.resize(731, 467)
        self.buttonBox = QtWidgets.QDialogButtonBox(createProjectDialog)
        self.buttonBox.setGeometry(QtCore.QRect(370, 420, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.locationEdit = QtWidgets.QLineEdit(createProjectDialog)
        self.locationEdit.setGeometry(QtCore.QRect(140, 20, 541, 31))
        self.locationEdit.setObjectName("locationEdit")
        self.label = QtWidgets.QLabel(createProjectDialog)
        self.label.setGeometry(QtCore.QRect(50, 20, 81, 31))
        self.label.setObjectName("label")

        self.retranslateUi(createProjectDialog)
        self.buttonBox.accepted.connect(createProjectDialog.accept)
        self.buttonBox.rejected.connect(createProjectDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(createProjectDialog)

    def retranslateUi(self, createProjectDialog):
        _translate = QtCore.QCoreApplication.translate
        createProjectDialog.setWindowTitle(_translate("createProjectDialog", "Dialog"))
        self.label.setText(_translate("createProjectDialog", "Location:"))

