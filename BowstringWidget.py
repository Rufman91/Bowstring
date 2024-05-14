# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 17:38:41 2021

@author: Manuel Rufin, Project COSIMA
@institution: Institute of Lightweight Design and Structural Biomechanics, TU Wien, Austria
"""

import PyQt5.QtGui as PyGui
import PyQt5.QtWidgets as PyWidgets
import PyQt5.QtCore as PyCore
import time
import sys
import os
import numpy as np
from calibration import load_images, detect_afm_head, phase_correlation, estimate_transformation, transform_coordinates


class PaintPixmap(PyGui.QPixmap):
    def __init__(self, Path):
        super().__init__(Path)

    def paintEvent(self, PointList, PaintedObject='TestDrawing'):
        if len(PointList) == 0:
            return

        Points = []
        FPoints = []
        for P in PointList:
            Points.append(PyCore.QPoint(int(P[0]), int(P[1])))
            FPoints.append(PyCore.QPointF(int(P[0]), int(P[1])))

        painter = PyGui.QPainter(self)

        if PaintedObject == 'User Points':
            painter.setPen(PyGui.QPen(PyCore.Qt.red, 3))
            painter.setRenderHint(PyGui.QPainter.Antialiasing)
            for p in FPoints:
                painter.drawPoint(p)
            painter.end()
            painter = PyGui.QPainter(self)
            painter.setPen(PyGui.QPen(PyCore.Qt.red, 3))
            painter.setRenderHint(PyGui.QPainter.Antialiasing)
            for p in FPoints:
                Dist = 6
                Len = 6
                DistLen = Dist + Len
                p11 = PyCore.QPointF(p)
                p12 = PyCore.QPointF(p)
                p11.setX(p11.x() - DistLen)
                p12.setX(p12.x() - Dist)
                p21 = PyCore.QPointF(p)
                p22 = PyCore.QPointF(p)
                p21.setX(p21.x() + DistLen)
                p22.setX(p22.x() + Dist)
                p31 = PyCore.QPointF(p)
                p32 = PyCore.QPointF(p)
                p31.setY(p31.y() - DistLen)
                p32.setY(p32.y() - Dist)
                p41 = PyCore.QPointF(p)
                p42 = PyCore.QPointF(p)
                p41.setY(p41.y() + DistLen)
                p42.setY(p42.y() + Dist)
                painter.drawLine(p11, p12)
                painter.drawLine(p21, p22)
                painter.drawLine(p31, p32)
                painter.drawLine(p41, p42)
        elif PaintedObject == 'Accessible Area':
            Rectangle = PyCore.QRect(Points[0], Points[1])
            painter.setPen(PyGui.QPen(PyCore.Qt.cyan, 4))
            painter.setRenderHint(PyGui.QPainter.Antialiasing)
            painter.drawRect(Rectangle)
        elif PaintedObject == 'Bowstring Geometry':
            painter.setPen(PyGui.QPen(PyCore.Qt.green, 2))
            painter.setRenderHint(PyGui.QPainter.Antialiasing)
            painter.drawLine(FPoints[0], FPoints[1])
            painter.drawLine(FPoints[0], FPoints[2])
            painter.drawLine(FPoints[1], FPoints[2])
            painter.drawLine(FPoints[3], FPoints[2])
            painter.setPen(PyGui.QPen(PyCore.Qt.green, 1, PyCore.Qt.DashLine))
            painter.drawLine(FPoints[4], FPoints[3])
        elif PaintedObject == 'Scratch-Off Geometry':
            painter.setPen(PyGui.QPen(PyCore.Qt.darkGreen, 1))
            painter.setRenderHint(PyGui.QPainter.Antialiasing)
            
            # Draw each scratch line between points
            for i in range(0, int(len(FPoints)/2)):
                painter.drawLine(FPoints[i], FPoints[i+int(len(FPoints)/2)])
            

        elif PaintedObject == 'TestDrawing':
            painter = PyGui.QPainter(self)
            painter.setPen(PyGui.QPen(PyCore.Qt.black, 30, PyCore.Qt.DashLine))
            painter.setRenderHint(PyGui.QPainter.Antialiasing)
            painter.drawEllipse(450, 250, 200, 400)

        painter.end()

class MainWindow(PyWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Run the script like this: python BowstringWidget.py CurrentTipPositionX CurrentTipPositionY ImageFullFile
        #            e.g. on linux: python BowstringWidget.py 1.345e-6 1.0000e-6 "path/to/image/image.tif"
        #          e.g. on windows: python BowstringWidget.py 1.345e-6 1.0000e-6 "path\to\image\image.tif"
        # Note: on linux '' and "" work as string denomiators, in windows its just ""

        FullPath = os.path.abspath(str(sys.argv[0]))
        self.ProgramPath = os.path.dirname(FullPath)

        if len(sys.argv) < 2:
            self.StartingTipPosition = [4.999e-5, 4.999e-5]
            self.ImageFullFile = os.path.join(self.ProgramPath, 'TestImage.tif')
        else:
            self.StartingTipPosition = np.array([float(sys.argv[1]), float(sys.argv[2])])
            self.ImageFullFile = str(sys.argv[3])

        self.ImageFullFile = os.path.abspath(self.ImageFullFile)
        self.ImagePath = os.path.dirname(self.ImageFullFile)

        self.InstructionStartString = 'InstructionStart'
        self.InstructionEndString = 'InstructionEnd'

        self.UpperPiezoRange = 4.999e-5
        self.LowerPiezoRange = -4.999e-5

        # General settings
        self.PositioningVelocity = float(1e-5)
        self.RecordVideo = False
        self.RecordVideoNthFrame = 5
        self.RecordRealTimeScan = True
        
        # Coordiante Transformation Calibration
        
        self.PixelSize = float(4.65e-6)
        self.Magnification = float(10)
        self.calibration_matrix = None
        self.use_model_based_transformation = True

        self.PointCounter = 0
        self.Points = list()

        # Pull and Hold mode
        self.PaHStrainRate = float(2e-6)
        self.PaHFinalStrain = float(.2)
        self.PaHTip2HalfPointBuffer = float(1e-5)
        self.PaHHoldingTime = 0

        # Scratch off mode
        self.SOStrainRate = float(2e-6)
        self.SOFinalStrain = float(.2)
        self.SOTip2HalfPointBuffer = float(1e-5)
        self.SODistToAnchors = float(1e-5)
        self.SONumScratchPoints = 20
        self.SONumRepeats = 1
        self.SOShowScratchLines = True
        self.SOFinalStrainPoints = []
        self.SOBufferPoints = []

        toolbar = PyWidgets.QToolBar('My main toolbar')
        toolbar.setIconSize(PyCore.QSize(64, 64))
        self.addToolBar(toolbar)

        self.BowModeButton = PyWidgets.QAction(PyGui.QIcon(os.path.join(self.ProgramPath, 'icons/Bow.jpg')), "Bowstring mode", self)
        self.BowModeButton.setStatusTip("Design and run a Bowstring experiment")
        self.BowModeButton.triggered.connect(self.onBowModeButtonClick)
        self.BowModeButton.setCheckable(True)
        self.BowModeButton.toggle()
        toolbar.addAction(self.BowModeButton)

        toolbar.addSeparator()

        self.LithModeButton = PyWidgets.QAction(PyGui.QIcon(os.path.join(self.ProgramPath, "icons/Chisel.png")), "Nanolithography mode", self)
        self.LithModeButton.setStatusTip("This is just a placeholder for Nanolithography mode")
        self.LithModeButton.triggered.connect(self.onLithModeButtonClick)
        self.LithModeButton.setCheckable(True)
        toolbar.addAction(self.LithModeButton)

        toolbar.addSeparator()

        self.setStatusBar(PyWidgets.QStatusBar(self))

        # Now we start adding widgets!

        self.ImageDescriptionPrompts = ['Set the first fibril anchorpoint', 'Set the second fibril anchorpoint', 'Set the exact position of the cantilever tip', 'Clicking again will reset all points']
        self.ImageDescription = PyWidgets.QLabel(self.ImageDescriptionPrompts[self.PointCounter])
        self.ImageDescription.setFont(PyGui.QFont('Arial', 20))

        self.Pixmap = PaintPixmap(self.ImageFullFile)
        self.Image = PyWidgets.QLabel()
        self.Image.setPixmap(self.Pixmap)
        self.Image.setAlignment(PyCore.Qt.AlignHCenter | PyCore.Qt.AlignTop)
        self.Image.mousePressEvent = self.getPos

        # New Calibration Section
        self.TitleFontSize = 16
        self.MaxEditLength = 10

        # General Settings
        Title0 = PyWidgets.QLabel('General Settings')
        Title0.setFont(PyGui.QFont('Arial', self.TitleFontSize))

        InputText7 = PyWidgets.QLabel('Positioning Velocity [um/s]:')
        Input7 = PyWidgets.QLineEdit('%.1f' % (self.PositioningVelocity * 1e6))
        Input7.setMaxLength(self.MaxEditLength)
        Input7.setValidator(PyGui.QDoubleValidator())
        Input7.textChanged.connect(self.set_positioning_velocity)
        
        Input8 = PyWidgets.QCheckBox('Record Real Time Scan:')
        Input8.setChecked(self.RecordRealTimeScan)
        Input8.stateChanged.connect(self.set_record_real_time_scan)
        
        Input9 = PyWidgets.QCheckBox('Record Real Time Video:')
        Input9.setChecked(self.RecordVideo)
        Input9.stateChanged.connect(self.set_record_video)
        
        InputText10 = PyWidgets.QLabel('Record every Nth frame: N =')
        Input10 = PyWidgets.QLineEdit('%d' % self.RecordVideoNthFrame)
        Input10.setMaxLength(4)
        Input10.setValidator(PyGui.QIntValidator())
        Input10.textChanged.connect(self.set_record_video_nth_frame)

        # Coordinate Transformation Calibration
        TitleCalibration = PyWidgets.QLabel('Coordinate Transformation Calibration')
        TitleCalibration.setFont(PyGui.QFont('Arial', self.TitleFontSize))

        InputText3 = PyWidgets.QLabel('Camera Pixel Size [um]:')
        Input3 = PyWidgets.QLineEdit('%.3f' % (self.PixelSize * 1e6))
        Input3.setMaxLength(self.MaxEditLength)
        Input3.setValidator(PyGui.QDoubleValidator())
        Input3.textChanged.connect(self.set_pixel_size)
        
        InputText4 = PyWidgets.QLabel('Microscope Magnification:')
        Input4 = PyWidgets.QLineEdit('%.1f' % (self.Magnification))
        Input4.setMaxLength(self.MaxEditLength)
        Input4.setValidator(PyGui.QDoubleValidator())
        Input4.textChanged.connect(self.set_magnification)

        self.CalibrateButton = PyWidgets.QPushButton('Start Calibration')
        self.CalibrateButton.clicked.connect(self.start_calibration)

        self.TransformSwitch = PyWidgets.QCheckBox('Use Model-Based Transformation')
        self.TransformSwitch.setChecked(True)
        self.TransformSwitch.stateChanged.connect(self.switch_transformation)
        self.TransformSwitch.setEnabled(False)  # Disabled initially

        # Layout adjustments
        Spacing = 24
        Grid = PyWidgets.QGridLayout()
        Grid.setSpacing(Spacing)
        
        # Add the image description and image
        Grid.addWidget(self.ImageDescription, 0, 0, 1, 4)
        Grid.addWidget(self.Image, 1, 0, Spacing-1, 4)
        
        # General Settings
        Grid.addWidget(Title0, 0, 4, 1, 2)
        Grid.addWidget(InputText7, 1, 4)
        Grid.addWidget(Input7, 1, 5)
        Grid.addWidget(Input8, 2, 4, 1, 2)
        Grid.addWidget(Input9, 3, 4, 1, 2)
        Grid.addWidget(InputText10, 4, 4)
        Grid.addWidget(Input10, 4, 5)
        
        # Coordinate Transformation Calibration
        Grid.addWidget(TitleCalibration, 5, 4, 1, 2)
        Grid.addWidget(InputText3, 6, 4)
        Grid.addWidget(Input3, 6, 5)
        Grid.addWidget(InputText4, 7, 4)
        Grid.addWidget(Input4, 7, 5)
        Grid.addWidget(self.CalibrateButton, 8, 4, 1, 2)
        Grid.addWidget(self.TransformSwitch, 9, 4, 1, 2)

        # Pull and Hold settings
        Title1 = PyWidgets.QLabel('Pull and Hold')
        Title1.setFont(PyGui.QFont('Arial', self.TitleFontSize))
        InputText1 = PyWidgets.QLabel('Choose a strain rate [um/s]:')
        Input1 = PyWidgets.QLineEdit('%.2f' % (self.PaHStrainRate * 1e6))
        Input1.setMaxLength(self.MaxEditLength)
        Input1.setValidator(PyGui.QDoubleValidator())
        Input1.textChanged.connect(self.set_strain_rate)
        
        InputText2 = PyWidgets.QLabel('Choose the final strain [%]:')
        Input2 = PyWidgets.QLineEdit('%.2f' % (self.PaHFinalStrain * 100))
        Input2.setMaxLength(self.MaxEditLength)
        Input2.setValidator(PyGui.QDoubleValidator())
        Input2.textChanged.connect(self.set_final_strain)
        
        InputText5 = PyWidgets.QLabel('Tip-to-Halfpoint Buffer [um]:')
        Input5 = PyWidgets.QLineEdit('%.2f' % (self.PaHTip2HalfPointBuffer * 1e6))
        Input5.setMaxLength(self.MaxEditLength)
        Input5.setValidator(PyGui.QDoubleValidator())
        Input5.textChanged.connect(self.set_tip_to_halfpoint_buffer)
        
        InputText6 = PyWidgets.QLabel('Holding Time [s]:')
        Input6 = PyWidgets.QLineEdit('%.2f' % self.PaHHoldingTime)
        Input6.setMaxLength(self.MaxEditLength)
        Input6.setValidator(PyGui.QDoubleValidator())
        Input6.textChanged.connect(self.set_holding_time)
        
        self.StartPaHButton = PyWidgets.QPushButton('Start Experiment')
        self.StartPaHButton.mousePressEvent = self.send_instructions_pull_and_hold
        self.StartPaHButton.setEnabled(False)
        
        self.StartPaHPCButton = PyWidgets.QPushButton('Cycle Positions')
        self.StartPaHPCButton.mousePressEvent = self.send_instructions_pull_and_hold_position_check
        self.StartPaHPCButton.setEnabled(False)

        Grid.addWidget(Title1, 10, 4, 1, 2)
        Grid.addWidget(InputText1, 11, 4)
        Grid.addWidget(Input1, 11, 5)
        Grid.addWidget(InputText2, 12, 4)
        Grid.addWidget(Input2, 12, 5)
        Grid.addWidget(InputText5, 13, 4)
        Grid.addWidget(Input5, 13, 5)
        Grid.addWidget(InputText6, 14, 4)
        Grid.addWidget(Input6, 14, 5)
        Grid.addWidget(self.StartPaHPCButton, 15, 4, 1, 2)
        Grid.addWidget(self.StartPaHButton, 16, 4, 1, 2)
        
        # Scratch Off settings
        Title2 = PyWidgets.QLabel('Scratch Off')
        Title2.setFont(PyGui.QFont('Arial', self.TitleFontSize))
        InputText11 = PyWidgets.QLabel('Choose a strain rate [um/s]:')
        Input11 = PyWidgets.QLineEdit('%.2f' % (self.SOStrainRate * 1e6))
        Input11.setMaxLength(self.MaxEditLength)
        Input11.setValidator(PyGui.QDoubleValidator())
        Input11.textChanged.connect(self.set_so_strain_rate)
        
        InputText12 = PyWidgets.QLabel('Choose the final strain [%]:')
        Input12 = PyWidgets.QLineEdit('%.2f' % (self.SOFinalStrain * 100))
        Input12.setMaxLength(self.MaxEditLength)
        Input12.setValidator(PyGui.QDoubleValidator())
        Input12.textChanged.connect(self.set_so_final_strain)
        
        InputText13 = PyWidgets.QLabel('Tip-to-String-Buffer [um]:')
        Input13 = PyWidgets.QLineEdit('%.2f' % (self.SOTip2HalfPointBuffer * 1e6))
        Input13.setMaxLength(self.MaxEditLength)
        Input13.setValidator(PyGui.QDoubleValidator())
        Input13.textChanged.connect(self.set_so_tip_to_string_buffer)
        
        InputText14 = PyWidgets.QLabel('Safety Distance to Anchors [um]:')
        Input14 = PyWidgets.QLineEdit('%.2f' % (self.SODistToAnchors * 1e6))
        Input14.setMaxLength(self.MaxEditLength)
        Input14.setValidator(PyGui.QDoubleValidator())
        Input14.textChanged.connect(self.set_so_safety_distance_to_anchors)
        
        InputText15 = PyWidgets.QLabel('Set number of scratching points: N =')
        Input15 = PyWidgets.QLineEdit('%d' % self.SONumScratchPoints)
        Input15.setMaxLength(4)
        Input15.setValidator(PyGui.QIntValidator())
        Input15.textChanged.connect(self.set_so_number_of_scratch_points)
        
        InputText16 = PyWidgets.QLabel('Set number of repeats: N =')
        Input16 = PyWidgets.QLineEdit('%d' % self.SONumRepeats)
        Input16.setMaxLength(4)
        Input16.setValidator(PyGui.QIntValidator())
        Input16.textChanged.connect(self.set_so_number_of_repeats)
        
        Input17 = PyWidgets.QCheckBox('Show Scratch-Off Lines')
        Input17.setChecked(self.SOShowScratchLines)
        Input17.stateChanged.connect(self.set_so_show_scratch_lines)
        
        self.StartSOButton = PyWidgets.QPushButton('Start Scratching Off')
        self.StartSOButton.mousePressEvent = self.send_instructions_scratch_off
        self.StartSOButton.setEnabled(False)

        Grid.addWidget(Title2, 17, 4, 1, 2)
        Grid.addWidget(InputText11, 18, 4)
        Grid.addWidget(Input11, 18, 5)
        Grid.addWidget(InputText12, 19, 4)
        Grid.addWidget(Input12, 19, 5)
        Grid.addWidget(InputText13, 20, 4)
        Grid.addWidget(Input13, 20, 5)
        Grid.addWidget(InputText14, 21, 4)
        Grid.addWidget(Input14, 21, 5)
        Grid.addWidget(InputText15, 22, 4)
        Grid.addWidget(Input15, 22, 5)
        Grid.addWidget(InputText16, 23, 4)
        Grid.addWidget(Input16, 23, 5)
        Grid.addWidget(Input17, 24, 4, 1, 2)
        Grid.addWidget(self.StartSOButton, 25, 4, 1, 2)

        self.Widget = PyWidgets.QWidget()
        self.Widget.setLayout(Grid)

        self.setCentralWidget(self.Widget)
        
        # Screen Size Calculation
        screen = PyWidgets.QDesktopWidget().screenGeometry()
        screenWidth = screen.width()
        screenHeight = screen.height()

        # Set window size to 80% of the screen size
        self.setGeometry(100, 100, screenWidth * 0.8, screenHeight * 0.8)

        # Set the minimum size if necessary (could be smaller)
        self.setMinimumSize(screenWidth * 0.5, screenHeight * 0.5)
        
        self.setAcceptDrops(True)
        self.setWindowTitle('Bowstring')
        # self.setGeometry(200, 200, 300, 600)
        self.show()
        

    def initialize_scratch_off_points(self):
        
        Bool = self.check_sufficient_information()

        if not Bool:
            return
        
        # Calculate anchor points and scale based on pixel size and magnification
        anchor1 = np.array(self.transform_coordinates_image2rl(self.Points[0]))
        anchor2 = np.array(self.transform_coordinates_image2rl(self.Points[1]))
    
        # Compute the total distance between the anchors
        total_anchor_distance = np.linalg.norm(anchor2 - anchor1)
    
        # Compute the effective length of scratch-off points, subtracting the safety distances from both sides
        effective_length = total_anchor_distance - 2 * self.SODistToAnchors
    
        # Calculate the position of each scratch point along the base line
        self.SOBufferPoints = []
        self.SOFinalStrainPoints = []
        if self.SONumScratchPoints >= 1:
            for i in range(self.SONumScratchPoints):
                # Position of each point along the line, normalized to effective length
                t = (i + 1) / (self.SONumScratchPoints + 1)
                scratch_point = anchor1 + (anchor2 - anchor1) * ((self.SODistToAnchors / total_anchor_distance) + t * (effective_length / total_anchor_distance))  # linear interpolation
                
                mid_point = anchor1 + (anchor2 - anchor1) / 2
                
                # Calculate orthogonal direction from scratch point
                orthogonal_direction = np.array([-(anchor2[1] - anchor1[1]), anchor2[0] - anchor1[0]])
                orthogonal_direction = orthogonal_direction / np.linalg.norm(orthogonal_direction)  # normalize
    
                # Calculate half point (offset by half buffer)
                buffer_point = scratch_point + self.SOTip2HalfPointBuffer * orthogonal_direction
                self.SOBufferPoints.append(buffer_point)
    
                # Calculate final strain point based on a percentage of the base line length
                final_strain_height = self.SOFinalStrain * total_anchor_distance
                final_strain_height = (1 - np.linalg.norm(mid_point - scratch_point)*2/total_anchor_distance) * total_anchor_distance / 2 * np.sqrt((1 + self.SOFinalStrain) ** 2 - 1)
                final_strain_point = scratch_point - final_strain_height * orthogonal_direction
                self.SOFinalStrainPoints.append(final_strain_point)
        else:
            print("Error: Number of scratch points must be greater than zero")
    
    
        LogList = []
        for i in range(len(self.SOFinalStrainPoints)):
            LogList.append(all([abs(self.SOBufferPoints[i][0]) < 5e-5, 
                        abs(self.SOBufferPoints[i][1]) < 5e-5, 
                        abs(self.SOFinalStrainPoints[i][0]) < 5e-5, 
                        abs(self.SOFinalStrainPoints[i][1]) < 5e-5]))
        
        if all(LogList):
            self.StartSOButton.setEnabled(True)
        else:
            self.StartSOButton.setEnabled(False)    
    
        self.update_scratch_off_visualization()



    def update_scratch_off_visualization(self):
        if self.SOShowScratchLines == False:
            return
        elif self.SOShowScratchLines == True:
            # Visualize the scratch-off setup points
            points = [self.transform_coordinates_rl2image(point) for point in self.SOFinalStrainPoints]
            BuffPoints = [self.transform_coordinates_rl2image(point) for point in self.SOBufferPoints]
            points = points + BuffPoints
            self.Pixmap.paintEvent(points, 'Scratch-Off Geometry')  # This assumes your paintEvent can handle this new type
            self.Image.setPixmap(self.Pixmap)

    def getPos(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.Points.append([x, y])
        if self.PointCounter == 3:
            self.PointCounter = -1
            self.Points = list()
        self.PointCounter += 1
        self.ImageDescription.setText(self.ImageDescriptionPrompts[self.PointCounter])
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def onLithModeButtonClick(self, s):
        if not s:
            self.LithModeButton.toggle()
            # TODO Switch between main widgets
        else:
            self.BowModeButton.toggle()

    def onBowModeButtonClick(self, s):
        if not s:
            self.BowModeButton.toggle()
            # TODO Switch between main widgets
        else:
            self.LithModeButton.toggle()

    def set_strain_rate(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.PaHStrainRate = float(s) * 1e-6
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_pixel_size(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.PixelSize = float(s) * 1e-6
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_magnification(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.Magnification = float(s)
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_final_strain(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.PaHFinalStrain = float(s) / 100
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_tip_to_halfpoint_buffer(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.PaHTip2HalfPointBuffer = float(s) * 1e-6
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_holding_time(self, s):
        if not s or s == '':
            self.set_holding_time('0')
            return
        s = s.replace(',', '.')
        self.PaHHoldingTime = float(s)
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_positioning_velocity(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.PositioningVelocity = float(s) * 1e-6
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_record_video_nth_frame(self, s):
        if not s:
            return
        self.RecordVideoNthFrame = int(s)

    def set_record_real_time_scan(self, s):
        self.RecordRealTimeScan = bool(s)

    def set_record_video(self, s):
        self.RecordVideo = bool(s)

    def set_so_strain_rate(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.SOStrainRate = float(s) * 1e-6
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_so_final_strain(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.SOFinalStrain = float(s) / 100
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_so_tip_to_string_buffer(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.SOTip2HalfPointBuffer = float(s) * 1e-6
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_so_safety_distance_to_anchors(self, s):
        if not s:
            return
        
        # Calculate anchor points and scale based on pixel size and magnification
        anchor1 = np.array(self.transform_coordinates_image2rl(self.Points[0]))
        anchor2 = np.array(self.transform_coordinates_image2rl(self.Points[1]))
    
        # Compute the total distance between the anchors
        total_anchor_distance = np.linalg.norm(anchor2 - anchor1)
        
        s = s.replace(',', '.')
        self.SODistToAnchors = min(float(s) * 1e-6,total_anchor_distance/3);
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_so_number_of_scratch_points(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.SONumScratchPoints = int(s)
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_so_number_of_repeats(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.SONumRepeats = int(s)
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_so_show_scratch_lines(self, s):
        self.SOShowScratchLines = bool(s)
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def start_calibration(self):
        # Implement the calibration logic here
        # This should involve loading the images, detecting positions, and calculating the transformation matrix
        image_paths = [...]  # List of image paths for calibration
        images = load_images(image_paths)
        template = ...  # Load template image of the AFM head
    
        positions_image = [detect_afm_head(image, template) for image in images]
        positions_afm = [...]  # Known AFM positions
    
        self.calibration_matrix = estimate_transformation(positions_image, positions_afm)
        self.TransformSwitch.setChecked(False)
        self.TransformSwitch.setEnabled(True)
    
    def switch_transformation(self, state):
        if state == PyCore.Qt.Checked:
            # Use model-based transformation
            self.use_model_based_transformation = True
        else:
            # Use calibrated transformation if available
            if self.calibration_matrix is not None:
                self.use_model_based_transformation = False
            else:
                PyWidgets.QMessageBox.warning(self, 'Error', 'Calibration data not available. Reverting to model-based transformation.')
                self.TransformSwitch.setChecked(True)


    def transform_coordinates_image2rl(self, InPoint):
        InPoint = np.array(InPoint)
        if self.use_model_based_transformation:
            self.calculate_transformation_constants()
            if InPoint.size == 1:
                OutPoint = InPoint * self.Im2RlScalingVector[0]
                return OutPoint
    
            InPoint = InPoint - self.RlOriginInImage
            OutPoint = InPoint * self.Im2RlScalingVector
        else:
            # Use calibrated transformation
            OutPoint = transform_coordinates(InPoint, self.calibration_matrix)

        return OutPoint

    def transform_coordinates_rl2image(self, InPoint):
        InPoint = np.array(InPoint)
        if self.use_model_based_transformation:
            self.calculate_transformation_constants()
            if InPoint.size == 1:
                OutPoint = InPoint * self.Rl2ImScalingVector[0]
                return OutPoint
    
            InPoint = InPoint - self.ImageOriginInRl
            OutPoint = InPoint * self.Rl2ImScalingVector
        else:
            # Use calibrated transformation
            # Apply inverse of calibration matrix for reverse transformation
            inv_calibration_matrix = np.linalg.inv(self.calibration_matrix)
            OutPoint = transform_coordinates(InPoint, inv_calibration_matrix)

        return OutPoint


    def calculate_transformation_constants(self):
        self.Im2RlScalingVector = np.array([1, -1]) * self.PixelSize / self.Magnification
        self.Rl2ImScalingVector = np.array([1, -1]) * self.Magnification / self.PixelSize
        self.RlOriginInImage = np.array(self.Points[2]) - self.StartingTipPosition * self.Rl2ImScalingVector
        self.ImageOriginInRl = self.StartingTipPosition - np.array(self.Points[2]) * self.Im2RlScalingVector

    def draw_geometry(self):
        Bool = self.check_sufficient_information()

        self.Pixmap = PaintPixmap(self.ImageFullFile)
        self.Image.setPixmap(self.Pixmap)
        self.Pixmap.paintEvent(self.Points, 'User Points')
        self.Image.setPixmap(self.Pixmap)

        if not Bool:
            return

        self.calculate_geometry()
        self.paint_experiment()

    def calculate_geometry(self):
        self.Anchor1 = self.transform_coordinates_image2rl(np.array(self.Points[0]))
        self.Anchor2 = self.transform_coordinates_image2rl(np.array(self.Points[1]))

        self.PaHSegmentLength = np.linalg.norm(self.Anchor1 - self.Anchor2)
        self.HalfPoint = (self.Anchor1 + self.Anchor2) / 2
        self.SegmentDirection = (self.Anchor1 - self.Anchor2) / self.PaHSegmentLength
        self.PerpendicularDirection = np.array([-self.SegmentDirection[1], self.SegmentDirection[0]])
        self.PaHBufferPoint = self.HalfPoint - self.PerpendicularDirection * self.PaHTip2HalfPointBuffer
        self.PaHBowDrawingDistance = self.PaHSegmentLength / 2 * np.sqrt((1 + self.PaHFinalStrain) ** 2 - 1)
        self.PaHFinalStrainPoint = self.HalfPoint + self.PerpendicularDirection * self.PaHBowDrawingDistance
        self.PaHTotalMovementTime = (self.PaHBowDrawingDistance + self.PaHTip2HalfPointBuffer) / self.PaHStrainRate

        if all([abs(self.PaHBufferPoint[0]) < 5e-5, abs(self.PaHBufferPoint[1]) < 5e-5,
                abs(self.PaHFinalStrainPoint[0]) < 5e-5, abs(self.PaHFinalStrainPoint[1]) < 5e-5]):
            self.StartPaHButton.setEnabled(True)
            self.StartPaHPCButton.setEnabled(True)
        else:
            self.StartPaHButton.setEnabled(False)
            self.StartPaHPCButton.setEnabled(False)

    def check_sufficient_information(self):
        valid_bow = len(self.Points) == 3 and all(
            [self.PaHStrainRate, self.PaHFinalStrain, self.Magnification, self.PixelSize, self.PaHTip2HalfPointBuffer])
        # valid_scratch = len(self.SOFinalStrainPoints) > 0  # Ensure points are initialized
        valid_scratch = True
        return valid_bow and valid_scratch

    def paint_experiment(self):
        self.Pixmap = PaintPixmap(self.ImageFullFile)
        self.Image.setPixmap(self.Pixmap)

        # TODO define list of points
        ListOfPoints = [1, 1]
        TopLeft = self.transform_coordinates_rl2image([self.LowerPiezoRange, self.LowerPiezoRange])
        BottomRight = self.transform_coordinates_rl2image([self.UpperPiezoRange, self.UpperPiezoRange])
        InPoints1 = [TopLeft, BottomRight]
        self.Pixmap.paintEvent(InPoints1, 'Accessible Area')
        InPoints2 = [
            self.transform_coordinates_rl2image(self.Anchor1),
            self.transform_coordinates_rl2image(self.Anchor2),
            self.transform_coordinates_rl2image(self.PaHFinalStrainPoint),
            self.transform_coordinates_rl2image(self.HalfPoint),
            self.transform_coordinates_rl2image(self.PaHBufferPoint)
        ]
        self.Pixmap.paintEvent(InPoints2, 'Bowstring Geometry')
        self.Pixmap.paintEvent(self.Points, 'User Points')
        self.Image.setPixmap(self.Pixmap)

    def enable_instruction_send_buttons(self, Bool):
        self.StartPaHButton.setEnabled(Bool)
        self.StartPaHPCButton.setEnabled(Bool)

    def send_instructions_pull_and_hold(self, event):
        InList = [['PullAndHold', str(self.RecordRealTimeScan), str(self.RecordVideo), str(self.RecordVideoNthFrame)],
                  [str(self.PaHBufferPoint[0]), str(self.PaHBufferPoint[1]), str(self.PositioningVelocity), '0', 'Retracted'],
                  [str(self.HalfPoint[0]), str(self.HalfPoint[1]), str(self.PaHStrainRate), '0', 'Approached'],
                  [str(self.PaHFinalStrainPoint[0]), str(self.PaHFinalStrainPoint[1]), str(self.PaHStrainRate),
                   str(self.PaHHoldingTime), 'Approached'],
                  [str(self.StartingTipPosition[0]), str(self.StartingTipPosition[1]), str(self.PositioningVelocity), '0',
                   'Retracted'],
                  ]

        Instructions = self.construct_and_send_instructions(InList)

    def send_instructions_pull_and_hold_position_check(self, event):
        PositionCheckHoldingTime = '1'

        InList = [['PullAndHoldPositionCheck', str(self.RecordRealTimeScan), str(self.RecordVideo), str(self.RecordVideoNthFrame)],
                  [str(self.Anchor1[0]), str(self.Anchor1[1]), str(self.PositioningVelocity), PositionCheckHoldingTime, 'Retracted'],
                  [str(self.Anchor2[0]), str(self.Anchor2[1]), str(self.PositioningVelocity), PositionCheckHoldingTime, 'Retracted'],
                  [str(self.PaHBufferPoint[0]), str(self.PaHBufferPoint[1]), str(self.PositioningVelocity),
                   PositionCheckHoldingTime, 'Retracted'],
                  [str(self.HalfPoint[0]), str(self.HalfPoint[1]), str(self.PositioningVelocity), PositionCheckHoldingTime,
                   'Retracted'],
                  [str(self.PaHFinalStrainPoint[0]), str(self.PaHFinalStrainPoint[1]), str(self.PositioningVelocity),
                   PositionCheckHoldingTime, 'Retracted'],
                  [str(self.StartingTipPosition[0]), str(self.StartingTipPosition[1]), str(self.PositioningVelocity),
                   PositionCheckHoldingTime, 'Retracted'],
                  ]

        Instructions = self.construct_and_send_instructions(InList)

    def send_instructions_scratch_off(self, event):
        SOHoldingTime = '0'
    
        InList = [['Scratch Off', str(self.RecordRealTimeScan), str(self.RecordVideo), str(self.RecordVideoNthFrame)]]
    
        for i in range(len(self.SOFinalStrainPoints)):
            InList.append(
                [str(self.SOBufferPoints[i][0]), str(self.SOBufferPoints[i][1]), str(self.PositioningVelocity), SOHoldingTime,
                 'Retracted'])
            InList.append(
                [str(self.SOFinalStrainPoints[i][0]), str(self.SOFinalStrainPoints[i][1]), str(self.SOStrainRate), SOHoldingTime,
                 'Approached'])
    
        InList.append([str(self.StartingTipPosition[0]), str(self.StartingTipPosition[1]), str(self.PositioningVelocity), SOHoldingTime,
                       'Retracted'])
    
        Instructions = self.construct_and_send_instructions(InList)


    def construct_and_send_instructions(self, InList):
        Instructions = [self.InstructionStartString]

        # Clip all numbers outside of piezorange
        First = InList.pop(0)
        for S in InList:
            S[0] = str(np.clip(float(S[0]), self.LowerPiezoRange, self.UpperPiezoRange))
            S[1] = str(np.clip(float(S[1]), self.LowerPiezoRange, self.UpperPiezoRange))

        InList.insert(0, First)

        # Join them together
        for S in InList:
            InstructionLine = ';'.join(S)
            Instructions.append(InstructionLine)

        Instructions.append(self.InstructionEndString)

        sys.stdout.flush()
        for S in Instructions:
            sys.stdout.write(S + '\n')

        # freeze the main window so no new instructions can be sent
        # ModalDlg = QDialog(self)
        # ModalDlg.setWindowTitle('Executing instructions...')
        # ModalDlg.setModal(True)
        # ModalDlg.show()

        sys.stdout.flush()

        # ModalDlg.reject()

        return Instructions

def main():
    app = PyWidgets.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
