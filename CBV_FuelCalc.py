version = "1.0"

import ac, acsys, platform, os, sys, time, re, configparser, traceback, random, math
from module.debug import debug
from module.data import FuelCalcData

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
y_app_size = 400
x_app_min_size = 300
y_app_min_size = 70
defaultFontSize = 14
customFontName = "Digital-7 Mono"
backgroundOpacity = 0.50
minimised = True

# app related

timer = 0
formTimer = 0
waitingForSessionType = True
currentSessionType = -1
averageFuelPerLapValue = None
raceFuelNeededValue = None
raceTotalLapsText = None
raceTotalLapsValue = None
averageLapTimeText = None
averageLapTimeValue = None
bestLapTimeText = None
bestLapTimeValue = None
raceTypeValue = None
averageFuelPerLapText = None
extraLitersText = None
timedRaceText = None
completedLapsText = None
completedLapsValue = None
fuelLapsCountedText = None
fuelLapsCountedValue = None
calcTypeText = None
calcTypeCurrentButton = None
calcTypeMultipleButton = None
calcTypeStoredButton = None
tableCurrentFuel = None
tableCurrentTime = None
tableCurrentLaps = None
tableRaceFuel = None
tableRaceTime = None
tableRaceLaps = None

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
currentLapReset = False
wasInPit = False
raceTotalSessionTime = -1
raceCrossedStartLine = False
sessionStartTime = -1
sessionChangedDetections = 0

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
percentOfBestLapTime = 1.03

persistedCalcData = None
multipleSessionsCalcData = None
currentSessionCalcData = None
shownCalcData = None

def acMain(ac_version):
    global version, appName, mainApp, x_app_size, y_app_size, backgroundOpacity, customFontName

    try:
        debug("starting version " + version)

        mainApp = ac.newApp(appName)
        ac.setTitle(mainApp, "")
        ac.drawBorder(mainApp, 0)
        ac.setIconPosition(mainApp, 0, -10000)
        ac.setBackgroundOpacity(mainApp, backgroundOpacity)
#        ac.initFont(0, customFontName, 0, 0)
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
    global extraLiters, isTimedRace, timedRaceMinutes, raceLaps, percentOfBestLapTime

    try:
        settingsFilePath = os.path.dirname(__file__)+'/settings/settings.ini'
        if not os.path.isfile(settingsFilePath):
            with open(settingsFilePath, "w") as sf:
                debug("Settings file created")

        settingsParser = configparser.ConfigParser()
        settingsParser.optionxform = str
        settingsParser.read(settingsFilePath)

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
    global extraLiters, extraLitersMinButton, extraLitersPlusButton, extraLitersValue, raceTypeValue, averageFuelPerLapText, extraLitersText, timedRaceText, toggleAppSizeButton, fuelLapsCountedText, fuelLapsCountedValue, calcTypeText, calcTypeCurrentButton, calcTypeMultipleButton, calcTypeStoredButton, completedLapsText, completedLapsValue, averageLapTimeText, averageLapTimeValue
    global tableCurrentFuel, tableCurrentTime, tableCurrentLaps, tableRaceFuel, tableRaceTime, tableRaceLaps

    try:
        row = 0
        x_offset = 5
        y_offset = 20

        createLabel("tableHeaderFuel", "Fuel", ((x_app_size)/5) * 2, row * y_offset, defaultFontSize, "center")
        createLabel("tableHeaderTime", "Time", ((x_app_size)/5) * 3, row * y_offset, defaultFontSize, "center")
        createLabel("tableHeaderLaps", "Laps", ((x_app_size)/5) * 4, row * y_offset, defaultFontSize, "center")

        row += 1
        createLabel("tableRowCurrent", "Current", x_offset, row * y_offset, defaultFontSize, "left")

        tableCurrentFuel = createLabel("tableCurrentFuel", "--", ((x_app_size)/5) * 2, row * y_offset, defaultFontSize+2, "center")
        tableCurrentTime = createLabel("tableCurrentTime", "--", ((x_app_size)/5) * 3, row * y_offset, defaultFontSize+2, "center")
        tableCurrentLaps = createLabel("tableCurrentLaps", "--", ((x_app_size)/5) * 4, row * y_offset, defaultFontSize+2, "center")

        row += 1
        createLabel("tableRowRace", "Race", x_offset, row * y_offset, defaultFontSize, "left")

        tableRaceFuel = createLabel("tableRaceFuel", "--", ((x_app_size)/5) * 2, row * y_offset, defaultFontSize+2, "center")
        tableRaceTime = createLabel("tableRaceTime", "--", ((x_app_size)/5) * 3, row * y_offset, defaultFontSize+2, "center")
        tableRaceLaps = createLabel("tableRaceLaps", "--", ((x_app_size)/5) * 4, row * y_offset, defaultFontSize+2, "center")

        toggleAppSizeButton = ac.addButton(mainApp, "+")
        ac.setPosition(toggleAppSizeButton, x_app_size - 20 - x_offset, (row * y_offset) + 5)
        ac.setSize(toggleAppSizeButton, 20, 20)
        ac.addOnClickedListener(toggleAppSizeButton, onToggleAppSizeButtonClickedListener)
        row += 2
        calcTypeText = createLabel("calcTypeText", "Session : ", x_offset, row * y_offset, defaultFontSize, "left")
        calcTypeWidth = 60
        calcTypeOffset = x_offset + 70
        calcTypeCurrentButton = ac.addButton(mainApp, "current")
        ac.setPosition(calcTypeCurrentButton, calcTypeOffset, row * y_offset)
        ac.setSize(calcTypeCurrentButton, calcTypeWidth, 20)
        ac.addOnClickedListener(calcTypeCurrentButton, onCalcTypeCurrentButtonClickedListener)
        calcTypeMultipleButton = ac.addButton(mainApp, "multiple")
        ac.setPosition(calcTypeMultipleButton, calcTypeOffset + calcTypeWidth + 10, row * y_offset)
        ac.setSize(calcTypeMultipleButton, calcTypeWidth, 20)
        ac.addOnClickedListener(calcTypeMultipleButton, onCalcTypeMultipleButtonClickedListener)
        calcTypeStoredButton = ac.addButton(mainApp, "stored")
        ac.setPosition(calcTypeStoredButton, calcTypeOffset + (2*calcTypeWidth) + 20, row * y_offset)
        ac.setSize(calcTypeStoredButton, calcTypeWidth, 20)
        ac.addOnClickedListener(calcTypeStoredButton, onCalcTypeStoredButtonClickedListener)
        row += 2
        averageFuelPerLapText = createLabel("averageFuelPerLapText", "Avg fuel per lap : ", x_offset, row * y_offset, defaultFontSize, "left")
        averageFuelPerLapValue = createLabel("averageFuelPerLapValue", "--", x_app_size - x_offset, row * y_offset, defaultFontSize, "right")
        row += 1
        fuelLapsCountedText = createLabel("fuelLapsCountedText", "Counted laps for fuel average : ", x_offset, row * y_offset, defaultFontSize, "left")
        fuelLapsCountedValue = createLabel("averageFuelPerLapValue", "--", x_app_size - x_offset, row * y_offset, defaultFontSize, "right")
        row += 1
        completedLapsText = createLabel("completedLapsText", "Completed laps : ", x_offset, row * y_offset, defaultFontSize, "left")
        completedLapsValue = createLabel("completedLapsValue", "--", x_app_size - x_offset, row * y_offset, defaultFontSize, "right")
        row += 1
        extraLitersText = createLabel("extraLitersText", "Extra liters : ", x_offset, row * y_offset, defaultFontSize, "left")
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
        timedRaceText = createLabel("timedRaceText", "Is timed race : ", x_offset, row * y_offset, defaultFontSize, "left")
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
        averageLapTimeText = createLabel("averageLapTimeText", "Average lap time : ", x_offset, row * y_offset, defaultFontSize, "left")
        averageLapTimeValue = createLabel("averageLapTimeValue", "--", x_app_size - x_offset, row * y_offset, defaultFontSize, "right")
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
        ac.setPosition(resetButton, x_offset + 5, (row * y_offset) + (y_offset / 2))
        ac.setSize(resetButton, 50, 22)
        ac.addOnClickedListener(resetButton, onResetClickedListener)

        row = raceTypeRow

        row += 5
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
    global mainApp, x_app_size, y_app_size, x_app_min_size, y_app_min_size, minimised, shownCalcData
    global isTimedRace, raceTotalLapsText, raceTotalLapsValue, bestLapTimeText, bestLapTimeValue, timedRaceMinutesSpinner, raceLapsSpinner, timedRaceMinLapButton, timedRacePlusLapButton, averageFuelPerLapText, extraLitersText, timedRaceText
    global extraLitersMinButton, extraLitersPlusButton, resetButton, timedRaceCheckbox, extraLitersValue, averageFuelPerLapValue, fuelLapsCountedText, fuelLapsCountedValue, calcTypeText, calcTypeCurrentButton, calcTypeMultipleButton, calcTypeStoredButton, completedLapsText, completedLapsValue, averageLapTimeText, averageLapTimeValue

    if minimised:
        ac.setSize(mainApp, x_app_min_size, y_app_min_size)
        ac.setVisible(raceTotalLapsText, False)
        ac.setVisible(raceTotalLapsValue, False)
        ac.setVisible(averageLapTimeText, False)
        ac.setVisible(averageLapTimeValue, False)
        ac.setVisible(bestLapTimeText, False)
        ac.setVisible(bestLapTimeValue, False)
        ac.setVisible(timedRaceMinutesSpinner, False)
        ac.setVisible(timedRaceMinLapButton, False)
        ac.setVisible(timedRacePlusLapButton, False)
        ac.setVisible(raceLapsSpinner, False)
        ac.setVisible(averageFuelPerLapText, False)
        ac.setVisible(extraLitersText, False)
        ac.setVisible(timedRaceText, False)
        ac.setVisible(extraLitersMinButton, False)
        ac.setVisible(extraLitersPlusButton, False)
        ac.setVisible(resetButton, False)
        ac.setVisible(timedRaceCheckbox, False)
        ac.setVisible(extraLitersValue, False)
        ac.setVisible(averageFuelPerLapValue, False)
        ac.setVisible(completedLapsText, False)
        ac.setVisible(completedLapsValue, False)
        ac.setVisible(fuelLapsCountedText, False)
        ac.setVisible(fuelLapsCountedValue, False)
        ac.setVisible(calcTypeText, False)
        ac.setVisible(calcTypeCurrentButton, False)
        ac.setVisible(calcTypeMultipleButton, False)
        ac.setVisible(calcTypeStoredButton, False)
    else:
        ac.setSize(mainApp, x_app_size, y_app_size)
        ac.setVisible(averageFuelPerLapText, True)
        ac.setVisible(extraLitersText, True)
        ac.setVisible(timedRaceText, True)
        ac.setVisible(extraLitersMinButton, currentSessionType != 2)
        ac.setVisible(extraLitersPlusButton, currentSessionType != 2)
        ac.setVisible(resetButton, currentSessionType != 2)
        ac.setVisible(timedRaceCheckbox, True)
        ac.setVisible(extraLitersValue, True)
        ac.setVisible(averageFuelPerLapValue, True)
        ac.setVisible(completedLapsText, True)
        ac.setVisible(completedLapsValue, True)
        ac.setVisible(fuelLapsCountedText, True)
        ac.setVisible(fuelLapsCountedValue, True)
        ac.setVisible(calcTypeText, True)
        ac.setVisible(calcTypeCurrentButton, True)
        ac.setVisible(calcTypeMultipleButton, currentSessionType != 2)
        ac.setVisible(calcTypeStoredButton, currentSessionType != 2)
        ac.setVisible(raceTotalLapsText, True)
        ac.setVisible(raceTotalLapsValue, True)
        ac.setVisible(averageLapTimeText, True)
        ac.setVisible(averageLapTimeValue, True)
        ac.setVisible(bestLapTimeText, True)
        ac.setVisible(bestLapTimeValue, True)
        ac.setVisible(timedRaceMinutesSpinner, (isTimedRace and currentSessionType != 2))
        ac.setVisible(timedRaceMinLapButton, (isTimedRace and currentSessionType != 2))
        ac.setVisible(timedRacePlusLapButton, (isTimedRace and currentSessionType != 2))
        ac.setVisible(raceLapsSpinner, (not isTimedRace and currentSessionType != 2))

    updateFuelEstimate()

def onMainAppActivatedListener(*args):
    global mainAppIsActive

    mainAppIsActive = True

    debug("Main app is active")

def onMainAppDismissedListener(*args):
    global mainAppIsActive

    mainAppIsActive = False

    debug("Main app is inactive")

def onMainAppFormRender(deltaT):
    global formTimer

    formTimer += deltaT
    if formTimer < 0.200:
        return

    formTimer = 0

def acUpdate(deltaT):
    global mainAppIsActive, timer
    global averageFuelPerLap, fuelLastLap, completedLaps, fuelAtLapStart, distanceTraveledAtStart, fuelAtStart, lastFuelMeasurement, lastDistanceTraveled, fuelLapsCounted, fuelUsedForCountedLaps, percentOfBestLapTime, bestLapTime, currentSessionType, fuelRemaining
    global currentSessionCalcData, multipleSessionsCalcData, persistedCalcData, shownCalcData, currentLapReset, wasInPit, raceTotalSessionTime, sessionStartTime, sessionChangedDetections, raceCrossedStartLine

    timer += deltaT
    if timer < 0.025:
        return

    timer = 0

    try:
        remaining = sm.physics.fuel
        currentLap = sm.graphics.completedLaps
        totalLaps = sm.graphics.numberOfLaps
        isInPit = sm.graphics.isInPit
        maxFuel = sm.static.maxFuel
        session = sm.graphics.session

        if currentSessionType != session:
            sessionChangedDetections += 1
            if sessionChangedDetections > 5:
                initNewSession(session)

        if isInPit and not wasInPit:
            wasInPit = True
            debug("is in pit")

        fuelRemaining = remaining

        if currentSessionType == 2:
            lapPosition = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)
            currentSectorIndex = sm.graphics.currentSectorIndex

            if raceTotalSessionTime == -1:
                lapCount = ac.getCarState(0, acsys.CS.LapCount)
                currentLapTimeMS = ac.getCarState(0, acsys.CS.LapTime)
                isCountDown = currentLapTimeMS <= 0 and lapCount <= 0

                if not isCountDown:
                    raceTotalSessionTime = sm.graphics.sessionTimeLeft / 1000
                    debug("Green green green - Race session time %d" % (raceTotalSessionTime))

            if raceTotalSessionTime != -1 and not raceCrossedStartLine and currentSectorIndex == 0 and lapPosition < 0.1:
                debug("Crossed start line, lap position = %.1f ; sector = %d" % (lapPosition, currentSectorIndex))
                raceCrossedStartLine = True

        updateFuelEstimate()

        if currentLap != completedLaps: #when crossed finish line
            # debug("Current Lap %d, completedLaps %d, fuelAtLapStart = %.1f, remaining = %.1f" % (currentLap, completedLaps, fuelAtLapStart, remaining))

            if not currentLapReset and not wasInPit and currentLap >= 2 and fuelAtLapStart > remaining: #if more than 2 laps driven
                lastLapTime = sm.graphics.iLastTime
                fuelLastLap = fuelAtLapStart - remaining # calculate fuel used last lap

                currentSessionCalcData.updateCalcData(fuelLastLap, lastLapTime, percentOfBestLapTime)
                multipleSessionsCalcData.updateCalcData(fuelLastLap, lastLapTime, percentOfBestLapTime)
                persistedCalcData.updateCalcData(fuelLastLap, lastLapTime, percentOfBestLapTime)

                updateFuelEstimate()

            fuelAtLapStart = remaining #reset fuelAtLapStart
            completedLaps = currentLap #set completedLaps
            currentLapReset = False
            wasInPit = False
    except Exception:
        debug(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        showMessage("Error: " + traceback.format_exc())

def initNewSession(session):
    global sessionChangedDetections, currentSessionType, sessionStartTime, completedLaps, shownCalcData, currentSessionCalcData, multipleSessionsCalcData, persistedCalcData, raceTotalSessionTime, raceCrossedStartLine

    currentSessionType = session
    sessionStartTime = time.time()
    completedLaps = 0
    raceTotalSessionTime = -1
    raceCrossedStartLine = False
    sessionChangedDetections = 0

    debug("Session type changed to " + str(session))

    if currentSessionCalcData == None:
        currentSessionCalcData = FuelCalcData(sm.static.track, sm.static.carModel, False)
    else:
        currentSessionCalcData.reset()

    if multipleSessionsCalcData == None:
        multipleSessionsCalcData = FuelCalcData(sm.static.track, sm.static.carModel, False)

    if persistedCalcData == None:
        persistedCalcData = FuelCalcData(sm.static.track, sm.static.carModel, True)
        if persistedCalcData.hasData():
            shownCalcData = persistedCalcData
        else:
            shownCalcData = multipleSessionsCalcData

    if currentSessionType == 2:
        shownCalcData = currentSessionCalcData

    updateUIVisibility()
    updateCalcTypeUI()
    updateFuelEstimate()

def updateFuelEstimate():
    global averageFuelPerLap, timedRaceMinutes, extraLiters, timedRaceExtraLaps, isTimedRace, raceLaps, fuelRemaining, currentSessionType, sessionStartTime, raceTotalSessionTime
    global averageFuelPerLapValue, raceFuelNeededValue, raceTotalLapsValue, extraLitersValue, raceTypeValue, fuelLapsCountedText, fuelLapsCountedValue, completedLapsValue, shownCalcData, averageLapTimeValue, raceCrossedStartLine
    global tableCurrentFuel, tableCurrentTime, tableCurrentLaps, tableRaceFuel, tableRaceTime, tableRaceLaps

    # TODO: Only update if we are live (AC_LIVE)

    calcData = shownCalcData

    expectedNumberOfLaps = -1

    if currentSessionType == 2:
        expectedNumberOfLaps = getExpectedRaceLaps()
    else:
        if isTimedRace:
            ac.setText(raceTypeValue, "for a %d minutes timed race" % (timedRaceMinutes))
        else:
            ac.setText(raceTypeValue, "for a %d lap race" % (raceLaps))

    ac.setText(tableCurrentFuel, "%.1f" % (fuelRemaining))
    ac.setText(extraLitersValue, str(extraLiters))

    if calcData != None and calcData.hasData() and calcData.averageFuelUsed() != 0.0 and calcData.bestLapTime != -1:
        raceTime = timedRaceMinutes * 60 * 1000

        if isTimedRace:
            laps = (raceTime / calcData.bestLapTime) + timedRaceExtraLaps
        else:
            laps = raceLaps

        # debug("laps = %.1f ; extraLiters = %d" % (laps, extraLiters))

        fuelNeeded = math.ceil(math.ceil(laps) * calcData.averageFuelUsed()) + extraLiters

        ac.setText(averageFuelPerLapValue, "%.3f" % (calcData.averageFuelUsed()))
        ac.setText(completedLapsValue, "%d" % (calcData.completedLaps))
        ac.setText(fuelLapsCountedValue, "%d" % (calcData.fuelLapsCounted))

        if timedRaceExtraLaps != 0:
            if timedRaceExtraLaps > 0:
                ac.setText(raceTotalLapsValue, "%.1f (+%d)" % (laps, timedRaceExtraLaps))
            else:
                ac.setText(raceTotalLapsValue, "%.1f (%d)" % (laps, timedRaceExtraLaps))
        else:
            ac.setText(raceTotalLapsValue, "%.1f" % (laps))

        timeRemaining = (fuelRemaining / calcData.averageFuelUsed()) * calcData.averageLapTime();
        timeRemainingSeconds = (timeRemaining / 1000) % 60
        timeRemainingMinutes = (timeRemaining // 1000) // 60
        #ac.setText(raceTypeValue, "Remaining : %.1f liter, %.0f mins" % (fuelRemaining, timeRemainingMinutes))

        ac.setText(tableCurrentTime, "%.0f" % (timeRemainingMinutes))

        lapsRemaining = fuelRemaining / calcData.averageFuelUsed()
        #ac.setText(raceTypeValue, "Remaining : %.1f liter, %d laps" % (fuelRemaining, lapsRemaining))

        ac.setText(tableCurrentLaps, "%d" % (lapsRemaining))

        if currentSessionType == 2:
            if expectedNumberOfLaps != -1:
                currentLap = ac.getCarState(0, acsys.CS.LapCount)
                lapPosition = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)

                lapCount = currentLap
                if raceCrossedStartLine:
                    lapCount = currentLap + lapPosition

                lapRemaining = expectedNumberOfLaps - lapCount
                fuelEndOfRace = fuelRemaining - (lapRemaining * calcData.averageFuelUsed())
                # ac.setText(raceFuelNeededValue, "Fuel end of race : %d (%.1f) (%.1f)" % (fuelEndOfRace, lapRemaining, lapCount))

                ac.setText(tableRaceFuel, "%d" % (fuelEndOfRace))
                ac.setText(tableRaceTime, "%.0f" % (sessionTimeLeft / 60))
                ac.setText(tableRaceLaps, "%.1f" % (lapsRemaining))
        else:
            ac.setText(tableRaceFuel, "%d" % (fuelNeeded))
            if isTimedRace:
                ac.setText(tableRaceTime, "%d" % (timedRaceMinutes))
            else:
                estimatedRaceTime = raceLaps * calcData.averageLapTime()
                estimatedRaceMinutes = (estimatedRaceTime // 1000) // 60
                ac.setText(tableRaceTime, "%.0f" % (estimatedRaceMinutes))

            ac.setText(tableRaceLaps, "%d" % (laps))

        averageLapTime = calcData.averageLapTime()
        averageLapValueSeconds = (averageLapTime / 1000) % 60
        averageLapValueMinutes = (averageLapTime // 1000) // 60
        ac.setText(averageLapTimeValue,  "{:.0f}:{:06.3f}".format(averageLapValueMinutes, averageLapValueSeconds)[:-1])
        bestLapValueSeconds = (calcData.bestLapTime / 1000) % 60
        bestLapValueMinutes = (calcData.bestLapTime // 1000) // 60
        ac.setText(bestLapTimeValue,  "{:.0f}:{:06.3f}".format(bestLapValueMinutes, bestLapValueSeconds)[:-1])
    else:
        if sm.static.isTimedRace == 1:
            ac.setText(tableRaceLaps, "--")
            # ac.setText(raceFuelNeededValue, "Remaining : %.1f liter, -- mins" % (fuelRemaining))
        else:
            ac.setText(tableRaceTime, "--")
            # ac.setText(raceFuelNeededValue, "Remaining : %.1f liter, -- laps" % (fuelRemaining))
        ac.setText(tableCurrentTime, "--")
        ac.setText(tableCurrentLaps, "--")
        ac.setText(tableRaceFuel, "--")
        ac.setText(averageFuelPerLapValue, "--")
        ac.setText(raceTotalLapsValue, "--")
        ac.setText(averageLapTimeValue,  "--")
        ac.setText(bestLapTimeValue,  "--")
        ac.setText(completedLapsValue, "--")
        ac.setText(fuelLapsCountedValue, "--")

def getExpectedRaceLaps():
    global raceTotalSessionTime, raceCrossedStartLine

    extraLap = 0
    if sm.static.hasExtraLap:
        extraLap = 1

    if sm.static.isTimedRace != 1:
        return sm.graphics.numberOfLaps + extraLap
    else:
        if raceTotalSessionTime != -1 and raceCrossedStartLine:
            numberOfCars = ac.getCarsCount()
            carIds = range(0, ac.getCarsCount(), 1)
            for carId in carIds:
                # debug("Getting car with ID : " + str(carId) + " ; driver name = " + str(ac.getDriverName(carId)))
                if str(ac.getCarName(carId)) == '-1':
                    # debug("Car name for ID is -1 - break : " + str(carId))
                    break
                else:
                    carPosition = ac.getCarRealTimeLeaderboardPosition(carId)
                    # debug("Car position = " + str(carPosition))
                    if carPosition == 0:
                        sessionTimeElapsed = raceTotalSessionTime - (sm.graphics.sessionTimeLeft / 1000)
                        # debug("Session time elapsed is : %d" % (sessionTimeElapsed))
                        lapCount = ac.getCarState(carId, acsys.CS.LapCount) + ac.getCarState(carId, acsys.CS.NormalizedSplinePosition)
                        # debug("Lap count is : " + str(lapCount))
                        estimatedLaps = ((raceTotalSessionTime - 10) / sessionTimeElapsed) * lapCount # 10 seconds to account for standing start
                        # debug("Estimated number of laps : " + str(estimatedLaps))
                        return math.ceil(estimatedLaps)
                    else:
                        continue

    return -1

def onToggleAppSizeButtonClickedListener(*args):
    global minimised, toggleAppSizeButton

    minimised = not minimised
    if minimised:
        ac.setText(toggleAppSizeButton, "+")
    else:
        ac.setText(toggleAppSizeButton, "-")

    updateUIVisibility()

def onTimedRaceChangedListener(*args):
    global isTimedRace

    isTimedRace = not isTimedRace
    updateUIVisibility()

def onTimedRaceMinutesChangedListener(*args):
    global timedRaceMinutesSpinner, timedRaceMinutes, shownCalcData

    timedRaceMinutes = ac.getValue(timedRaceMinutesSpinner)
    updateFuelEstimate()

def onTimedRaceMinLapButtonClickedListener(*args):
    global timedRaceExtraLaps, shownCalcData

    timedRaceExtraLaps -= 1
    updateFuelEstimate()

def onTimedRacePlusLapButtonClickedListener(*args):
    global timedRaceExtraLaps, shownCalcData

    debug("args = %s" % (args,))

    timedRaceExtraLaps += 1
    updateFuelEstimate()

def onExtraLitersMinButtonClickedListener(*args):
    global extraLiters, shownCalcData

    extraLiters -= 1
    updateFuelEstimate()

def onExtraLitersPlusButtonClickedListener(*args):
    global extraLiters, shownCalcData

    extraLiters += 1
    updateFuelEstimate()

def onRaceLapsChangedListener(*args):
    global raceLapsSpinner, raceLaps, shownCalcData

    raceLaps = ac.getValue(raceLapsSpinner)
    updateFuelEstimate()

def onResetClickedListener(*args):
    global averageFuelPerLap, fuelLapsCounted, fuelUsedForCountedLaps, shownCalcData, currentLapReset

    currentLapReset = True
    shownCalcData.reset()
    updateFuelEstimate()

def onCalcTypeCurrentButtonClickedListener(*args):
    global shownCalcData, currentSessionCalcData, calcTypeCurrentButton

    shownCalcData = currentSessionCalcData
    updateCalcTypeUI()
    updateFuelEstimate()

def onCalcTypeMultipleButtonClickedListener(*args):
    global shownCalcData, multipleSessionsCalcData, calcTypeMultipleButton

    shownCalcData = multipleSessionsCalcData
    updateCalcTypeUI()
    updateFuelEstimate()

def onCalcTypeStoredButtonClickedListener(*args):
    global shownCalcData, persistedCalcData, calcTypeStoredButton

    shownCalcData = persistedCalcData
    updateCalcTypeUI()
    updateFuelEstimate()

def updateCalcTypeUI():
    global shownCalcData, currentSessionCalcData, multipleSessionsCalcData, persistedCalcData
    global calcTypeCurrentButton, calcTypeMultipleButton, calcTypeStoredButton

    ac.drawBorder(calcTypeCurrentButton, shownCalcData == currentSessionCalcData)
    ac.drawBorder(calcTypeMultipleButton, shownCalcData == multipleSessionsCalcData)
    ac.drawBorder(calcTypeStoredButton, shownCalcData == persistedCalcData)

def acShutdown(*args):
    global mainAppIsActive

def createLabel(name, text, x, y, font_size = 14, align = "center"):
    global mainApp

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
