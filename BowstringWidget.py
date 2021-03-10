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
import numpy as np

class DrawWidget(QWidget):
    def __init__(self, parent=None):
        super(DrawWidget, self).__init__(parent)
        self.image = QPixmap("TestImage.tif")
        self.drawing = True
        self.lastPoint = QPoint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(QPoint(), self.image)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.lastPoint = event.pos()
            self.Path = list(np.array((self.lastPoint.x(), self.lastPoint.y() )))

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.drawing:
            painter = QPainter(self.image)
            painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))
            painter.drawLine(self.lastPoint, event.pos())
            self.lastPoint = event.pos()
            #print(np.array((self.lastPoint.x(), self.lastPoint.y() )))
            self.Path.append(np.array((self.lastPoint.x(), self.lastPoint.y() )))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            self.drawing = False
            print(self.Path)

class PointWidget(QWidget):
    def __init__(self, parent=None):
        super(DrawWidget, self).__init__(parent)
        self.image = QPixmap("TestImage.tif")
        self.lastPoint = QPoint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(QPoint(), self.image)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.lastPoint = event.pos()
            self.Path = list(np.array((self.lastPoint.x(), self.lastPoint.y() )))

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.drawing:
            painter = QPainter(self.image)
            painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))
            painter.drawLine(self.lastPoint, event.pos())
            self.lastPoint = event.pos()
            #print(np.array((self.lastPoint.x(), self.lastPoint.y() )))
            self.Path.append(np.array((self.lastPoint.x(), self.lastPoint.y() )))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            self.drawing = False
            print(self.Path)

class MainWindow(QMainWindow):
    
    def __init__(self,*args,**kwargs):
        super(MainWindow,self).__init__(*args,**kwargs)
        
        # Run the script like this: python BowstringWidget.py CurrentTipPositionX CurrentTipPositionY ImageFullfile
        #                     e.g.: python BowstringWidget.py 1.345e-6 1.0000e-6 path\to\eternity
        if len(sys.argv)<3:
            self.ImageFullfile = 'TestImage.tif'
            self.CurrentTipPosition = [1.5e-6, 1e-6]
        else:
            self.ImageFullfile = sys.argv[3]
            self.CurrentTipPosition = [float(sys.argv[1]) , float(sys.argv[2])]
        
        self.PointCounter = 0
        self.Points = list()
        self.StrainRate = []
        self.FinalStrain = []
        self.PixelSize = 0.5
        self.Magnification = 200
        
        toolbar = QToolBar('My main toolbar')
        toolbar.setIconSize(QSize(64,64))
        self.addToolBar(toolbar)
        
        self.BowModeButton = QAction(QIcon('icons/Bow.jpg'),"Your button", self)
        self.BowModeButton.setStatusTip("Design and run a Bowstring experiment")
        self.BowModeButton.triggered.connect(self.onBowModeButtonClick)
        self.BowModeButton.setCheckable(True)
        self.BowModeButton.toggle()
        toolbar.addAction(self.BowModeButton)
        
        toolbar.addSeparator()

        self.LithModeButton = QAction(QIcon("icons/Chisel.jpg"), "Your button2", self)
        self.LithModeButton.setStatusTip("This is just a placeholder for Nanolithography mode")
        self.LithModeButton.triggered.connect(self.onLithModeButtonClick)
        self.LithModeButton.setCheckable(True)
        toolbar.addAction(self.LithModeButton)
        
        toolbar.addSeparator()
        
        self.setStatusBar(QStatusBar(self))
        
        # Now we start adding widgets!
        
        self.ImageDescriptionPrompts = ['Set the first fibril anchorpoint','Set the second fibril anchorpoint','Set the exact position of the cantilever tip','Clicking again will reset all points']
        self.ImageDescription = QLabel(self.ImageDescriptionPrompts[self.PointCounter])
        self.ImageDescription.setFont(QFont('Arial',32))
        
        Image = QLabel()
        Image.setPixmap(QPixmap('TestImage.tif'))
        Image.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        Image.setAcceptDrops(True)
        Image.dropEvent = self.drop_new_image
        Image.mousePressEvent = self.getPos
        
        InputText1 = QLabel('Choose a strain rate [um/s]:')
        Input1 = QLineEdit()
        Input1.setMaxLength(5)
        Input1.setValidator(QDoubleValidator())
        Input1.textChanged.connect(self.set_strain_rate)
        InputText2 = QLabel('Choose the final strain [%]:')
        Input2 = QLineEdit()
        Input2.setMaxLength(5)
        Input2.setValidator(QDoubleValidator())
        Input2.textChanged.connect(self.set_final_strain)
        InputText3 = QLabel('Camera Pixel Size [um]:')
        Input3 = QLineEdit('%d' % self.PixelSize)
        Input3.setMaxLength(5)
        Input3.setValidator(QDoubleValidator())
        Input3.textChanged.connect(self.set_pixel_size)
        InputText4 = QLabel('Microscope magnification:')
        Input4 = QLineEdit('%d' % self.Magnification)
        Input4.setMaxLength(5)
        Input4.setValidator(QDoubleValidator())
        Input4.textChanged.connect(self.set_magnification)
        
        StartButton = QPushButton('Start Experiment')
        StartButton.mousePressEvent = self.start_experiment
        
        Grid = QGridLayout()
        Grid.setSpacing(10)
        Grid.addWidget(self.ImageDescription,0,0)
        Grid.addWidget(Image,1,0,6,1)
        Grid.addWidget(InputText1,1,1)
        Grid.addWidget(Input1,1,2)
        Grid.addWidget(InputText2,2,1)
        Grid.addWidget(Input2,2,2)
        Grid.addWidget(InputText3,3,1)
        Grid.addWidget(Input3,3,2)
        Grid.addWidget(InputText4,4,1)
        Grid.addWidget(Input4,4,2)
        Grid.addWidget(StartButton,5,1,1,2)
        
        Widget = QWidget()
        Widget.setLayout(Grid)
        
        self.setCentralWidget(Widget)
        
        self.setAcceptDrops(True)
        self.setWindowTitle('Bowstring') 
        self.setGeometry(300, 300, 700, 600) 
        self.show()
        
    def start_experiment(self,event):
        print('starting experiment...')
        self.send_instructions_to_jpk()

    def getPos(self , event):
        print(self.CurrentTipPosition)
        print(self.ImageFullfile)
        x = event.pos().x()
        y = event.pos().y()
        self.Points.append([x,y])
        if self.PointCounter == 3:
            self.PointCounter = -1
            self.Points = list()
        self.PointCounter += 1
        self.ImageDescription.setText(self.ImageDescriptionPrompts[self.PointCounter])
        print(self.Points)
        self.draw_geometry()
        
    def drop_new_image(self,s):
        print(s)
        
        
    def onLithModeButtonClick(self,s):
        if not s:
            self.LithModeButton.toggle()
            # TODO Switch between main widgets
        else:
            self.BowModeButton.toggle()
            
    def onBowModeButtonClick(self,s):
        if not s:
            self.BowModeButton.toggle()
            # TODO Switch between main widgets
        else:
            self.LithModeButton.toggle()
            
    def set_strain_rate(self,s):
        self.StrainRate = float(s)*1e-6
        print(self.StrainRate)
        self.draw_geometry()
        
    def set_pixel_size(self,s):
        self.PixelSize = float(s)*1e-6
        self.draw_geometry()
        
    def set_magnification(self,s):
        self.Magnification = float(s)
        self.draw_geometry()
        
    def set_final_strain(self,s):
        self.FinalStrain = float(s)/100
        self.draw_geometry()
            
    def draw_geometry(self):
         Bool = self.check_sufficient_information()
         print(Bool)
         if not Bool:
             return
         self.calculate_geometry()
         
    def calculate_geometry(self):
        A1 = np.array(self.Points[0])
        A2 = np.array(self.Points[1])
        T = np.array(self.Points[2])
        
        self.T = 1
        self.Anchor1 = A1 #Real world position of anchor 1
        self.Anchor2 = A2 #Real world position of anchor 2
        self.SegmentLength = np.linalg.norm(self.A1-self.A2)
        self.HalfPoint = (self.A1+self.A2)/2
        print('foo')

    def check_sufficient_information(self):
        if len(self.Points)==3 and not self.StrainRate==[] and not self.FinalStrain==[] and not self.Magnification==[] and not self.PixelSize==[]:
            Bool = True
        else:
            Bool = False
        return Bool

def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
