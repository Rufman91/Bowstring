# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 20:49:34 2021

@author: ASUS
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np


class Label(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Label, self).__init__(parent)
        self.image = QtGui.QPixmap("TestImage.tif")
        self.drawing = True
        self.lastPoint = QtCore.QPoint()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(QtCore.QPoint(), self.image)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = True
            self.lastPoint = event.pos()
            self.Path = list(np.array((self.lastPoint.x(), self.lastPoint.y() )))

    def mouseMoveEvent(self, event):
        if event.buttons() and QtCore.Qt.LeftButton and self.drawing:
            painter = QtGui.QPainter(self.image)
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.SolidLine))
            painter.drawLine(self.lastPoint, event.pos())
            self.lastPoint = event.pos()
            #print(np.array((self.lastPoint.x(), self.lastPoint.y() )))
            self.Path.append(np.array((self.lastPoint.x(), self.lastPoint.y() )))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button == QtCore.Qt.LeftButton:
            self.drawing = False
            print(self.Path)

    def sizeHint(self):
        return self.image.size()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow,self).__init__(parent)

        self.label = Label()
        self.textedit = QtWidgets.QTextEdit()

        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)
        lay = QtWidgets.QHBoxLayout(widget)
        lay.addWidget(self.label, alignment=QtCore.Qt.AlignCenter)
        lay.addWidget(self.textedit)



import sys

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec_()