import traceback
from module.debug import debug

class FuelCalcData():
    completedLaps = 0
    fuelLapsCounted = 0
    fuelUsedForCountedLaps = 0.0
    totalTimeCountedLaps = 0.0
    bestLapTime = -1

    def updateCalcData(self, fuelLastLap, lapTime, percentOfBestLapTime):
        try:
            self.completedLaps += 1
            if self.bestLapTime == -1 or lapTime < self.bestLapTime:
                self.bestLapTime = lapTime

            thresholdLapTime = self.bestLapTime * percentOfBestLapTime
            if lapTime < thresholdLapTime:
                self.fuelLapsCounted += 1
                self.fuelUsedForCountedLaps += fuelLastLap
                self.totalTimeCountedLaps += lapTime
                return True
            else:
                return False
        except Exception:
            debug(traceback.format_exc())
            showMessage("Error: " + traceback.format_exc())

    def averageFuelUsed(self):
        return self.fuelUsedForCountedLaps / self.fuelLapsCounted

    def averageLapTime(self):
        return self.totalTimeCountedLaps / self.fuelLapsCounted

    def hasData(self):
        return self.fuelLapsCounted > 0

    def reset(self):
        self.completedLaps = 0
        self.fuelLapsCounted = 0
        self.fuelUsedForCountedLaps = 0.0
        self.totalTimeCountedLaps = 0.0
        self.bestLapTime = -1
