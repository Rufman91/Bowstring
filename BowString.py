# Python code for ExperimentPlanner
# JPK Script
checkVersion('SPM', 6, 1, 158)

# JPK Script

from com.jpk.inst.lib import JPKScript
from com.jpk.util import XYPosition
from com.jpk.util.jyswingutils import callSwing
import httplib


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

def hover_over_all_key_points(ScannerInstance,TTLInstance,
A1X,A1Y,A2X,A2Y,ITX,ITY,HPX,HPY,BPX,BPY,FPX,FPY,
Speed = 10e-6,WaitTime = 2,RecordRealTime = True,
RecordVideo = False,NthKeyFrame = 2):
    
    # make sure piezo is retracted and get current position
    Scanner.retractPiezo()
    #CurPos = ScannerInstance.getCurrentPosition().get_translated(0,0)

    if RecordRealTime:
        RealTimeScan.setFilenameRoot('Key-Point-Hoover')
        RealTimeScan.setAutosave(True)
        RealTimeScan.startScanning()
    if RecordVideo:
        Snapshooter.startImageSequenceSaving('jpg', NthKeyFrame, 'Key-Point-Hoover')
        
    # Go though the points with Speed and print the points name
    # each time the position is reached. Then wait for WaitTime
    # and move on to next point. At each point also trigger a 
    # TTL pulse. If the point is out of the scan range of the 
    # X-Y-Scanner inform the user and move on to the next point.
    
    # Initial Tip Position
    if abs(ITX) >= 5e-5 or abs(ITY) >= 5e-5:
        print('Initial Tip Position exceeds scanner range. Skipping to next point')
    else:
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(ITX,ITY,Speed)
        print('Initial Tip Position')
        time.sleep(WaitTime)
    # Anchor 1
    if abs(A1X) >= 5e-5 or abs(A1Y) >= 5e-5:
        print('Anchor 1 Position exceeds scanner range. Skipping to next point')
    else:
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(A1X,A1Y,Speed)
        print('Anchor 1')
        time.sleep(WaitTime)
    # Anchor 2
    if abs(A2X) >= 5e-5 or abs(A2Y) >= 5e-5:
        print('Anchor 2 Position exceeds scanner range. Skipping to next point')
    else:
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(A2X,A2Y,Speed)
        print('Anchor 2')
        time.sleep(WaitTime)
    # Buffer Position
    if abs(BPX) >= 5e-5 or abs(BPY) >= 5e-5:
        print('Buffer Position exceeds scanner range. Skipping to next point')
    else:
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(BPX,BPY,Speed)
        print('Buffer Position')
        time.sleep(WaitTime)
    # Segment Half Point
    if abs(HPX) >= 5e-5 or abs(HPY) >= 5e-5:
        print('Segment Half Point Position exceeds scanner range. Skipping to next point')
    else:
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(HPX,HPY,Speed)
        print('Segment Half Point')
        time.sleep(WaitTime)
    # Final Position
    if abs(FPX) >= 5e-5 or abs(FPY) >= 5e-5:
        print('Final Position exceeds scanner range. Skipping to next point')
    else:
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(FPX,FPY,Speed)
        print('Final Position')
        time.sleep(WaitTime)

    # Back to initial position
    # Initial Tip Position
    if abs(ITX) >= 5e-5 or abs(ITY) >= 5e-5:
        print('Initial Tip Position exceeds scanner range. Returning to were prgram started')
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(CurPos,Speed)
        print('Program starting Position')
    else:
        TTLInstance.trigger_pulse()
        xyScanner.moveToXYPosition(ITX,ITY,Speed)
        print('Initial Tip Position')
    

    # Stop recordings
    if RecordRealTime:
        RealTimeScan.stopScanning()
    if RecordVideo:
        Snapshooter.stopImageSequenceSaving()
    
    

    

#################### Execution #############################

# Set the scanner
xyScanner = CurrentXYScannerControl()
print xyScanner.getCurrentPosition()
#quit('Just need current position')
#xyScanner.moveToXYPosition(0,0)

# set TTLOutput pulse for later segmentation
output = TTLOutput.outputs['Pin 4']
output.style = 'PULSE'
output.pulse_time = 0.05

#TODO: send current pos and ccd image to other pc with httplib
# determine geometry and target position there and send back
# Speeds
AuxSpeed = 10e-6
MeasurementSpeed = 2e-6
# Initial Positions
Anchor1X = -3.61986495e-5
Anchor1Y = -3.77713914e-5
Anchor2X = -5.04364951e-6
Anchor2Y = 3.89536086e-5
InitialTipX = -4.4103649513738645e-5
InitialTipY = 3.523360862260744e-5
HalfPointX = -2.06211495e-5
HalfPointY = 5.91108623e-7

BufferPosX = -2.52537883e-5
BufferPosY = 2.47224073e-6
FinalPosX = 6.84354713e-6
FinalPosY = 2.80558053e-5

# run the desired program here

hover_over_all_key_points(
xyScanner,output,
Anchor1X,Anchor1Y,
Anchor2X,Anchor2Y,
InitialTipX,InitialTipY,
HalfPointX,HalfPointY,
BufferPosX,BufferPosY,
FinalPosX,FinalPosY,
20e-6,1,False,
False,1)

#xyScanner.moveToXYPosition(0,0,AuxSpeed)
#xyScanner.moveToXYPosition(-3.61986495e-5,-3.77713914e-5,AuxSpeed)
#xyScanner.moveToXYPosition(-5.04364951e-6,3.89536086e-5,AuxSpeed)
#xyScanner.moveToXYPosition(0,0,AuxSpeed)

print('Program ended successfully')
