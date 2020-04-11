import ac

appName = "CBV_FuelCalc"

def debug(message):
    global appName

    ac.log(appName + ": " + message)
    ac.console(appName + ": " + message)
