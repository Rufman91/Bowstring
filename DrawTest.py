# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 20:49:34 2021

@author: ASUS
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import time


class DrawTool(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(DrawTool, self).__init__(parent)
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
        if event.buttons() == QtCore.Qt.LeftButton and self.drawing:
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
    
    def draw_line(self,Point1,Point2):
        painter = QtGui.QPainter(self.image)
        painter.setPen(QtGui.QPen(QtCore.Qt.red, 5, QtCore.Qt.SolidLine))
        painter.drawLine(QtCore.QPoint(Point1[0],Point1[1]),QtCore.QPoint(Point2[0],Point2[1]) )
        self.update()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow,self).__init__(parent)

        self.Draw = DrawTool()
        self.textedit = QtWidgets.QTextEdit()

        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)
        lay = QtWidgets.QHBoxLayout(widget)
        lay.addWidget(self.Draw, alignment=QtCore.Qt.AlignCenter)
        lay.addWidget(self.textedit)
        
        
        
        time.sleep(1)
        
        Point1 = np.array([0,0])
        Point2 = np.array([500,500])
        
        self.Draw.draw_line(Point1,Point2)
        
        time.sleep(1)
        
        Point1 = np.array([0,500])
        Point2 = np.array([500,0])
        
        self.Draw.draw_line(Point1,Point2)
        



import sys

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec_()