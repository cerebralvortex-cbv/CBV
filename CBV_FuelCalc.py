version = "0.4"

import ac, acsys, platform, os, sys, time, re, configparser, traceback, random, math

try:
    if platform.architecture()[0] == "64bit":
        sysdir = os.path.dirname(__file__)+'/lib/stdlib64'
    else:
        sysdir = os.path.dirname(__file__)+'/lib/stdlib'

    sys.path.insert(0, sysdir)
    os.environ['PATH'] = os.environ['PATH'] + ";."
except Exception as e:
    debug(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

from lib.sim_info_cbv import sm
import threading
import ctypes
from ctypes import wintypes

## variables

# app

appName = "CBV_FuelCalc"
mainApp = 0
mainAppIsActive = False
x_app_size = 300
y_app_size = 240
defaultFontSize = 14
customFontName = "Digital-7 Mono"
backgroundOpacity = 0

# app related

timer = 0
formTimer = 0
waitingForSessionType = True
previousSessionType = -1
averageFuelPerLapValue = 0
raceFuelNeededValue = 0
raceTotalLapsText = 0
raceTotalLapsValue = 0
bestLapTimeText = 0
bestLapTimeValue = 0

# fuel

averageFuelPerLap = 0.0
fuelLastLap = 0.0
completedLaps = 0.0
fuelAtLapStart = 0.0
fuelRemaining = 0.0
distanceTraveledAtStart = 0.0
fuelAtStart = 0.0
lastFuelMeasurement = 0.0
lastDistanceTraveled = 0.0
fuelLapsCounted = 0
fuelUsedForCountedLaps = 0.0
bestLapTime = -1

# config

settingsSectionGeneral = "GENERAL"
settingsSectionFUELCALC = "FUELCALC"
extraLiters = 2
extraLitersMinButton = 0
extraLitersPlusButton = 0
extraLitersValue = 0
isTimedRace = True
timedRaceCheckbox = 0
timedRaceMinutesSpinner = 0
timedRaceMinutes = 20
timedRaceExtraLaps = 0
timedRacePlusLapButton = 0
timedRaceMinLapButton = 0
raceLapsSpinner = 0
raceLaps = 10
resetButton = 0
percentOfBestLapTime = 1.07

def acMain(ac_version):
    global version, appName, mainApp, x_app_size, y_app_size, backgroundOpacity, customFontName

    try:
        debug("starting version " + version)

        mainApp = ac.newApp(appName)
        ac.setTitle(mainApp, "")
        ac.drawBorder(mainApp, 0)
        ac.setIconPosition(mainApp, 0, -10000)
        ac.setBackgroundOpacity(mainApp, backgroundOpacity)
        # ac.initFont(0, customFontName, 0, 0)
        ac.setSize(mainApp, x_app_size, y_app_size)
        ac.addOnAppActivatedListener(mainApp, onMainAppActivatedListener)
        ac.addOnAppDismissedListener(mainApp, onMainAppDismissedListener)
        ac.addRenderCallback(mainApp, onMainAppFormRender)

        getSettings()
        createUI()

        return appName

    except exception:
        debug(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        showMessage("Error: " + traceback.format_exc())

def getSettings():
    global isTimedRace, timedRaceCheckbox, timedRaceMinutesSpinner, timedRaceMinutes, raceLapsSpinner, raceLaps, percentOfBestLapTime

    try:
        settingsFilePath = os.path.dirname(__file__)+'/settings/settings.ini'
        if not os.path.isfile(settingsFilePath):
            with open(settingsFilePath, "w") as sf:
                debug("Settings file created")

        settingsParser = configparser.ConfigParser()
        settingsParser.optionxform = str
        settingsParser.read(settingsFilePath)

        defaultFontSize = int(getSettingsValue(settingsParser, settingsSectionGeneral, "defaultFontSize", 14))
        extraLiters = int(getSettingsValue(settingsParser, settingsSectionFUELCALC, "extraLiters", 2))
        isTimedRace = getSettingsValue(settingsParser, settingsSectionFUELCALC, "isTimedRace", True, True)
        timedRaceMinutes = int(getSettingsValue(settingsParser, settingsSectionFUELCALC, "timedRaceMinutes", 20))
        raceLaps = int(getSettingsValue(settingsParser, settingsSectionFUELCALC, "raceLaps", 10))
        percentOfBestLapTime = float(getSettingsValue(settingsParser, settingsSectionFUELCALC, "percentOfBestLapTime", 1.07))

        with open(settingsFilePath, 'w') as settingsFile:
             settingsParser.write(settingsFile)
        return True

    except exception:
        debug("Error while loading settings : " + traceback.format_exc())
        return False

def createUI():
    global x_app_size, y_app_size, defaultFontSize
    global isTimedRace, timedRaceCheckbox, averageFuelPerLapValue, raceFuelNeededValue, raceTotalLapsText, raceTotalLapsValue, bestLapTimeText, bestLapTimeValue, timedRaceMinutesSpinner, raceLapsSpinner, resetButton, timedRacePlusLapButton, timedRaceMinLapButton
    global extraLiters, extraLitersMinButton, extraLitersPlusButton, extraLitersValue

    try:
        row = 0
        x_offset = 5
        y_offset = 20

        createLabel("averageFuelPerLapText", "Avg fuel per lap : ", x_offset, row * y_offset, defaultFontSize, "left")
        averageFuelPerLapValue = createLabel("averageFuelPerLapValue", "--", x_app_size - x_offset, row * y_offset, defaultFontSize, "right")
        row += 1
        createLabel("raceFuelNeededText", "Race fuel needed : ", x_offset, row * y_offset, defaultFontSize, "left")
        raceFuelNeededValue = createLabel("raceFuelNeededValue", "--", x_app_size - x_offset, row * y_offset, defaultFontSize, "right")
        row += 1
        createLabel("extraLitersLabel", "Extra liters : ", x_offset, row * y_offset, defaultFontSize, "left")
        extraLitersValue = createLabel("extraLitersValue", "--", x_app_size - x_offset, row * y_offset, defaultFontSize, "right")
        extraLitersMinButton = ac.addButton(mainApp, "-")
        ac.setPosition(extraLitersMinButton, 180, row * y_offset)
        ac.setSize(extraLitersMinButton, 20, 20)
        ac.addOnClickedListener(extraLitersMinButton, onExtraLitersMinButtonClickedListener)
        extraLitersPlusButton = ac.addButton(mainApp, "+")
        ac.setPosition(extraLitersPlusButton, 205, row * y_offset)
        ac.setSize(extraLitersPlusButton, 20, 20)
        ac.addOnClickedListener(extraLitersPlusButton, onExtraLitersPlusButtonClickedListener)
        row += 1
        createLabel("timedRaceLabel", "Is timed race : ", x_offset, row * y_offset, defaultFontSize, "left")
        timedRaceCheckbox = ac.addCheckBox(mainApp, "")
        ac.setPosition(timedRaceCheckbox, x_app_size - (x_offset + 15), row * y_offset + 4)
        ac.setSize(timedRaceCheckbox, 15, 15)
        ac.setValue(timedRaceCheckbox, isTimedRace)
        ac.addOnCheckBoxChanged(timedRaceCheckbox, onTimedRaceChangedListener)
        row += 1

        raceTypeRow = row

        raceTotalLapsText = createLabel("raceTotalLapsText", "Expected race laps : ", x_offset, row * y_offset, defaultFontSize, "left")
        raceTotalLapsValue = createLabel("raceTotalLapsValue", "--", x_app_size - x_offset, row * y_offset, defaultFontSize, "right")
        timedRaceMinLapButton = ac.addButton(mainApp, "-")
        ac.setPosition(timedRaceMinLapButton, 180, row * y_offset)
        ac.setSize(timedRaceMinLapButton, 20, 20)
        ac.addOnClickedListener(timedRaceMinLapButton, onTimedRaceMinLapButtonClickedListener)
        timedRacePlusLapButton = ac.addButton(mainApp, "+")
        ac.setPosition(timedRacePlusLapButton, 205, row * y_offset)
        ac.setSize(timedRacePlusLapButton, 20, 20)
        ac.addOnClickedListener(timedRacePlusLapButton, onTimedRacePlusLapButtonClickedListener)
        row += 1
        bestLapTimeText = createLabel("bestLapTimeText", "Best lap time : ", x_offset, row * y_offset, defaultFontSize, "left")
        bestLapTimeValue = createLabel("bestLapTimeValue", "--", x_app_size - x_offset, row * y_offset, defaultFontSize, "right")
        row += 3
        timedRaceMinutesSpinner = ac.addSpinner(mainApp, "Timed race minutes")
        ac.setRange(timedRaceMinutesSpinner, 0, 240)
        ac.setValue(timedRaceMinutesSpinner, timedRaceMinutes)
        ac.setStep(timedRaceMinutesSpinner, 1)
        ac.setPosition(timedRaceMinutesSpinner, x_app_size / 6, row * y_offset)
        ac.addOnValueChangeListener(timedRaceMinutesSpinner, onTimedRaceMinutesChangedListener)
        row += 2
        resetButton = ac.addButton(mainApp, "Reset")
        ac.setPosition(resetButton, x_offset, row * y_offset)
        ac.setSize(resetButton, 50, 22)
        ac.addOnClickedListener(resetButton, onResetClickedListener)

        row = raceTypeRow

        row += 2
        raceLapsSpinner = ac.addSpinner(mainApp, "Race laps")
        ac.setRange(raceLapsSpinner, 0, 100)
        ac.setValue(raceLapsSpinner, raceLaps)
        ac.setStep(raceLapsSpinner, 1)
        ac.setPosition(raceLapsSpinner, x_app_size / 6, row * y_offset)
        ac.addOnValueChangeListener(raceLapsSpinner, onRaceLapsChangedListener)

        updateUIVisibility()

    except exception:
        debug(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        showMessage("Error: " + traceback.format_exc())

def updateUIVisibility():
    global isTimedRace, raceTotalLapsText, raceTotalLapsValue, bestLapTimeText, bestLapTimeValue, timedRaceMinutesSpinner, raceLapsSpinner, timedRaceMinLapButton, timedRacePlusLapButton

    ac.setVisible(raceTotalLapsText, isTimedRace)
    ac.setVisible(raceTotalLapsValue, isTimedRace)
    ac.setVisible(bestLapTimeText, isTimedRace)
    ac.setVisible(bestLapTimeValue, isTimedRace)
    ac.setVisible(timedRaceMinutesSpinner, isTimedRace)
    ac.setVisible(timedRaceMinLapButton, isTimedRace)
    ac.setVisible(timedRacePlusLapButton, isTimedRace)
    ac.setVisible(raceLapsSpinner, not isTimedRace)

def onMainAppActivatedListener(*args):
    global mainAppIsActive

    mainAppIsActive = True

    debug("Main app is active")

def onMainAppDismissedListener(*args):
    global mainAppIsActive

    mainAppIsActive = False

    debug("Main app is inactive")

def onMainAppFormRender(deltaT):
    global formTimer, waitingForSessionType, previousSessionType, waitTimeSessionType, timerSessionType, completedLaps

    formTimer += deltaT
    if formTimer < 0.200:
        return

    formTimer = 0

def acUpdate(deltaT):
    global mainAppIsActive, timer
    global averageFuelPerLap, fuelLastLap, completedLaps, fuelAtLapStart, distanceTraveledAtStart, fuelAtStart, lastFuelMeasurement, lastDistanceTraveled, fuelLapsCounted, fuelUsedForCountedLaps, percentOfBestLapTime, bestLapTime, previousSessionType, fuelRemaining

    timer += deltaT
    if timer < 0.025:
        return

    timer = 0

    try:
        remaining = sm.physics.fuel
        currentLap = sm.graphics.completedLaps
        totalLaps = sm.graphics.numberOfLaps
        distanceTraveled = sm.graphics.distanceTraveled
        isInPit = sm.graphics.isInPit
        inPitLane = ac.isCarInPitline(0)
        maxFuel = sm.static.maxFuel
        normalizedSplinePosition = round(sm.graphics.normalizedCarPosition, 4)
        session = sm.graphics.session
        if previousSessionType != session or remaining > fuelRemaining:
            previousSessionType = session
            completedLaps = 0
            debug("Session type changed to " + str(session))

        if currentLap >= 1 and bestLapTime == -1 or (sm.graphics.iBestTime != 0 and sm.graphics.iBestTime < bestLapTime):
            bestLapTime = sm.graphics.iBestTime
            debug("New best lap time posted : " + str(bestLapTime))

        lastLapTime = sm.graphics.iLastTime
        fuelRemaining = remaining

        if currentLap != completedLaps: #when crossed finish line
            debug("Current Lap %d, fuelAtLapStart = %.1f, remaining = %.1f" % (currentLap, fuelAtLapStart, remaining))

            if currentLap >= 2 and fuelAtLapStart > remaining: #if more than 2 laps driven
                thresholdLapTime = bestLapTime * percentOfBestLapTime

                debug("lastLapTime = %.3f, thresholdLapTime = %.3f" % (lastLapTime, thresholdLapTime))

                if lastLapTime > thresholdLapTime:
                    debug("Last lap was too slow, fuel not counted")
                else:
                    fuelLastLap = fuelAtLapStart - remaining # calculate fuel used last lap
                    fuelLapsCounted += 1
                    fuelUsedForCountedLaps += fuelLastLap
                    # averageFuelPerLap = (averageFuelPerLap * (currentLap - 2) + fuelLastLap) / (currentLap - 1) #calculate AverageFuelPerLap
                    averageFuelPerLap = fuelUsedForCountedLaps / fuelLapsCounted
                    debug("AverageFuelPerLap = %.3f" % (averageFuelPerLap))
                    updateFuelEstimate()

            fuelAtLapStart = remaining #reset fuelAtLapStart
            completedLaps = currentLap #set completedLaps

            debug("fuelLapsCounted %d, fuelUsedForCountedLaps = %.1f" % (fuelLapsCounted, fuelUsedForCountedLaps))

    except exception:
        debug(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        showMessage("Error: " + traceback.format_exc())

def updateFuelEstimate():
    global averageFuelPerLap, timedRaceMinutes, extraLiters, timedRaceExtraLaps, isTimedRace, raceLaps, bestLapTime
    global averageFuelPerLapValue, raceFuelNeededValue, raceTotalLapsValue, extraLitersValue

    ac.setText(extraLitersValue, str(extraLiters))

    if averageFuelPerLap != 0.0 and bestLapTime != -1:
        raceTime = timedRaceMinutes * 60 * 1000

        if isTimedRace:
            laps = (raceTime / bestLapTime) + timedRaceExtraLaps
        else:
            laps = raceLaps

        fuelNeeded = math.ceil(math.ceil(laps) * averageFuelPerLap) + extraLiters
        bestLapValueSeconds = (bestLapTime / 1000) % 60
        bestLapValueMinutes = (bestLapTime // 1000) // 60

        ac.setText(averageFuelPerLapValue, "%.3f" % (averageFuelPerLap))

        if timedRaceExtraLaps != 0:
            if timedRaceExtraLaps > 0:
                ac.setText(raceTotalLapsValue, "%.1f (+%d)" % (laps, timedRaceExtraLaps))
            else:
                ac.setText(raceTotalLapsValue, "%.1f (%d)" % (laps, timedRaceExtraLaps))
        else:
            ac.setText(raceTotalLapsValue, "%.1f" % (laps))

        ac.setText(raceFuelNeededValue, str(fuelNeeded))
        ac.setText(bestLapTimeValue,  "{:.0f}:{:06.3f}".format(bestLapValueMinutes, bestLapValueSeconds)[:-1])
    else:
        ac.setText(averageFuelPerLapValue, "--")
        ac.setText(raceTotalLapsValue, "--")
        ac.setText(raceFuelNeededValue, "--")
        ac.setText(bestLapTimeValue,  "--")

def onTimedRaceChangedListener(*args):
    global isTimedRace, timedRaceCheckbox

    if isTimedRace:
        isTimedRace = False
    else:
        isTimedRace = True

    updateUIVisibility()
    updateFuelEstimate()

def onTimedRaceMinutesChangedListener(*args):
    global timedRaceMinutesSpinner, timedRaceMinutes

    timedRaceMinutes = ac.getValue(timedRaceMinutesSpinner)
    updateFuelEstimate()

def onTimedRaceMinLapButtonClickedListener(*args):
    global timedRaceExtraLaps

    timedRaceExtraLaps -= 1
    updateFuelEstimate()

def onTimedRacePlusLapButtonClickedListener(*args):
    global timedRaceExtraLaps

    timedRaceExtraLaps += 1
    updateFuelEstimate()

def onExtraLitersMinButtonClickedListener(*args):
    global extraLiters

    extraLiters -= 1
    updateFuelEstimate()

def onExtraLitersPlusButtonClickedListener(*args):
    global extraLiters

    extraLiters += 1
    updateFuelEstimate()

def onRaceLapsChangedListener(*args):
    global raceLapsSpinner, raceLaps

    raceLaps = ac.getValue(raceLapsSpinner)
    updateFuelEstimate()

def onResetClickedListener(*args):
    global averageFuelPerLap, fuelLapsCounted, fuelUsedForCountedLaps

    averageFuelPerLap = 0.0
    fuelLapsCounted = 0
    fuelUsedForCountedLaps = 0.0

    updateFuelEstimate()

def acShutdown(*args):
    global mainAppIsActive

def createLabel(name, text, x, y, font_size = 14, align = "center"):
    global mainApp, labels

    label = ac.addLabel(mainApp, name)
    ac.setText(label, text)
    ac.setPosition(label, x, y)
    ac.setFontSize(label, font_size)
    ac.setFontAlignment(label, align)

    return label

def getSettingsValue(parser, section, option, value, boolean = False):
    if parser.has_option(str(section), str(option)):
        if boolean:
            return parser.getboolean(str(section), option)
        else:
            return parser.get(str(section), str(option))
    else:
        return setSettingsValue(parser, section, option, value)


def setSettingsValue(parser, section, option, value):
    if not parser.has_section(section):
        parser.add_section(section)

    parser.set(str(section), str(option), str(value))
    return value

def debug(message):
    global appName

    ac.log(appName + ": " + message)
    ac.console(appName + ": " + message)
