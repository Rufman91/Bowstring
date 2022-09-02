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
        #                     e.g.: python BowstringWidget.py 1.345e-6 1.0000e-6 'TestImage.tif'
        if len(sys.argv)<3:
            self.ImageFullfile = 'TestImage.tif'
            self.CurrentTipPosition = [1.5e-6, 1e-6]
        else:
            self.ImageFullfile = sys.argv[3]
            self.CurrentTipPosition = [float(sys.argv[1]) , float(sys.argv[2])]
        
        self.PointCounter = 0
        self.Points = list()
        self.StrainRate = float(2e-6)
        self.FinalStrain = float(.2)
        self.PixelSize = float(0.5e-6)
        self.Magnification = float(200)
        self.Tip2HalfPointBuffer = float(5e-6)
        
        toolbar = QToolBar('My main toolbar')
        toolbar.setIconSize(QSize(64,64))
        self.addToolBar(toolbar)
        
        self.BowModeButton = QAction(QIcon('icons/Bow.jpg'),"Bowstring mode", self)
        self.BowModeButton.setStatusTip("Design and run a Bowstring experiment")
        self.BowModeButton.triggered.connect(self.onBowModeButtonClick)
        self.BowModeButton.setCheckable(True)
        self.BowModeButton.toggle()
        toolbar.addAction(self.BowModeButton)
        
        toolbar.addSeparator()

        self.LithModeButton = QAction(QIcon("icons/Chisel.png"), "Nanolithography mode", self)
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
        Input1 = QLineEdit('%d' % (self.StrainRate*1e6))
        Input1.setMaxLength(5)
        Input1.setValidator(QDoubleValidator())
        Input1.textChanged.connect(self.set_strain_rate)
        InputText2 = QLabel('Choose the final strain [%]:')
        Input2 = QLineEdit('%d' % (self.FinalStrain*100))
        Input2.setMaxLength(5)
        Input2.setValidator(QDoubleValidator())
        Input2.textChanged.connect(self.set_final_strain)
        InputText3 = QLabel('Camera Pixel Size [um]:')
        Input3 = QLineEdit('%d' % (self.PixelSize*1e6))
        Input3.setMaxLength(5)
        Input3.setValidator(QDoubleValidator())
        Input3.textChanged.connect(self.set_pixel_size)
        InputText4 = QLabel('Microscope magnification:')
        Input4 = QLineEdit('%d' % (self.Magnification))
        Input4.setMaxLength(5)
        Input4.setValidator(QDoubleValidator())
        Input4.textChanged.connect(self.set_magnification)
        InputText5 = QLabel('Tip-to-Halfpoint Buffer [um]:')
        Input5 = QLineEdit('%d' % (self.Tip2HalfPointBuffer*1e6))
        Input5.setMaxLength(5)
        Input5.setValidator(QDoubleValidator())
        Input5.textChanged.connect(self.set_tip_to_halfpoint_buffer)
        
        StartButton = QPushButton('Start Experiment')
        StartButton.mousePressEvent = self.start_experiment
        
        Grid = QGridLayout()
        Grid.setSpacing(10)
        Grid.addWidget(self.ImageDescription,0,0)
        Grid.addWidget(Image,1,0,10,1)
        Grid.addWidget(InputText1,1,1)
        Grid.addWidget(Input1,1,2)
        Grid.addWidget(InputText2,2,1)
        Grid.addWidget(Input2,2,2)
        Grid.addWidget(InputText3,3,1)
        Grid.addWidget(Input3,3,2)
        Grid.addWidget(InputText4,4,1)
        Grid.addWidget(Input4,4,2)
        Grid.addWidget(InputText5,5,1)
        Grid.addWidget(Input5,5,2)
        Grid.addWidget(StartButton,6,1,1,2)
        
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
        
    def set_tip_to_halfpoint_buffer(self,s):
        self.Tip2HalfPointBuffer = float(s)*1e-6
        self.draw_geometry
        
    def transform_coordinates_image2rl(self,InPoint):
        
        return OutPoint
        
    def transform_coordinates_rl2image(self,InPoint):
        
        return OutPoint
            
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
        
        self.InitialTipPosition = 1
        self.Anchor1 = A1 #Real world position of anchor 1
        self.Anchor2 = A2 #Real world position of anchor 2
        self.SegmentLength = np.linalg.norm(self.Anchor1-self.Anchor2)
        self.HalfPoint = (self.Anchor1+self.Anchor2)/2
        self.SegmentDirection = (self.Anchor1 - self.Anchor2)/self.SegmentLength
        self.PerpendicularDirection = np.array([-self.SegmentDirection[1],self.SegmentDirection[0]])
        
        print('foo')

    def check_sufficient_information(self):
        if len(self.Points)==3 and not self.StrainRate==[] and not self.FinalStrain==[] and not self.Magnification==[] and not self.PixelSize==[]:
            Bool = True
        else:
            Bool = False
        return Bool
    
    def send_instructions_to_jpk(self):
        print('Anchor1 ' + str(self.Anchor1))
        print('Anchor2 ' + str(self.Anchor2))
        print('HalfPoint ' + str(self.HalfPoint))

def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
