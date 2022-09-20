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
import os
import numpy as np



class PaintPixmap(QPixmap):
    def __init__(self, Path):
        super().__init__(Path)
        
        
    def paintEvent(self,PointList,PaintedObject='TestDrawing'):
        
        if len(PointList)==0:
            return
        
        Points = []
        FPoints = []
        for P in PointList:
            Points.append(QPoint(int(P[0]),int(P[1])))
            FPoints.append(QPointF(int(P[0]),int(P[1])))
        
        painter = QPainter(self)
        
        if PaintedObject=='User Points':
                painter.setPen(QPen(Qt.red,3))
                painter.setRenderHint(QPainter.Antialiasing)
                for p in FPoints:
                    painter.drawPoint(p)
                painter.end()
                painter = QPainter(self)
                painter.setPen(QPen(Qt.red,3))
                painter.setRenderHint(QPainter.Antialiasing)
                for p in FPoints:
                    Dist = 6
                    Len = 6
                    DistLen = Dist+Len
                    p11 = QPointF(p)
                    p12 = QPointF(p)
                    p11.setX(p11.x() - DistLen)
                    p12.setX(p12.x() - Dist)
                    p21 = QPointF(p)
                    p22 = QPointF(p)
                    p21.setX(p21.x() + DistLen)
                    p22.setX(p22.x() + Dist)
                    p31 = QPointF(p)
                    p32 = QPointF(p)
                    p31.setY(p31.y() - DistLen)
                    p32.setY(p32.y() - Dist)
                    p41 = QPointF(p)
                    p42 = QPointF(p)
                    p41.setY(p41.y() + DistLen)
                    p42.setY(p42.y() + Dist)
                    painter.drawLine(p11,p12)
                    painter.drawLine(p21,p22)
                    painter.drawLine(p31,p32)
                    painter.drawLine(p41,p42)
        elif PaintedObject=='Accessible Area':
                Rectangle = QRect(Points[0],Points[1])
                painter.setPen(QPen(Qt.cyan,4))
                painter.setRenderHint(QPainter.Antialiasing)
                painter.drawRect(Rectangle)
        elif PaintedObject=='Bowstring Geometry':
                painter.setPen(QPen(Qt.green,2))
                painter.setRenderHint(QPainter.Antialiasing)
                painter.drawLine(FPoints[0], FPoints[1])
                painter.drawLine(FPoints[0], FPoints[2])
                painter.drawLine(FPoints[1], FPoints[2])
                painter.drawLine(FPoints[3], FPoints[2])
                painter.setPen(QPen(Qt.green,1,Qt.DashLine))
                painter.drawLine(FPoints[4], FPoints[3])
        elif PaintedObject=='TestDrawing':
                painter = QPainter(self)
                painter.setPen(QPen(Qt.black,30,Qt.DashLine))
                painter.setRenderHint(QPainter.Antialiasing)
                painter.drawEllipse(450,250, 200, 400)
        
        painter.end()


class MainWindow(QMainWindow):
    
    def __init__(self,*args,**kwargs):
        super(MainWindow,self).__init__(*args,**kwargs)
        
        
        # Run the script like this: python BowstringWidget.py CurrentTipPositionX CurrentTipPositionY ImageFullFile
        #            e.g. on linux: python BowstringWidget.py 1.345e-6 1.0000e-6 "path/to/image/image.tif"
        #          e.g. on windows: python BowstringWidget.py 1.345e-6 1.0000e-6 "path\to\image\image.tif"
        # Note: on linux '' and "" work as string denomiators, in windows its just ""
        
        
        FullPath = os.path.abspath(str(sys.argv[0]))
        self.ProgramPath = os.path.dirname(FullPath)
        
        if len(sys.argv)<2:
            self.StartingTipPosition = [0, 0]
            self.ImageFullFile = os.path.join(self.ProgramPath,'TestImage.tif')
        else:
            self.StartingTipPosition = np.array([float(sys.argv[1]) , float(sys.argv[2])])
            self.ImageFullFile = str(sys.argv[3])
        
        
        self.ImageFullFile = os.path.abspath(self.ImageFullFile)
        self.ImagePath = os.path.dirname(self.ImageFullFile)
        
        print(self.ProgramPath)
        print(self.ImagePath)
        
        self.PointCounter = 0
        self.Points = list()
        self.PaHStrainRate = float(2e-6)
        self.PaHFinalStrain = float(.2)
        self.PixelSize = float(4.65e-6)
        self.Magnification = float(10)
        self.Tip2HalfPointBuffer = float(1e-5)
        self.PaHHoldingTime = 0
        
        toolbar = QToolBar('My main toolbar')
        toolbar.setIconSize(QSize(64,64))
        self.addToolBar(toolbar)
        
        self.BowModeButton = QAction(QIcon(os.path.join(self.ProgramPath,'icons/Bow.jpg')),"Bowstring mode", self)
        self.BowModeButton.setStatusTip("Design and run a Bowstring experiment")
        self.BowModeButton.triggered.connect(self.onBowModeButtonClick)
        self.BowModeButton.setCheckable(True)
        self.BowModeButton.toggle()
        toolbar.addAction(self.BowModeButton)
        
        toolbar.addSeparator()

        self.LithModeButton = QAction(QIcon(os.path.join(self.ProgramPath,"icons/Chisel.png")), "Nanolithography mode", self)
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
        
        self.Pixmap = PaintPixmap(self.ImageFullFile)
        self.Image = QLabel()
        self.Image.setPixmap(self.Pixmap)
        self.Image.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.Image.mousePressEvent = self.getPos
        
        self.MaxEditLength = 10
        
        Title1 = QLabel('Pull and hold')
        Title1.setFont(QFont('Arial',22))
        Title1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        InputText1 = QLabel('Choose a strain rate [um/s]:')
        Input1 = QLineEdit('%d' % (self.PaHStrainRate*1e6))
        Input1.setMaxLength(self.MaxEditLength)
        Input1.setValidator(QDoubleValidator())
        Input1.textChanged.connect(self.set_strain_rate)
        InputText2 = QLabel('Choose the final strain [%]:')
        Input2 = QLineEdit('%d' % (self.PaHFinalStrain*100))
        Input2.setMaxLength(self.MaxEditLength)
        Input2.setValidator(QDoubleValidator())
        Input2.textChanged.connect(self.set_final_strain)
        InputText3 = QLabel('Camera Pixel Size [um]:')
        Input3 = QLineEdit('%f' % (self.PixelSize*1e6))
        Input3.setMaxLength(self.MaxEditLength)
        Input3.setValidator(QDoubleValidator())
        Input3.textChanged.connect(self.set_pixel_size)
        InputText4 = QLabel('Microscope magnification:')
        Input4 = QLineEdit('%d' % (self.Magnification))
        Input4.setMaxLength(self.MaxEditLength)
        Input4.setValidator(QDoubleValidator())
        Input4.textChanged.connect(self.set_magnification)
        InputText5 = QLabel('Tip-to-Halfpoint Buffer [um]:')
        Input5 = QLineEdit('%d' % (self.Tip2HalfPointBuffer*1e6))
        Input5.setMaxLength(self.MaxEditLength)
        Input5.setValidator(QDoubleValidator())
        Input5.textChanged.connect(self.set_tip_to_halfpoint_buffer)
        InputText6 = QLabel('Holding Time [s]:')
        Input6 = QLineEdit('%d' % self.PaHHoldingTime)
        Input6.setMaxLength(self.MaxEditLength)
        Input6.setValidator(QDoubleValidator())
        Input6.textChanged.connect(self.set_holding_time)
        
        self.StartButton = QPushButton('Start Experiment')
        self.StartButton.mousePressEvent = self.start_experiment
        self.StartButton.setEnabled(False)
        
        Grid = QGridLayout()
        Grid.setSpacing(10)
        Grid.addWidget(self.ImageDescription,0,0)
        Grid.addWidget(self.Image,1,0,10,1)
        Grid.addWidget(Title1,1,1,1,2)
        Grid.addWidget(InputText1,2,1)
        Grid.addWidget(Input1,2,2)
        Grid.addWidget(InputText2,3,1)
        Grid.addWidget(Input2,3,2)
        Grid.addWidget(InputText3,4,1)
        Grid.addWidget(Input3,4,2)
        Grid.addWidget(InputText4,5,1)
        Grid.addWidget(Input4,5,2)
        Grid.addWidget(InputText5,6,1)
        Grid.addWidget(Input5,6,2)
        Grid.addWidget(InputText6,7,1)
        Grid.addWidget(Input6,7,2)
        Grid.addWidget(self.StartButton,8,1,1,2)
        
        self.Widget = QWidget()
        self.Widget.setLayout(Grid)
        
        self.setCentralWidget(self.Widget)
        
        self.setAcceptDrops(True)
        self.setWindowTitle('Bowstring') 
        self.setGeometry(300, 300, 700, 600) 
        self.show()
        
    def start_experiment(self,event):
        print('starting experiment...')
        self.send_instructions_pull_and_hold()

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
        if not s:
            return
        s = s.replace(',','.')
        self.PaHStrainRate = float(s)*1e-6
        self.draw_geometry()
        
    def set_pixel_size(self,s):
        if not s:
            return
        s = s.replace(',','.')
        self.PixelSize = float(s)*1e-6
        self.draw_geometry()
        
    def set_magnification(self,s):
        if not s:
            return
        s = s.replace(',','.')
        self.Magnification = float(s)
        self.draw_geometry()
        
    def set_final_strain(self,s):
        if not s:
            return
        s = s.replace(',','.')
        self.PaHFinalStrain = float(s)/100
        self.draw_geometry()
        
    def set_tip_to_halfpoint_buffer(self,s):
        if not s:
            return
        s = s.replace(',','.')
        self.Tip2HalfPointBuffer = float(s)*1e-6
        self.draw_geometry()
        
    def set_holding_time(self,s):
        if not s or s=='':
            self.set_holding_time('0')
            return
        s = s.replace(',','.')
        self.PaHHoldingTime = float(s)
        self.draw_geometry()
        
        
    def transform_coordinates_image2rl(self,InPoint):
        
        # transform InPoint to np array
        InPoint = np.array(InPoint)
        
        self.calculate_transformation_constants()
        
        if InPoint.size == 1:
            OutPoint = InPoint*self.Im2RlScalingVector[0]
            return OutPoint
        
        # shift InPoint to Origin
        InPoint = InPoint - self.RlOriginInImage
        # scale InPoint via SizePerPixel
        OutPoint = InPoint*self.Im2RlScalingVector
        
        return OutPoint
        
    def transform_coordinates_rl2image(self,InPoint):
        
        # transform InPoint to np array
        InPoint = np.array(InPoint)
        
        self.calculate_transformation_constants()
        
        if InPoint.size == 1:
            OutPoint = InPoint*self.Rl2ImScalingVector[0]
            return OutPoint
        
        # shift InPoint to Origin
        InPoint = InPoint - self.ImageOriginInRl
        # scale InPoint via SizePerPixel
        OutPoint = InPoint*self.Rl2ImScalingVector
        
        return OutPoint
    
    def calculate_transformation_constants(self):
        
        self.Im2RlScalingVector = np.array([1,-1])*self.PixelSize/self.Magnification
        self.Rl2ImScalingVector = np.array([1,-1])*self.Magnification/self.PixelSize
        self.RlOriginInImage = np.array(self.Points[2]) - self.StartingTipPosition*self.Rl2ImScalingVector
        self.ImageOriginInRl = self.StartingTipPosition - np.array(self.Points[2])*self.Im2RlScalingVector
        
        
            
    def draw_geometry(self):
         Bool = self.check_sufficient_information()
         
         self.Pixmap = PaintPixmap(self.ImageFullFile)
         self.Image.setPixmap(self.Pixmap)
         self.Pixmap.paintEvent(self.Points,'User Points')
         self.Image.setPixmap(self.Pixmap)
         
         if not Bool:
             return
         
         self.calculate_geometry()
         self.paint_experiment()
         
    def calculate_geometry(self):
        
        self.Anchor1 = self.transform_coordinates_image2rl(np.array(self.Points[0]))
        self.Anchor2 = self.transform_coordinates_image2rl(np.array(self.Points[1]))
        
        self.PaHSegmentLength = np.linalg.norm(self.Anchor1-self.Anchor2)
        self.HalfPoint = (self.Anchor1+self.Anchor2)/2
        self.SegmentDirection = (self.Anchor1 - self.Anchor2)/self.PaHSegmentLength
        self.PerpendicularDirection = np.array([-self.SegmentDirection[1],self.SegmentDirection[0]])
        self.PaHBufferPoint = self.HalfPoint - self.PerpendicularDirection*self.Tip2HalfPointBuffer
        self.PaHBowDrawingDistance = self.PaHSegmentLength/2*np.sqrt((1+self.PaHFinalStrain)**2 - 1)
        self.PaHFinalStrainPoint = self.HalfPoint + self.PerpendicularDirection*self.PaHBowDrawingDistance
        self.PaHTotalMovementTime = (self.PaHBowDrawingDistance + self.Tip2HalfPointBuffer)/self.PaHStrainRate
        
        if all([abs(self.PaHBufferPoint[0])<5e-5,abs(self.PaHBufferPoint[1])<5e-5,
                abs(self.PaHFinalStrainPoint[0])<5e-5,abs(self.PaHFinalStrainPoint[1])<5e-5]):
            self.StartButton.setEnabled(True)
        else:
            self.StartButton.setEnabled(False)
        
        

    def check_sufficient_information(self):
        if len(self.Points)==3 and all([self.PaHStrainRate,self.PaHFinalStrain,self.Magnification,self.PixelSize,self.Tip2HalfPointBuffer]):
            Bool = True
        else:
            Bool = False
            self.StartButton.setEnabled(False)
        
        return Bool
    
    def paint_experiment(self):
        
        self.Pixmap = PaintPixmap(self.ImageFullFile)
        self.Image.setPixmap(self.Pixmap)
        
        #TODO define list of points
        ListOfPoints = [1,1]
        TopLeft = self.transform_coordinates_rl2image([-5e-5, -5e-5])
        BottomRight = self.transform_coordinates_rl2image([5e-5,5e-5])
        InPoints1 = [TopLeft, BottomRight]
        self.Pixmap.paintEvent(InPoints1,'Accessible Area')
        InPoints2 = [
            self.transform_coordinates_rl2image(self.Anchor1),
            self.transform_coordinates_rl2image(self.Anchor2),
            self.transform_coordinates_rl2image(self.PaHFinalStrainPoint),
            self.transform_coordinates_rl2image(self.HalfPoint),
            self.transform_coordinates_rl2image(self.PaHBufferPoint)
            ]
        self.Pixmap.paintEvent(InPoints2,'Bowstring Geometry')
        self.Pixmap.paintEvent(self.Points,'User Points')
        self.Image.setPixmap(self.Pixmap)
    
    def send_instructions_pull_and_hold(self):
        
        print('-----------------')
        print('Anchor1 Rl: ' + str(self.Anchor1))
        print('Anchor2 Rl: ' + str(self.Anchor2))
        print('Segment Length Rl: ' + str(self.PaHSegmentLength))
        print('HalfPoint Rl: ' + str(self.HalfPoint))
        print('Cantilever Tip Rl: ' + str(self.StartingTipPosition))
        print('Final Position Rl: ' + str(self.PaHFinalStrainPoint))
        print('Buffer Position Rl: ' + str(self.PaHBufferPoint))
        print('Bow Drawing Distance Rl: ' + str(self.PaHBowDrawingDistance))
        print('-----------------')
        print('Anchor1 Image: ' + str(self.transform_coordinates_rl2image(self.Anchor1)))
        print('Anchor2 Image: ' + str(self.transform_coordinates_rl2image(self.Anchor2)))
        print('Segment Length Image: ' + str(self.transform_coordinates_rl2image(self.PaHSegmentLength)))
        print('HalfPoint Image: ' + str(self.transform_coordinates_rl2image(self.HalfPoint)))
        print('Cantilever Tip Image: ' + str(self.transform_coordinates_rl2image(self.StartingTipPosition)))
        print('Final Position Image: ' + str(self.transform_coordinates_rl2image(self.PaHFinalStrainPoint)))
        print('Buffer Position Image: ' + str(self.transform_coordinates_rl2image(self.PaHBufferPoint)))
        print('Bow Drawing Distance Image: ' + str(self.transform_coordinates_rl2image(self.PaHBowDrawingDistance)))
        print('-----------------')
        print('Anchor1 R2I2R: ' + str(self.transform_coordinates_image2rl(self.transform_coordinates_rl2image(self.Anchor1))))
        print('Anchor2 R2I2R: ' + str(self.transform_coordinates_image2rl(self.transform_coordinates_rl2image(self.Anchor2))))
        print('Segment Length R2I2R: ' + str(self.transform_coordinates_image2rl(self.transform_coordinates_rl2image(self.PaHSegmentLength))))
        print('HalfPoint R2I2R: ' + str(self.transform_coordinates_image2rl(self.transform_coordinates_rl2image(self.HalfPoint))))
        print('Cantilever Tip R2I2R: ' + str(self.transform_coordinates_image2rl(self.transform_coordinates_rl2image(self.StartingTipPosition))))
        print('Final Position R2I2R: ' + str(self.transform_coordinates_image2rl(self.transform_coordinates_rl2image(self.PaHFinalStrainPoint))))
        print('Buffer Position R2I2R: ' + str(self.transform_coordinates_image2rl(self.transform_coordinates_rl2image(self.PaHBufferPoint))))
        print('Bow Drawing Distance R2I2R: ' + str(self.transform_coordinates_image2rl(self.transform_coordinates_rl2image(self.PaHBowDrawingDistance))))
        print('-----------------')
        print('Buffer Position: ' + str(self.PaHBufferPoint))
        print('Final Position: ' + str(self.PaHFinalStrainPoint))
        print('')
        print('Projected Movement Time [s]: ' + str(self.PaHTotalMovementTime))
        print('-----------------')
        
        
        print(self.Im2RlScalingVector)
        print(self.Rl2ImScalingVector)
        print(self.RlOriginInImage)
        print(self.ImageOriginInRl)
        
        sys.stdout.flush()

def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
