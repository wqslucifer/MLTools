import os
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QListWidget, QToolBox, \
    QTabWidget, QTextEdit, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QSpinBox, \
    QDoubleSpinBox, QFrame, QSizePolicy, QHeaderView, QTableView, QApplication, QScrollArea, QScrollBar, QSplitter, \
    QSplitterHandle, QComboBox, QGroupBox, QFormLayout, QCheckBox, QMenu, QAction, QWidgetAction, QStackedWidget, \
    QHeaderView, QRadioButton, QButtonGroup,QMessageBox
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, QSettings, QTimer, QUrl, QDir, \
    QAbstractTableModel, QEvent, QObject, QModelIndex, QVariant, QThread, QObject, QMimeData
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath, QStandardItemModel, QTextCursor, \
    QCursor, QDrag, QStandardItem
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from customWidget import CollapsibleTabWidget, ImageViewer, DragTableView, customProcessModel
from customLayout import FlowLayout

from SwitchButton import switchButton
import pandas as pd
import numpy as np
import subprocess
import logging
import threading
import gc
import time
import datetime
from multiprocessing import Queue

from model import xgbModel

import seaborn as sns
from process import processQueue


