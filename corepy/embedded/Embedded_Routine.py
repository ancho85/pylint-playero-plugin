from CThread import *
from globalfunctions import getScriptDirs, getServerConnection

class BackgroundRoutineRunner(CThread):

    def __init__(self, routine):
        CThread.__init__(self)
        self.routine = routine
        self.setName(routine.__class__.__name__)

    def run(self):
        self.routine.call_run()
        self.routine.afterRun()

class ServerRoutineRunner(CThread):

    def __init__(self, routine):
        CThread.__init__(self)
        self.routine = routine
        self.setName("Server: " + routine.__class__.__name__)

    def run(self):
        sc = getServerConnection()
        sc.runRoutine(self.routine.__class__.__name__, self.routine.getRecord())

class Embedded_Routine(object):

    def __init__(self, spec=None):
        self.__background__ = False
        self.__runOnServer__ = False
        if spec:
            self.__fixed_spec__ = True
            self.setRecord(spec)
        else:
            self.__fixed_spec__ = False
            #self.setRecord(self.genRoutineRecord())
        self._should_finish = False
        self.__thread__ = None
        self.__task__ = None

    def setRecord(self, record):
        self.__record__ = record

    def setTask(self, task):
        self.__task__ = task

    def getTask(self):
        return self.__task__

    def getRecord(self):
        return self.__record__

    def setBackground(self, b):
        self.__background__ = b

    def setRunOnServer(self, b):
        self.__runOnServer__ = b

    def getBackground(self):
        return self.__background__

    def background(self):
        return self.__background__

    def getRunOnServer(self):
        return self.__runOnServer__

    def getRoutineUserInputXML(self):
        import os
        sdirs = getScriptDirs()
        for sd in sdirs:
            fn = os.path.join(sd, "interface", self.__class__.__name__ + ".routinewindow.xml")
            if os.path.exists(fn):
                res = open(fn, "rb").read()
                return res
        return None

    """def genRoutineWindow(self):
        xml = self.getRoutineUserInputXML()
        if not xml: return None
        xml = xml.replace("\n","")
        import re
        windowxml = re.search("(<routinewindow.*?>.*</routinewindow>)", xml)
        w = None
        if windowxml:
            wxml = windowxml.group(1)
            wxml = wxml.replace("routinewindow", "window")
            wname = re.search('<window .*?name="([^"]*?)".*?>', wxml)
            w = createRoutineWindow(wxml)
            if wname:
                windowname = wname.group(1)
                if not windowname.endswith("RoutineWindow"): windowname += "RoutineWindow"
                try:
                    exec("from %s import %s as cls" % (windowname, windowname))
                    w.__class__ = cls
                except ImportError, e:
                    pass
        return w

    def genRoutineRecord(self):
        if "WEBCLIENT" in globals():
            from classes.XMLParser import XMLParser
            return Embedded_Record(XMLParser.parseRoutineUserInput(self.__class__.__name__))
        xml = self.getRoutineUserInputXML()
        if not xml: return None
        xml = xml.replace("\n","")
        import re
        recordxml = re.search("(<routinerecord.*?>.*</routinerecord>)", xml)
        r = None
        if recordxml:
            rxml = recordxml.group(1)
            rxml = rxml.replace("routinerecord", "record")
            r = createRecord(rxml)
        return r"""

    def open(self):
        if not self.__fixed_spec__: self.defaults()
        self.start()

    def shouldFinish(self):
        return self._should_finish

    def start(self):
        if self.getRunOnServer():
            self.__thread__ = ServerRoutineRunner(self)
            self.call_beforeRun()
            self.__thread__.start()
        else:
            if self.getBackground():
                self.__thread__ = BackgroundRoutineRunner(self)
                self.call_beforeRun()
                self.__thread__.start()
            else:
                self.call_beforeRun()
                self.call_run()
                self.afterRun()

    def afterRun(self):
        if self.getTask():
            self.getTask().routineFinished()
        sysprint("Running Routine: %s" %(self.__class__.__name__))

    def call_beforeRun_fromC(self):
        res = self.call_beforeRun()
        return res

    def call_beforeRun(self):
        try:
            rollback() #para que inicie una nueva transaccion
            res = self.beforeRun()
            return res
        except Exception, e:
            rollback()

    def call_run_fromC(self):
        try:
            res = self.call_run()
            return res
        except Exception, e:
            rollback()

    def call_run(self):
        try:
            rollback() #para que inicie una nueva transaccion
            res = self.run()
            commit()
            return res
        except Exception, e:
            rollback()

    def defaults(self, *args, **kwargs):
        pass

    def beforeRun(self):
        #este metodo se corre siempre en foreground
        pass

    def run(self):
        pass

    def currentWindow(self):
        pass
