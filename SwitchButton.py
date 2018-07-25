import os
from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget, QDialog, QFrame, QHBoxLayout, QListWidget, QToolBox, \
    QTabWidget, QTextEdit, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, pyqtSignal, QTimer
from PyQt5 import QtCore
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPalette, QPainterPath, QPaintEvent, QMouseEvent, \
    QResizeEvent
from PyQt5 import QtWidgets


class switchButton(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self):
        super(switchButton, self).__init__()
        # init local variable
        self.Checked = False
        self.bgColorOn = QColor('#78E54C')
        self.bgColorOff = QColor('#CACACA')
        self.sliderColorOn = QColor('#F1F1F1')  #('#6B81FE')
        self.sliderColorOff = QColor('#F1F1F1') #(100, 100, 100)
        self.textColorOn = QColor('#FDECFF')
        self.textColorOff = QColor(10, 10, 10)

        # self.checkedColor = QColor(0, 150, 136)
        # self.disabledColor = QColor(190, 190, 190)
        # self.thumbColor = Qt.white
        self.textOn = 'On'
        self.textOff = 'Off'
        self.step = self.width() / 50
        # self.radius = 4.0
        self.space = 2
        self.startX = 0
        self.endX = 0
        self.timer = QTimer(self)
        self.timer.setInterval(5)
        self.timer.timeout.connect(self.onTimeout)
        self.setMaximumSize(85, 25)
        self.setFont(QFont("Arial", 10, QFont.Bold))

    def isToggled(self):
        return self.Checked

    def setToggle(self, checked):
        self.Checked = checked
        self.timer.start()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.drawBg(painter)
        self.drawSlider(painter)
        self.drawText(painter)

    def drawBg(self, painter: QPainter):
        painter.save()
        painter.setPen(Qt.NoPen)
        if self.Checked:
            painter.setBrush(self.bgColorOn)
        else:
            painter.setBrush(self.bgColorOff)
        rect = QRect(0, 0, self.width(), self.height())
        radius = rect.height() / 2
        circleWidth = rect.height()

        path = QPainterPath()
        path.moveTo(radius, rect.left())
        path.arcTo(QRectF(rect.left(), rect.top(), circleWidth, circleWidth), 90, 180)
        path.lineTo(rect.width() - radius, rect.height())
        path.arcTo(QRectF(rect.width() - rect.height(), rect.top(), circleWidth, circleWidth), 270, 180)
        path.lineTo(radius, rect.top())
        painter.drawPath(path)
        painter.restore()

    def drawSlider(self, painter: QPainter):
        painter.save()
        painter.setPen(Qt.NoPen)
        if self.Checked:
            painter.setBrush(self.sliderColorOn)
        else:
            painter.setBrush(self.sliderColorOff)
        rect = QRect(0, 0, self.width(), self.height())
        sliderWidth = rect.height() - self.space * 2
        sliderRect = QRect(self.startX + self.space, self.space, sliderWidth, sliderWidth)
        painter.drawEllipse(sliderRect)
        painter.restore()

    def drawText(self, painter: QPainter):
        painter.save()
        if not self.Checked:
            painter.setPen(self.textColorOff)
            painter.drawText(self.width() / 2, 0, self.width() / 2 - self.space, self.height(),
                             Qt.AlignCenter, self.textOff)
        else:
            painter.setPen(self.textColorOn)
            painter.drawText(0, 0, self.width() / 2 + self.space * 2, self.height(), Qt.AlignCenter,
                             self.textOn)
        painter.restore()

    def mousePressEvent(self, event: QMouseEvent):
        if event.buttons() and Qt.LeftButton:
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if (event.type() == QMouseEvent.MouseButtonRelease) and (event.button() == Qt.LeftButton):
            event.accept()
            self.Checked = not self.Checked
            self.toggled.emit(self.Checked)
            self.step = self.width() / 50
            if self.Checked:
                self.endX = self.width() - self.height()
            else:
                self.endX = 0
            self.timer.start()
        else:
            event.ignore()

    def resizeEvent(self, event: QResizeEvent):
        self.step = self.width() / 50
        if self.Checked:
            self.startX = self.width() - self.height()
        else:
            self.startX = 0
        self.update()
        QWidget.resizeEvent(self, event)

    def onTimeout(self):
        if self.Checked:
            if self.startX < self.endX:
                self.startX += self.step
            else:
                self.startX = self.endX
                self.timer.stop()
        else:
            if self.startX > self.endX:
                self.startX = self.startX - self.step
            else:
                self.startX = self.endX
                self.timer.stop()
        self.update()


class testDialog(QDialog):
    def __init__(self):
        super(testDialog, self).__init__()
        self.mainLayout = QGridLayout(self)
        self.setFixedSize(200, 50)
        self.setLayout(self.mainLayout)
        self.item = switchButton()
        self.mainLayout.addWidget(self.item, 0, 0)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = testDialog()
    window.show()
    sys.exit(app.exec_())
