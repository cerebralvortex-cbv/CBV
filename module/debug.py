import ac

appName = "CBV_FuelCalc"

def debug(message):
    global appName

    fileDebug = False
    consoleDebug = False

    if fileDebug:
        ac.log(appName + ": " + message)
    if consoleDebug:
        ac.console(appName + ": " + message)
