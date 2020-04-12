import os, traceback, io, json
from json import JSONEncoder
from module.debug import debug

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

class FuelCalcDataEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class FuelCalcData():
    def __init__(self, track, car, persist):
        self.version = 1
        self.track = track
        self.car = car
        self.persist = persist
        self.completedLaps = 0
        self.fuelLapsCounted = 0
        self.fuelUsedForCountedLaps = 0.0
        self.totalTimeCountedLaps = 0.0
        self.bestLapTime = -1

        if self.persist:
            self.read()

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
        finally:
            if self.persist:
                self.write()

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

        if self.persist:
            self.write()

    def write(self):
        dataFilePath = os.path.dirname(os.path.dirname(__file__))+'/data/' + self.track
        os.makedirs(dataFilePath, exist_ok=True)

        calcFilePath =  os.path.dirname(os.path.dirname(__file__))+'/data/' + self.track + '/' + self.car + ".json"
        with io.open(calcFilePath, "w", encoding='utf8') as outfile:
            jsonData = json.dumps(self, indent=4, cls=FuelCalcDataEncoder)
            outfile.write(to_unicode(jsonData))

    def read(self):
        calcFilePath =  os.path.dirname(os.path.dirname(__file__))+'/data/' + self.track + '/' + self.car + ".json"
        if os.path.isfile(calcFilePath):
            with io.open(calcFilePath, "r", encoding='utf8') as infile:
                self.__dict__ = json.load(infile)
