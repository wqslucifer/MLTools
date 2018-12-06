from PyQt5.QtWidgets import *

from core.project import ml_project
import GENERAL

GENERAL.init()


class modelManagerDialog(QDialog):
    def __init__(self, MLProject: ml_project, parent=None):
        super(modelManagerDialog, self).__init__(parent=parent)
