from PyQt5.QtCore import pyqtSlot, QSettings, QTimer, QUrl, QDir
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QApplication,QDialog,QGridLayout,QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

import sys
import subprocess
import signal
import logging
import threading

logfileformat = '[%(levelname)s] (%(threadName)-10s) %(message)s'
logging.basicConfig(level=logging.DEBUG, format=logfileformat)

def log(message):
    logging.debug(message)

class MainWindow(QWidget):
    def __init__(self, parent=None, homepage=None):
        super(MainWindow, self).__init__(parent)
        self.homepage = homepage
        self.windows = []
        self.layout = QGridLayout(self)
        self.basewebview = CustomWebView(self, main=True)
        self.layout.addWidget(self.basewebview,0,0)
        self.setLayout(self.layout)
        # self.setCentralWidget(self.basewebview)
        QTimer.singleShot(0, self.initialload)

    @pyqtSlot()
    def initialload(self):
        if self.homepage:
            self.basewebview.load(QUrl(self.homepage))
        self.show()

    def closeEvent(self, event):
        if self.windows:
            for i in reversed(range(len(self.windows))):
                w = self.windows.pop(i)
                w.close()
            event.accept()
        else:
            event.accept()

class CustomWebView(QWebEngineView):

    def __init__(self, mainwindow, main=False):
        super(CustomWebView, self).__init__(None)
        self.parent = mainwindow
        self.main = main
        self.loadedPage = None

    @pyqtSlot(bool)
    def onpagechange(self, ok):
        log("on page change: %s, %s" % (self.url(), ok))
        if self.loadedPage is not None:
            log("disconnecting on close signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)
        self.loadedPage = self.page()
        log("connecting on close signal")
        self.loadedPage.windowCloseRequested.connect(self.close)

    def createWindow(self, windowType):
        v = CustomWebView(self.parent)
        windows = self.parent.windows
        windows.append(v)
        v.show()
        return v

    def closeEvent(self, event):
        if self.loadedPage is not None:
            log("disconnecting on close signal")
            self.loadedPage.windowCloseRequested.disconnect(self.close)

        if not self.main:
            if self in self.parent.windows:
                self.parent.windows.remove(self)
            log("Window count: %s" % (len(self.parent.windows) + 1))
        event.accept()

def startnotebook(notebook_executable="jupyter-notebook", port=8888, directory='E:/project'):
    return subprocess.Popen([notebook_executable,
                             "--port=%s" % port, "--browser=n", "-y",
                             "--notebook-dir=%s" % directory], bufsize=1,
                            stderr=subprocess.PIPE)
def process_thread_pipe(process):
    while process.poll() is None:  # while process is still alive
        log(str(process.stderr.readline()))


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        log("Starting Jupyter notebook process")
        self.notebookp = startnotebook()
        log("Waiting for server to start...")
        webaddr = None
        while webaddr is None:
            line = str(self.notebookp.stderr.readline())
            log(line)
            if "http://" in line:
                start = line.find("http://")
                end = line.find("/", start + len("http://"))
                webaddr = line[start:end]
        log("Server found at %s, migrating monitoring to listener thread" % webaddr)
        # pass monitoring over to child thread
        notebookmonitor = threading.Thread(name="Notebook Monitor", target=process_thread_pipe,
                                           args=(self.notebookp,))
        notebookmonitor.start()

        self.mainLayout = QGridLayout(self)
        self.setFixedSize(800, 500)
        self.mainLayout.addWidget(MainWindow(None, homepage=webaddr))

    def closeEvent(self, QCloseEvent):
        self.notebookp.kill()

if __name__=='__main__':
    # start jupyter notebook and wait for line with the web address


    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    sys.exit(app.exec_())
