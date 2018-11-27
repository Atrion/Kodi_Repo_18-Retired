
import xbmc

def LOG(msg):
    xbmc.log(msg, xbmc.LOGNOTICE)

class Service(xbmc.Monitor):
    def __init__(self):
        self._pollInterval = 60  # One minute
        LOG('SERVICE START')
        self.start()
        LOG('SERVICE STOP')

    def start(self):
        self.onKodiStarted()
        while not self.waitForAbort(self._pollInterval):
            self.poll()

    def onKodiStarted(self):
        self.updateCVContent()

    def onScanFinished(self):
        pass

    def poll(self):
        pass

    def updateCVContent(self):
        xbmc.executebuiltin('RunScript(script.cinemavision,update.database)')

Service()
