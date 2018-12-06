import sys

from core.MLTools import MainFrame
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainFrame()
    window.show()

    sys.exit(app.exec_())