# JPK Script

from com.jpk.inst.lib import JPKScript
from com.jpk.util import XYPosition
from com.jpk.util.jyswingutils import callSwing


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


# how to use
xyScanner = CurrentXYScannerControl()
print xyScanner.getCurrentPosition()
xyScanner.moveToXYPosition(0,0)
xyScanner.moveRelative(1e-6, 1e-6)


