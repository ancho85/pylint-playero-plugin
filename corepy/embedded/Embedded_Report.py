from XMLParser import XMLParser
from Embedded_Record import Embedded_Record

class Embedded_Report(object):

    def __init__(self):
        from Record import Record
        self._record = Embedded_Record(XMLParser.parseReportUserInput(self.__class__.__name__))
        self._record.__class__ = Record
        self._content = ""
        self._view = None
        self.autoRefreshMillis = 0
        self.fontSize = 7
        self.session = Embedded_Record()
        self.reportid = id(self)

    def getRecord(self):
        return self._record

    def setRecord(self, record):
        self._record = record

    def open(self, openw=True):
        self.beforeStartRun()
        self.call_run()
        from ClientServerTools import getClientConnection
        cc = getClientConnection()
        if cc:
            return cc.openReport(self, openw)
        else:
            try:
                print "openReport: " + str(self)
            except Exception, e:
                pass

    def addHTML(self, html):
        self._content += html

    def getHTML(self):
        return self._content

    def isHeaderEnabled(self):
        return False

    def getFileOutput(self):
        return ""

    def addImageLink(self, imageid, filename):
        return

    def setAutoRefresh(self, millis):
        self.autoRefreshMillis = millis

    def clear(self):
        self._webhtml = ""

    def render(self):
        return

    def setView(self, x):
        self._view = x

    def close(self):
        from globalfunctions import rawAction
        rawAction("Report", self.reportid, "close")

    def run(self):
        return

    def openMailWindow(self):
        from MailWindow import MailWindow
        from globalfunctions import NewRecord
        from functions import alert, commit
        mw = MailWindow()
        m = NewRecord("Mail")
        m.defaults()
        if not self._webhtml:
            alert("No data to send.")
            return
        m.save()
        m.importHTML(self._webhtml)
        commit()
        mw.setRecord(m)
        mw.open()

    def getView(self):
        class obj:
            def resize(self,x,y): return None
        return obj()

    def setDefaultFontSize(self, value):
        self.fontSize = value
