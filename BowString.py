# Python code for ExperimentPlanner
# JPK Script
checkVersion('SPM', 6, 1, 158)

# JPK Script

from com.jpk.inst.lib import JPKScript
from com.jpk.util import XYPosition
from com.jpk.util.jyswingutils import callSwing
import httplib
import os
import time
import subprocess
import shlex
import psutil


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


def execute_instruction_list(Points,TTLInstance,Mode,RecordRealTimeScan,RecordVideo,RecordVideoNthFrame):
    
    #take the image that is then sent to the widget
    #TODO
    # make sure piezo is retracted and get current position
    Scanner.retractPiezo()
    PiezoEngaged = False
    #CurPos = ScannerInstance.getCurrentPosition().get_translated(0,0)
    
    if RecordRealTimeScan:
        RealTimeScan.setFilenameRoot(Mode)
        RealTimeScan.setAutosave(True)
        RealTimeScan.startScanning()
    if RecordVideo:
        Snapshooter.startImageSequenceSaving('jpg', RecordVideoNthFrame, Mode)
        
    # Go though the points with Speed and print the points name
    # each time the position is reached. Then wait for WaitTime
    # and move on to next point. At each point also trigger a 
    # TTL pulse. If the point is out of the scan range of the 
    # X-Y-Scanner inform the user and move on to the next point.
    
    for P in Points:
        if P[3]=='Approached' and not PiezoEngaged:
            Scanner.approach()
            PiezoEngaged = True
        elif P[3]=='Retracted' and PiezoEngaged:
            Scanner.retractPiezo()
            PiezoEngaged = False
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(P[0],P[1],P[2])
        if P[3]>0:
            time.sleep(P[3])
    
    # Stop recordings
    if RecordRealTimeScan:
        RealTimeScan.stopScanning()
    if RecordVideo:
        Snapshooter.stopImageSequenceSaving()
    

def parse_and_execute_instructions(InList,TTLInstance):
    
    SplitList = []
    for S in InList:
        SplitList.append(S.split(';'))
    
    print(InList)
    print(SplitList)
    
    StartStringCounter = 0
    EndStringCounter = 0
    for S in SplitList:
        if S[0]=='InstructionStart':
            StartStringCounter += 1
        elif S[0]=='InstructionEnd':
            EndStringCounter +=1
    if not (StartStringCounter==1 and EndStringCounter==1):
            print('Error: Instructions are faulty!')
            return
    SplitList.pop(0)
    SplitList.pop(-1)
    ModeSettings = SplitList.pop(0)
    print(ModeSettings)
    Mode = ModeSettings[0]
    RecordRealTimeScan = bool(ModeSettings[1])
    RecordVideo = bool(ModeSettings[2])
    RecordVideoNthFrame = int(ModeSettings[3])
    
    Points = []
    for S in SplitList:
        P = [float(S[0]) , float(S[1]) , float(S[2]) , float(S[3]) , S[4]]
        Points.append(P)
    
    if Mode=='PullAndHold':
        execute_instruction_list(Points,TTLInstance,Mode,RecordRealTimeScan,RecordVideo,RecordVideoNthFrame)
    elif Mode=='PullAndHoldPositionCheck':
        execute_instruction_list(Points,TTLInstance,Mode,RecordRealTimeScan,RecordVideo,RecordVideoNthFrame)
    else:
        print('%s is not an available Bowstring-mode' % Mode)
    return

#################### Execution #############################

# Set the scanner
xyScanner = CurrentXYScannerControl()
print(xyScanner.getCurrentPosition())
#quit('Just need current position')
#xyScanner.moveToXYPosition(0,0)

# set TTLOutput pulse for later segmentation
output = TTLOutput.outputs['Pin 4']
output.style = 'PULSE'
output.pulse_time = 0.05

FullCommand = """python BowstringWidget.py 1e-6 1.4e-6 "BSFibril-14.tif"
"""

SplitCommand = shlex.split(FullCommand)

#p = subprocess.Popen(FullCommand, shell=True, stdout = subprocess.PIPE, encoding='UTF-8')
#p = subprocess.Popen(SplitCommand, shell=False,bufsize=0, stdout  subprocess.PIPE, encoding='UTF-8')

cmd = SplitCommand


with subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1,universal_newlines=True) as p:
    Instructions=['Waiting']
    psProcess = psutil.Process(pid=p.pid)
    for line in p.stdout:
        if line=='InstructionStart\n':
            Instructions = ['InstructionStart']
        elif line=='InstructionEnd\n' and Instructions[0]=='InstructionStart':
            Instructions.append(line[0:-1])
            # psProcess.suspend()
            BlockNewInstructions = True
            parse_and_execute_instructions(Instructions)
            # psProcess.resume()
            Instructions = ['Waiting']
        elif Instructions[0]=='Waiting':
            print('Waiting...')
            continue
        else:
            Instructions.append(line[0:-1])
        # print(Instructions)
        # print(line)

# run the desired program here

print('Program ended successfully')
