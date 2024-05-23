# Python code for ExperimentPlanner
# JPK Script
checkVersion('SPM', 6, 1, 158)

# JPK Script

from com.jpk.inst.lib import JPKScript
from com.jpk.util import XYPosition
from com.jpk.util.jyswingutils import callSwing
from datetime import datetime
import httplib
import os
import time
import subprocess
import shlex


class CurrentXYScannerControl:
    class PositionOutOfRangeException(Exception):
        pass
    def __currentScannerInfo(self):
        return JPKScript.getInstrument().getCurrentXYScannerInfo()
    def __currentController(self):
        return self.__currentScannerInfo().getController()
    def __getMovingTime(self, newXYPosition, velocity):
        currentPosition = self.getCurrentPosition()
        distance = currentPosition.getDistance(newXYPosition)
        return distance / velocity
    def __moveToXYPosition(self, xyPosition, time):
        callSwing(self.__currentController().moveTo, xyPosition, time)
    def __checkIfPositionInRange(self, position):
        if self.isPositionContainedInScanRange(position):
            return
        else:
            raise CurrentXYScannerControl.PositionOutOfRangeException(
                     "The new position is outside of the scan range!")
    def getMaxScanRectangle(self):
        support = self.__currentScannerInfo().getScanRangeSupport()
        return support.getValue().getBounds()
    def moveToXYPosition(self, x, y, velocity = 20e-6):
        newPosition = XYPosition(x, y)
        movingTime = self.__getMovingTime(newPosition, velocity)
        self.__checkIfPositionInRange(newPosition)
        self.__moveToXYPosition(newPosition, movingTime)
    def moveRelative(self, deltaX, deltaY, velocity = 20e-6):
        currentPosition = self.getCurrentPosition()
        newPosition = currentPosition.getTranslated(deltaX, deltaY)
        movingTime = self.__getMovingTime(newPosition, velocity)
        self.__checkIfPositionInRange(newPosition)
        self.__moveToXYPosition(newPosition, movingTime)
    def getCurrentPosition(self):
        return self.__currentController().getPosition()
    def isPositionContainedInScanRange(self, x, y = None):
        if not y:
            if not isinstance(x, XYPosition):
                raise AttributeError()
            else:
                return self.getMaxScanRectangle().contains(x.x, x.y)
        else:
            return self.getMaxScanRectangle().contains(x, y)


def execute_instruction_list(Points,TTLInstance,Mode,
RecordRealTimeScan,RecordVideo,RecordVideoNthFrame,TargetDir,RootName):
    
    #take the image that is then sent to the widget
    #TODO
    # make sure piezo is retracted and get current position
    Scanner.retractPiezo()
    PiezoEngaged = False
    #CurPos = ScannerInstance.getCurrentPosition().get_translated(0,0)
    
    if RecordRealTimeScan:
        RealTimeScan.setOutputDirectory(TargetDir)
        RealTimeScan.setFilenameRoot(Mode + '_' + RootName)
        RealTimeScan.setAutosave(True)
        RealTimeScan.startScanning()
    if RecordVideo:
        Now = datetime.now().isoformat().replace('.','-').replace(':','-')
        Snapshooter.startImageSequenceSaving('jpg',
        RecordVideoNthFrame, os.path.join(TargetDir,Mode + '_' + RootName + '_' + Now,Mode + '_' + RootName + '_' + Now))
        
    # Go though the points with Speed and print the points name
    # each time the position is reached. Then wait for WaitTime
    # and move on to next point. At each point also trigger a 
    # TTL pulse. If the point is out of the scan range of the 
    # X-Y-Scanner inform the user and move on to the next point.
    
    for P in Points:
        if P[4]=='Approached' and not PiezoEngaged:
            print('Approaching...')
            Scanner.approach()
            PiezoEngaged = True
        elif P[4]=='Retracted' and PiezoEngaged:
            print('Retracting...')
            Scanner.retractPiezo()
            PiezoEngaged = False
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(P[0],P[1],P[2])
        if P[3]>0:
            time.sleep(P[3])
    
    # Stop recordings
    if RecordRealTimeScan:
        RealTimeScan.stopScanning()
        RealTimeScan.setAutosave(False)
        RealTimeScan.startScanning()
    if RecordVideo:
        Snapshooter.stopImageSequenceSaving()

    print('\nProcess complete. Waiting for new instructions...\n')
    

def execute_calibration(Points, TTLInstance, RecordRealTimeScan, RecordVideo, RecordVideoNthFrame, TempDir, RootName):
    # make sure piezo is retracted and get current position
    Scanner.retractPiezo()
    PiezoEngaged = False

    if not os.path.exists(TempDir):
        os.makedirs(TempDir)

    for idx, P in enumerate(Points):
        if P[4] == 'Approached' and not PiezoEngaged:
            print('Approaching...')
            Scanner.approach()
            PiezoEngaged = True
        elif P[4] == 'Retracted' and PiezoEngaged:
            print('Retracting...')
            Scanner.retractPiezo()
            PiezoEngaged = False
        xyScanner.moveToXYPosition(P[0], P[1], P[2])
        if P[3] > 0:
            time.sleep(P[3])
        # Capture and save image
        image_filename = os.path.join(TempDir, "calibration_image_" + str(idx) + ".jpg")
        Snapshooter.saveOpticalSnapshot(image_filename)

    print('\nCalibration complete. Waiting for new instructions...\n')


def parse_and_execute_instructions(InList, TTLInstance, TargetDir, RootName):
    SplitList = []
    for S in InList:
        SplitList.append(S.split(';'))
    
    StartStringCounter = 0
    EndStringCounter = 0
    for S in SplitList:
        if S[0] == 'InstructionStart':
            StartStringCounter += 1
        elif S[0] == 'InstructionEnd':
            EndStringCounter += 1
    if not (StartStringCounter == 1 and EndStringCounter == 1):
        print('Error: Instructions are faulty!')
        return
    SplitList.pop(0)
    SplitList.pop(-1)
    ModeSettings = SplitList.pop(0)
    print(ModeSettings)
    Mode = ModeSettings[0]
    if ModeSettings[1] == 'True':
        RecordRealTimeScan = True
    elif ModeSettings[1] == 'False':
        RecordRealTimeScan = False
    else:
        print('Error: Instructions are faulty!')
        return
    if ModeSettings[2] == 'True':
        RecordVideo = True
    elif ModeSettings[2] == 'False':
        RecordVideo = False
    else:
        print('Error: Instructions are faulty!')
        return
    RecordVideoNthFrame = int(ModeSettings[3])
    TempDir = ModeSettings[4] if Mode == 'Calibration' else None

    Points = []
    for S in SplitList:
        P = [float(S[0]), float(S[1]), float(S[2]), float(S[3]), S[4]]
        Points.append(P)

    if Mode == 'PullAndHold':
        execute_instruction_list(Points, TTLInstance, Mode,
                                 RecordRealTimeScan, RecordVideo, RecordVideoNthFrame, TargetDir, RootName)
    elif Mode == 'PullAndHoldPositionCheck':
        execute_instruction_list(Points, TTLInstance, Mode,
                                 RecordRealTimeScan, RecordVideo, RecordVideoNthFrame, TargetDir, RootName)
    elif Mode == 'Calibration':
        execute_calibration(Points, TTLInstance,
                            RecordRealTimeScan, RecordVideo, RecordVideoNthFrame, TempDir, RootName)
    elif Mode == 'Scratch Off':
        execute_instruction_list(Points, TTLInstance, Mode,
                                 RecordRealTimeScan, RecordVideo, RecordVideoNthFrame, TargetDir, RootName)
    else:
        print('%s is not an available Bowstring-mode' % Mode)
    return



#######################################################################
############################### Execution #############################
#######################################################################


# DEAR USER: First, set target directory and file name root
# Then just press 'Run' up above in the Experiment Planner
TargetDir = "/home/jpkuser/jpkdata/Jaritz_Simon_AFM/2022_09_23-BowstringStretching/"
RootName = "Image2Piezo-PrecisionTest"

# DEAR USER: If desired, reposition the AFM tip e.g. to the top left (x=-4.9e-5,y=4.9e-5)
# before starting the experiment# Set the scanner
xyScanner = CurrentXYScannerControl()
print(xyScanner.getCurrentPosition())
#xyScanner.moveToXYPosition(0,0)
RepositionFirst = True
if RepositionFirst:
    Scanner.retractPiezo()
    xyScanner.moveToXYPosition(4.9e-5,4.9e-5)
    print(xyScanner.getCurrentPosition())

# set TTLOutput pulse for later segmentation
output = TTLOutput.outputs['Pin 4']
output.style = 'PULSE'
output.pulse_time = 0.01

CurPos = xyScanner.getCurrentPosition()
CurX = CurPos.getX()
CurY = CurPos.getY()

Scanner.approach()
DT = datetime.now().isoformat().replace('.','-').replace(':','-')
ImagePath = os.path.join(TargetDir,RootName + '_InImage_' + DT)
Snapshooter.saveOpticalSnapshot(ImagePath)
Scanner.retractPiezo()

FullCommand = """./jpkdata/Jaritz_Simon_AFM/BowstringApp/dist/BowstringWidget/BowstringWidget
%e %e "%s"
""" % (CurX,CurY,ImagePath)

SplitCommand = shlex.split(FullCommand)

#p = subprocess.Popen(FullCommand, shell=True, stdout = subprocess.PIPE, encoding='UTF-8')
#p = subprocess.Popen(SplitCommand, shell=False,bufsize=0, stdout  subprocess.PIPE, encoding='UTF-8')

cmd = SplitCommand


p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1,universal_newlines=True)
Instructions=['Waiting']
for line in p.stdout:
    # Print out all lines to the console
    print(line) # DEBUG: disable when deploying
    
    if line=='InstructionStart\n':
        Instructions = ['InstructionStart']
    elif line=='InstructionEnd\n' and Instructions[0]=='InstructionStart':
        Instructions.append(line[0:-1])
        BlockNewInstructions = True
        parse_and_execute_instructions(Instructions,output,TargetDir,RootName)
        Instructions = ['Waiting']
    elif Instructions[0]=='Waiting':
        print('Waiting...')
        continue
    else:
        Instructions.append(line[0:-1])


print('Program ended successfully')
