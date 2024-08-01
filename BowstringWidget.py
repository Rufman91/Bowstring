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
import tempfile
import shutil
import sys
import traceback
import logging
import os
import numpy as np
from calibration import load_images, phase_correlation, estimate_transformation, transform_coordinates, preprocess_image
import cv2
import matplotlib.pyplot as plt
import re

# Exception hook
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("Unhandled exception:", error_message)

    error_dialog = PyWidgets.QMessageBox()
    error_dialog.setIcon(PyWidgets.QMessageBox.Critical)
    error_dialog.setText("An unexpected error occurred:")
    error_dialog.setInformativeText(error_message)
    error_dialog.setWindowTitle("Error")
    error_dialog.exec_()

sys.excepthook = handle_exception

# Redirect stderr to capture error messages
class StreamToLogger:
    def __init__(self, logger, log_level):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

# Configure logging
log_file_path = "application.log"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[
                        logging.FileHandler(log_file_path),
                        logging.StreamHandler(sys.stdout)
                    ])

stderr_logger = logging.getLogger('STDERR')
sys.stderr = StreamToLogger(stderr_logger, logging.ERROR)

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
            # Rectangle = PyCore.QRect(Points[0], Points[1])
            painter.setPen(PyGui.QPen(PyCore.Qt.cyan, 4))
            painter.setRenderHint(PyGui.QPainter.Antialiasing)
            # painter.drawRect(Rectangle)
            painter.drawLine(FPoints[0], FPoints[1])
            painter.drawLine(FPoints[1], FPoints[2])
            painter.drawLine(FPoints[2], FPoints[3])
            painter.drawLine(FPoints[3], FPoints[0])
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
        self.info_log_path = os.path.expanduser("~")  # Default to user's home directory

        self.DebugMode = False

        if len(sys.argv) < 2:
            self.StartingTipPosition = [4.999999e-5, 4.999999e-5]
            self.ImageFullFile = os.path.join(self.ProgramPath, 'TestImage.jpg')
        else:
            self.StartingTipPosition = np.array([float(sys.argv[1]), float(sys.argv[2])])
            self.ImageFullFile = str(sys.argv[3])

        
        log_path_button = PyWidgets.QPushButton("Choose Info Log Path")
        log_path_button.clicked.connect(self.choose_log_path)

        self.log_path_label = PyWidgets.QLabel(f"Current path: {self.info_log_path}")

        # Set the window icon
        icon_path = os.path.join(self.ProgramPath, 'icons', 'Bow.jpg')
        self.setWindowIcon(PyGui.QIcon(icon_path))
        
        
        self.ImageFullFile = os.path.abspath(self.ImageFullFile)
        self.ImagePath = os.path.dirname(self.ImageFullFile)

        self.InstructionStartString = 'InstructionStart'
        self.InstructionEndString = 'InstructionEnd'

        self.UpperPiezoRange = 4.999999e-5
        self.LowerPiezoRange = -4.999999e-5

        # General settings
        self.PositioningVelocity = float(1e-5)
        self.RecordVideo = False
        self.RecordVideoNthFrame = 5
        self.RecordRealTimeScan = True
        
        # Coordiante Transformation Calibration
        
        self.PixelSize = float(4.65e-6)
        self.Magnification = float(10)
        self.holding_time_calibration = 0
        self.grid_size = 5
        self.calibration_matrix = None
        self.use_model_based_transformation = True
        self.calibration_phasecorr_shifts = []
        # Load the initial image as reference
        self.reference_image = load_images([self.ImageFullFile])[0]
        
        print(self.reference_image.dtype, self.reference_image.shape)
        
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
        
        # Model-based Transformation
        TitleModelBased = PyWidgets.QLabel('Model-based Transformation')
        TitleModelBased.setFont(PyGui.QFont('Arial', self.TitleFontSize - 2))

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

        self.TransformSwitch = PyWidgets.QCheckBox('Use Model-Based Transformation')
        self.TransformSwitch.setChecked(True)
        self.TransformSwitch.stateChanged.connect(self.switch_transformation)
        self.TransformSwitch.setEnabled(False)  # Disabled initially

        # PhaseCorr. Calibration
        TitleActualCalibration = PyWidgets.QLabel('PhaseCorr. Calibration')
        TitleActualCalibration.setFont(PyGui.QFont('Arial', self.TitleFontSize - 2))
        
        GridSizeLabel = PyWidgets.QLabel('Grid Size:')
        self.GridSizeEdit = PyWidgets.QLineEdit(str(self.grid_size))
        self.GridSizeEdit.setMaxLength(4)
        self.GridSizeEdit.setValidator(PyGui.QIntValidator())
        self.GridSizeEdit.textChanged.connect(self.set_grid_size)
        
        HoldingTimeLabel = PyWidgets.QLabel('Holding Time [s]:')
        self.HoldingTimeEdit = PyWidgets.QLineEdit(str(self.holding_time_calibration))
        self.HoldingTimeEdit.setMaxLength(self.MaxEditLength)
        self.HoldingTimeEdit.setValidator(PyGui.QDoubleValidator())
        self.HoldingTimeEdit.textChanged.connect(self.set_holding_time_calibration)

        self.CalibrateButton = PyWidgets.QPushButton('Start Calibration')
        self.CalibrateButton.clicked.connect(self.start_calibration)

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
        Grid.addWidget(log_path_button,5,4,1,2)
        Grid.addWidget(self.log_path_label,6,4,1,2)
        
        # Coordinate Transformation Calibration
        Grid.addWidget(TitleCalibration, 7, 4, 1, 2)

        # Model-based Transformation
        Grid.addWidget(TitleModelBased, 8, 4, 1, 2)
        Grid.addWidget(InputText3, 9, 4)
        Grid.addWidget(Input3, 9, 5)
        Grid.addWidget(InputText4, 10, 4)
        Grid.addWidget(Input4, 10, 5)
        Grid.addWidget(self.TransformSwitch, 11, 4, 1, 2)

        # PhaseCorr. Calibration
        Grid.addWidget(TitleActualCalibration, 12, 4, 1, 2)
        Grid.addWidget(GridSizeLabel, 13, 4)
        Grid.addWidget(self.GridSizeEdit, 13, 5)
        Grid.addWidget(HoldingTimeLabel, 14, 4)
        Grid.addWidget(self.HoldingTimeEdit, 14, 5)
        Grid.addWidget(self.CalibrateButton, 15, 4, 1, 2)

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

        Grid.addWidget(Title1, 0, 6, 1, 2)
        Grid.addWidget(InputText1, 1, 6)
        Grid.addWidget(Input1, 1, 7)
        Grid.addWidget(InputText2, 2, 6)
        Grid.addWidget(Input2, 2, 7)
        Grid.addWidget(InputText5, 3, 6)
        Grid.addWidget(Input5, 3, 7)
        Grid.addWidget(InputText6, 4, 6)
        Grid.addWidget(Input6, 4, 7)
        Grid.addWidget(self.StartPaHPCButton, 5, 6, 1, 2)
        Grid.addWidget(self.StartPaHButton, 6, 6, 1, 2)
        
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

        Grid.addWidget(Title2, 7, 6, 1, 2)
        Grid.addWidget(InputText11, 8, 6)
        Grid.addWidget(Input11, 8, 7)
        Grid.addWidget(InputText12, 9, 6)
        Grid.addWidget(Input12, 9, 7)
        Grid.addWidget(InputText13, 10, 6)
        Grid.addWidget(Input13, 10, 7)
        Grid.addWidget(InputText14, 11, 6)
        Grid.addWidget(Input14, 11, 7)
        Grid.addWidget(InputText15, 12, 6)
        Grid.addWidget(Input15, 12, 7)
        Grid.addWidget(InputText16, 13, 6)
        Grid.addWidget(Input16, 13, 7)
        Grid.addWidget(Input17, 14, 6, 1, 2)
        Grid.addWidget(self.StartSOButton, 15, 6, 1, 2)

        self.Widget = PyWidgets.QWidget()
        self.Widget.setLayout(Grid)

        self.setCentralWidget(self.Widget)
        
        # Screen Size Calculation
        screen = PyWidgets.QDesktopWidget().screenGeometry()
        screenWidth = screen.width()
        screenHeight = screen.height()

        # Set window size to 80% of the screen size
        self.setGeometry(100, 100, int(screenWidth * 0.8), int(screenHeight * 0.8))

        # Set the minimum size if necessary (could be smaller)
        self.setMinimumSize(int(screenWidth * 0.5), int(screenHeight * 0.5))
        
        self.setAcceptDrops(True)
        self.setWindowTitle('Bowstring')
        # self.setGeometry(200, 200, 300, 600)
        self.show()
        
    def choose_log_path(self):
        # Open a dialog to select the folder for saving log files
        directory = PyWidgets.QFileDialog.getExistingDirectory(self, "Select Log Directory", self.info_log_path)
        if directory:
            self.info_log_path = directory
            self.log_path_label.setText(f"Current path: {self.info_log_path}")


    def start_calibration(self):
        if self.DebugMode:
            self.start_calibration_debug()
        else:
            self.start_calibration_standard()

########## DEBUG CODE #############

    def visualize_images(self, image1, image2):
        import matplotlib.pyplot as plt
        
        image1 = preprocess_image(image1)
        image2 = preprocess_image(image2)
        
        fig, axs = plt.subplots(1, 2, figsize=(10, 5))
        axs[0].imshow(cv2.cvtColor(image1, cv2.COLOR_BGR2RGB))
        axs[0].set_title("Reference Image")
        axs[0].axis('off')
        
        axs[1].imshow(cv2.cvtColor(image2, cv2.COLOR_BGR2RGB))
        axs[1].set_title("Target Image")
        axs[1].axis('off')
        
        plt.tight_layout()
        plt.show()
    
    def visualize_shift(self, image1, image2, shift):
        import matplotlib.pyplot as plt
    
        # image1 = preprocess_image(image1)
        # image2 = preprocess_image(image2)
        
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(cv2.cvtColor(image1, cv2.COLOR_BGR2RGB))
        ax.set_title(f"Shift: {shift}")
        ax.axis('off')
    
        # Overlay the second image with the shift applied
        shifted_image2 = np.roll(image2, shift.astype(int), axis=(0, 1))
        ax.imshow(cv2.cvtColor(shifted_image2, cv2.COLOR_BGR2RGB), alpha=0.5)
        
        plt.tight_layout()
        plt.show()
    
    def visualize_frequency_domain(self, image1, image2):
        import matplotlib.pyplot as plt
        
        # Preprocess images toer):
        print(f"Debug folder does not  isolate the cantilever")
        image1_preprocessed = preprocess_image(image1)
        image2_preprocessed = preprocess_image(image2)
        
        # Since preprocess_image already returns grayscale images, no need for additional conversion
        image1_gray = image1_preprocessed
        image2_gray = image2_preprocessed
        
        fig, axs = plt.subplots(1, 2, figsize=(10, 5))
        axs[0].imshow(np.log(np.abs(image1_gray) + 1), cmap='gray')
        axs[0].set_title("Reference Image Frequency Domain")
        axs[0].axis('off')
    
        axs[1].imshow(np.log(np.abs(image2_gray) + 1), cmap='gray')
        axs[1].set_title("Target Image Frequency Domain")
        axs[1].axis('off')
    
        plt.tight_layout()
        plt.show()
        
    def visualize_correlation_image(self, image1, image2):


        # Preprocess images to isolate the cantilever
        image1_preprocessed = preprocess_image(image1)
        image2_preprocessed = preprocess_image(image2)
    
        # Since preprocess_image already returns grayscale images, no need for additional conversion
        image1_gray = image1_preprocessed
        image2_gray = image2_preprocessed

        f_image1 = np.fft.fft2(image1_gray)
        f_image2 = np.fft.fft2(image2_gray)

        cross_power_spectrum = (f_image1 * np.conj(f_image2)) / np.abs(f_image1 * np.conj(f_image2))
        correlation_image = np.fft.ifft2(cross_power_spectrum)
        correlation_image = np.fft.fftshift(correlation_image)

        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(np.log(np.abs(correlation_image)), cmap='gray')
        ax.set_title("Phase Correlation Image")
        ax.axis('off')

        plt.tight_layout()
        plt.show()
    
    def visualize_phase_correlation(self,image1, image2):
        image1_preprocessed = preprocess_image(image1)
        image2_preprocessed = preprocess_image(image2)
        
        image1_gray = image1_preprocessed
        image2_gray = image2_preprocessed
    
        # Compute the phase correlation
        shift, response = cv2.phaseCorrelate(np.float32(image1_gray), np.float32(image2_gray))
        
        # Compute the cross power spectrum and its inverse for visualization
        dft1 = cv2.dft(np.float32(image1_gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft2 = cv2.dft(np.float32(image2_gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        
        conj_b = np.conj(dft2)
        dft_product = dft1 * conj_b
        cross_power_spectrum = dft_product / np.abs(dft_product)
        
        phase_correlation_image = cv2.idft(cross_power_spectrum, flags=cv2.DFT_SCALE | cv2.DFT_REAL_OUTPUT)
        phase_correlation_image = np.fft.fftshift(phase_correlation_image)
    
        plt.figure(figsize=(10, 5))
    
        plt.subplot(1, 2, 1)
        plt.imshow(image1_gray, cmap='gray')
        plt.title('Reference Image')
    
        plt.subplot(1, 2, 2)
        plt.imshow(image2_gray, cmap='gray')
        plt.title('Target Image')
    
        plt.figure(figsize=(6, 6))
        plt.imshow(phase_correlation_image, cmap='gray')
        plt.title(f'Phase Correlation Image\nShift: {shift}')
        plt.show()


    def plot_phase_correlation_results(self, reference_image, shifts, grid_size):
        fig, axs = plt.subplots(grid_size, grid_size, figsize=(10, 10))
        axs[0, 0].imshow(cv2.cvtColor(reference_image, cv2.COLOR_BGR2RGB))
        axs[0, 0].set_title("Reference Image")
        axs[0, 0].axis('off')

        for i, shift in enumerate(shifts, 1):
            x_idx = i % grid_size
            y_idx = i // grid_size
            axs[y_idx, x_idx].imshow(cv2.cvtColor(reference_image, cv2.COLOR_BGR2RGB))
            axs[y_idx, x_idx].set_title(f"Shift: {shift}")
            axs[y_idx, x_idx].axis('off')
        plt.tight_layout()
        plt.show()

    def plot_transformed_grid(self, reference_image, transformation_matrix, x_positions, y_positions):
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(cv2.cvtColor(reference_image, cv2.COLOR_BGR2RGB))
        for x in x_positions:
            for y in y_positions:
                transformed_point = transform_coordinates((x, y), transformation_matrix)
                ax.plot(transformed_point[0], transformed_point[1], 'ro')
        plt.show()


    def start_calibration_debug(self):
        import matplotlib.pyplot as plt
    
        # Load the initial image as reference
        self.reference_image = cv2.imread(self.ImageFullFile, cv2.IMREAD_COLOR)
        # Fixed input values for debugging
        grid_size = 5
        holding_time = 1.0  # seconds
        positioning_velocity = self.PositioningVelocity
    
        # Define movement boundaries (for visual representation)
        lower_bound = self.LowerPiezoRange
        upper_bound = self.UpperPiezoRange
    
        # Calculate grid points
        x_positions = np.linspace(lower_bound, upper_bound, grid_size)
        y_positions = np.linspace(lower_bound, upper_bound, grid_size)
    
        # Fixed folder path for debugging
        debug_folder = "/home/manuel/RawData/2024_05_16_BowstringCoordCalibTestdataset/tmpjefj5cif"
        if not os.path.exists(debug_folder):
            print(f"Debug folder does not exist: {debug_folder}")
            return
    
        # Assume a fixed number of images in the folder
        expected_num_images = grid_size * grid_size
        image_paths = [os.path.join(debug_folder, f"calibration_image_{i}.jpg") for i in range(expected_num_images)]
        if len(image_paths) != expected_num_images:
            print(f"Expected {expected_num_images} images, but found {len(image_paths)}")
            return
        
        images = load_images(image_paths)
        if any(img is None for img in images):
            print("One or more images could not be loaded.")
            return
    
        fig, axs = plt.subplots(grid_size, grid_size, figsize=(10, 10))
        for i, ax in enumerate(axs.flatten()):
            x_idx = i % grid_size
            y_idx = i // grid_size
            ax.imshow(cv2.cvtColor(images[i], cv2.COLOR_BGR2RGB))
            ax.set_title(f"({x_positions[x_idx]:.2e}, {y_positions[y_idx]:.2e})")
            ax.axis('off')
        plt.tight_layout()
        plt.show()
    
        self.afm_positions = [(x, y) for x in x_positions for y in y_positions]
        self.images = images
    
        # Perform phase correlation and visualize results
        shifts = []
        transshifts = []
        for i in range(len(images)):
            self.visualize_images(self.reference_image, images[i])
            shift = phase_correlation(self.reference_image, images[i])
            shifts.append(shift)
            transshifts.append((shift[0] + self.Points[2][0] , shift[1] + self.Points[2][1]))
            print(f"Shift for image {i}: {shift}")
            self.visualize_shift(self.reference_image, images[i], np.array(shift))
            self.visualize_frequency_domain(self.reference_image, images[i])
            self.visualize_correlation_image(self.reference_image, images[i])
            self.visualize_phase_correlation(self.reference_image, images[i])
            
        self.calibration_phasecorr_shifts = shifts
        # Plot phase correlation results
        # self.plot_phase_correlation_results(self.reference_image, shifts, grid_size)
    
    
        # Plot transformed grid
        # self.plot_transformed_grid(self.reference_image, self.calibration_matrix, x_positions, y_positions)
    
        self.use_model_based_transformation = False
        
        # Estimate transformation matrix
        self.recalculate_transformation_matrix()
        print("Estimated transformation matrix:", self.calibration_matrix)
        
        self.TransformSwitch.setChecked(False)
        self.TransformSwitch.setEnabled(True)
        
        self.draw_geometry()
        self.initialize_scratch_off_points()
    
        print("Debug: Calibration process completed successfully.")

###################################

    def start_calibration_standard(self):
        # Retrieve input values
        grid_size = self.grid_size
        holding_time = self.holding_time_calibration
        positioning_velocity = self.PositioningVelocity
    
        # Define movement boundaries
        lower_bound = self.LowerPiezoRange
        upper_bound = self.UpperPiezoRange
    
        # Calculate grid points
        x_positions = np.linspace(lower_bound, upper_bound, grid_size)
        y_positions = np.linspace(lower_bound, upper_bound, grid_size)
    
        temp_dir = tempfile.mkdtemp()
        self.calibration_temp_dir = temp_dir
    
        # Compile instruction list
        instruction_list = [['Calibration', str(False), str(False), str(self.RecordVideoNthFrame), temp_dir]]
        afm_positions = []
        for x in x_positions:
            for y in y_positions:
                afm_positions.append([x, y])
                instruction_list.append([
                    str(x), str(y), str(positioning_velocity), str(holding_time), 'Retracted'
                ])
    
        # Store afm_positions for later use
        self.afm_positions = afm_positions
    
        # Send instruction list to the second script
        self.construct_and_send_instructions(instruction_list)
    
        # Wait for the required number of images
        required_images = grid_size * grid_size
        self.wait_for_images(temp_dir, required_images)
    
    def wait_for_images(self, folder, num_images):
        print(folder)
        while True:
            files = os.listdir(folder)
            if len(files) >= num_images:
                break
            time.sleep(1)  # Check every second
    
        # Proceed with the next steps after all images are present
        self.process_calibration_images(folder)

    
    def process_calibration_images(self, folder):
        # Load images and associate them with AFM positions
        image_paths = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.startswith("calibration_image_")]
        
        logging.debug(f"Expected number of images: {self.grid_size**2}")
        logging.debug(f"Found {len(image_paths)} images in the folder.")
        
        # Sort image paths numerically
        image_paths = sorted(image_paths, key=self.numerical_sort)
        
        images = load_images(image_paths)
        
        print(image_paths)
        
        if len(images) != self.grid_size**2:
            logging.error(f"Number of images loaded ({len(images)}) does not match the expected number ({self.grid_size**2}).")
            return
        
        if not images:
            logging.error("No images were loaded successfully. Aborting calibration.")
            return
        
        # Perform phase correlation
        shifts = []
        for i in range(len(images)):
            shift = phase_correlation(self.reference_image, images[i])
            shifts.append(shift)
        
        self.calibration_phasecorr_shifts = shifts
        self.use_model_based_transformation = False
        
        # Estimate transformation matrix
        self.recalculate_transformation_matrix()
        self.TransformSwitch.setChecked(False)
        self.TransformSwitch.setEnabled(True)
        
        self.draw_geometry()
        self.initialize_scratch_off_points()
        
        # Clean up temporary folder
        shutil.rmtree(folder)




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

    def recalculate_transformation_matrix(self):
        if len(self.Points) < 3 or self.use_model_based_transformation:
            return  # Not enough points to calculate the transformation matrix

        # Use saved shifts and AFM positions to recalculate transformation matrix
        transshifts = [(shift[0] + self.Points[2][0], shift[1] + self.Points[2][1]) for shift in self.calibration_phasecorr_shifts]
        self.calibration_matrix = estimate_transformation(transshifts, self.afm_positions)
        # print("Recalculated transformation matrix:", self.calibration_matrix)

    def getPos(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.Points.append([x, y])
        if self.PointCounter == 3:
            self.PointCounter = -1
            self.Points = list()
        self.PointCounter += 1
        self.ImageDescription.setText(self.ImageDescriptionPrompts[self.PointCounter])
        self.recalculate_transformation_matrix()  # Recalculate transformation matrix
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
        
    def set_grid_size(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.grid_size = int(s)  # Store the grid size
        self.draw_geometry()
        self.initialize_scratch_off_points()

    def set_holding_time_calibration(self, s):
        if not s:
            return
        s = s.replace(',', '.')
        self.holding_time_calibration = float(s)  # Store the holding time for calibration
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
        self.shifts = []  # Initialize shifts property
        self.reference_image = None  # Initialize reference image property
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
        
        self.draw_geometry()
        self.initialize_scratch_off_points()        
        

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

        return OutPoint[0:2]

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
            InvMat = np.linalg.inv(np.array([self.calibration_matrix[0],
                                             self.calibration_matrix[1],[0, 0, 1]]))
            # print(InvMat)
            OutPoint = transform_coordinates(InPoint, InvMat)
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

        TopLeft = self.transform_coordinates_rl2image([self.LowerPiezoRange, self.UpperPiezoRange])
        TopRight = self.transform_coordinates_rl2image([self.UpperPiezoRange, self.UpperPiezoRange])
        BottomRight = self.transform_coordinates_rl2image([self.UpperPiezoRange, self.LowerPiezoRange])
        BottomLeft = self.transform_coordinates_rl2image([self.LowerPiezoRange, self.LowerPiezoRange])
        InPoints1 = [TopLeft, TopRight,  BottomRight, BottomLeft]
        # print(InPoints1)
        # print(f"Window size: {np.linalg.norm(TopLeft - BottomLeft)}")
        self.Pixmap.paintEvent(InPoints1, 'Accessible Area')
        InPoints2 = [
            self.transform_coordinates_rl2image(self.Anchor1),
            self.transform_coordinates_rl2image(self.Anchor2),
            self.transform_coordinates_rl2image(self.rl2im_im2rl(self.PaHFinalStrainPoint)),
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
        self.log_pull_and_hold_info()
        
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
    
    def im2rl_rl2im(self,InPoint):
        OutPoint = self.transform_coordinates_image2rl(InPoint)
        return self.transform_coordinates_rl2image(OutPoint)
    
    def rl2im_im2rl(self,InPoint):
        OutPoint = self.transform_coordinates_rl2image(InPoint)
        return self.transform_coordinates_image2rl(OutPoint)
    
    def log_pull_and_hold_info(self):
        # Prepare log content
        log_content = []
        log_content.append("Coordinate Transformation Matrix:")
        if self.calibration_matrix is not None:
            log_content.append(str(self.calibration_matrix))
        else:
            log_content.append("Not available")
    
        log_content.append("\nSettings:")
        log_content.append(f"Positioning Velocity: {self.PositioningVelocity}")
        log_content.append(f"Record Real Time Scan: {self.RecordRealTimeScan}")
        log_content.append(f"Record Video: {self.RecordVideo}")
        log_content.append(f"Record Video Nth Frame: {self.RecordVideoNthFrame}")
        log_content.append(f"Pixel Size: {self.PixelSize}")
        log_content.append(f"Magnification: {self.Magnification}")
        log_content.append(f"Holding Time Calibration: {self.holding_time_calibration}")
        log_content.append(f"Grid Size: {self.grid_size}")
        log_content.append(f"Strain Rate: {self.PaHStrainRate}")
        log_content.append(f"Final Strain: {self.PaHFinalStrain}")
        log_content.append(f"Tip-to-Halfpoint Buffer: {self.PaHTip2HalfPointBuffer}")
        log_content.append(f"Holding Time: {self.PaHHoldingTime}")
    
        log_content.append("\nDistances (real world):")
        log_content.append(f"Anchor 1 to Anchor 2: {np.linalg.norm(self.Anchor1 - self.Anchor2)}")
        log_content.append(f"Anchor to Final Strain Point: {np.linalg.norm(self.Anchor1 - self.PaHFinalStrainPoint)}")
        log_content.append(f"Mid Point to Final Strain Point: {np.linalg.norm(self.HalfPoint - self.PaHFinalStrainPoint)}")
    
        log_content.append("\nDistances (pixel world):")
        anchor1_pixel = np.array(self.Points[0])
        anchor2_pixel = np.array(self.Points[1])
        final_strain_pixel = np.array(self.transform_coordinates_rl2image(self.PaHFinalStrainPoint))
        mid_point_pixel = np.array(self.transform_coordinates_rl2image(self.HalfPoint))
    
        log_content.append(f"Anchor 1 to Anchor 2: {np.linalg.norm(anchor1_pixel - anchor2_pixel)}")
        log_content.append(f"Anchor to Final Strain Point: {np.linalg.norm(anchor1_pixel - final_strain_pixel)}")
        log_content.append(f"Mid Point to Final Strain Point: {np.linalg.norm(mid_point_pixel - final_strain_pixel)}")
        
        log_content.append("\nAbsolute positions (real world):")
        log_content.append(f"Anchor 1: {self.Anchor1}")
        log_content.append(f"Anchor 2: {self.Anchor2}")
        log_content.append(f"Half Point: {self.HalfPoint}")
        log_content.append(f"Buffer Point: {self.PaHBufferPoint}")
        log_content.append(f"Final Strain Point: {self.PaHFinalStrainPoint}")
        
        log_content.append("\nAbsolute positions (pixel world):")
        log_content.append(f"Anchor 1: {self.Points[0]}")
        log_content.append(f"Anchor 2: {self.Points[1]}")
        log_content.append(f"Half Point: {self.transform_coordinates_rl2image(self.HalfPoint)}")
        log_content.append(f"Buffer Point: {self.transform_coordinates_rl2image(self.PaHBufferPoint)}")
        log_content.append(f"Final Strain Point: {self.transform_coordinates_rl2image(self.PaHFinalStrainPoint)}")

    
        # Write log to file
        log_file_name = os.path.join(self.info_log_path, f"PullAndHold_Log_{time.strftime('%Y%m%d-%H%M%S')}.txt")
        with open(log_file_name, 'w') as log_file:
            log_file.write("\n".join(log_content))
        
        logging.info(f"Pull and Hold experiment info logged to {log_file_name}")

    
    def numerical_sort(self,value):
        numbers = re.findall(r'\d+', value)
        if numbers:
            return int(numbers[-1])
        return 0

def main():
    app = PyWidgets.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
