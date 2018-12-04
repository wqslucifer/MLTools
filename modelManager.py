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
from customWidget import ModelWidget, DataWidget, ProjectWidget, ScriptWidget, CollapsibleTabWidget, ResultWidget, \
    HistoryWidget, ImageDataWidget, QTreeWidgetItem
from customLayout import FlowLayout
from tabWidget import DataTabWidget, IpythonTabWidget, process_thread_pipe, IpythonWebView, log, ModelTabWidget, \
    ImageDataTabWidget, queueTabWidget, scriptTabWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtQuick import QQuickView
from PyQt5.QtCore import QUrl, QEvent

from SwitchButton import switchButton
from model import ml_model
from project import ml_project
from multiprocessing import Queue
from management import manageProcess
import GENERAL

GENERAL.init()

class modelManagerDialog(QDialog):
    def __init__(self, MLProject: ml_project, parent=None):
        super(modelManagerDialog, self).__init__(parent=parent)