# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 17:38:41 2021

@author: Manuel Rufin, Project COSIMA
@institution: Institute of Lightweight Design and Structural Biomechanics, TU Wien, Austria
"""

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import sys

class MainWindow(QMainWindow):
    
    def __init__(self,*args,**kwargs):
        super(MainWindow,self).__init__(*args,**kwargs)
        
        self.setWindowTitle('Bowstring')
        
        # setting  the geometry of window 
        self.setGeometry(0, 0, 400, 300) 
        
        toolbar = QToolBar('My main toolbar')
        toolbar.setIconSize(QSize(16,16))
        self.addToolBar(toolbar)
        
        button_action = QAction(QIcon('icons/bug--plus.png'),"Your button", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(self.onMyToolBarButtonClick)
        button_action.setCheckable(True)
        toolbar.addAction(button_action)
        
        toolbar.addSeparator()

        button_action2 = QAction(QIcon("icons/bug.png"), "Your button2", self)
        button_action2.setStatusTip("This is your button2")
        button_action2.triggered.connect(self.onMyToolBarButtonClick)
        button_action2.setCheckable(True)
        toolbar.addAction(button_action2)

        toolbar.addWidget(QLabel("Hello"))
        toolbar.addWidget(QCheckBox())
        
        self.setStatusBar(QStatusBar(self))
        
        # Now we start adding widgets!
        
        self.widget = QLabel()
        self.widget.setPixmap(QPixmap('TestImage.tif'))
        self.widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.widget.mousePressEvent = self.getPos
        
        self.setCentralWidget(self.widget)

    def getPos(self , event):
        x = event.pos().x()
        y = event.pos().y() 
        print('%i %i' % (x,y))
        
        
    def show_state(self,s):
        print(s == Qt.Checked)
        print(s)
        
    def onMyToolBarButtonClick(self,s):
        print('click',s)

class Color(QWidget):

    def __init__(self, color, *args, **kwargs):
        super(Color, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec_()