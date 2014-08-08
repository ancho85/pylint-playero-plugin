import sys

from xml.sax import make_parser, handler
from RecordDef import RecordDef, DetailRecordDef
from FieldDef import FieldDef
from IndexDef import IndexDef, IndexFieldDef
#from ReportUserInput import ReportUserInput

class XMLHandler(handler.ContentHandler):
    ElementClasses = {"reportrecord": RecordDef, "routinerecord": RecordDef, "record": RecordDef, "detailrecord": DetailRecordDef, "field": FieldDef, "index": IndexDef, "indexfield": IndexFieldDef}
    def __init__(self):
        self.elements = []
        self.parent = None
        self.result = None

    def startElement(self, name, attrs):
        cls = XMLHandler.ElementClasses.get(name, None)
        if cls:
            element = cls()
            self.elements.append(element)
            element.parse(self.parent, attrs)
            self.afterParseElement(element)
            self.parent = element
        else:
            self.elements.append(None)
            self.parent = None

    def afterParseElement(self, element):
        pass

    def endElement(self, name):
        self.result = self.elements.pop()
        try:
            self.parent = self.elements[-1]
        except:
            self.parent = None

    def getResult(self):
        return self.result


class ReportUserInputXMLHandler(XMLHandler):

    def __init__(self):
        XMLHandler.__init__(self)
        self.recorddef = None

    def afterParseElement(self, element):
        pass

    def endElement(self, name):
        if name=="reportrecord":
            self.recorddef = self.elements[-1]
        return XMLHandler.endElement(self, name)

    def getResult(self):
        return self.recorddef

class RoutineUserInputXMLHandler(XMLHandler):

    def __init__(self):
        XMLHandler.__init__(self)
        self.recorddef = None

    def afterParseElement(self, element):
        pass

    def endElement(self, name):
        if name=="routinerecord":
            self.recorddef = self.elements[-1]
        return XMLHandler.endElement(self, name)

    def getResult(self):
        return self.recorddef

class XMLParser(object):

    @classmethod
    def parseReportUserInput(objclass, reportname):
        import os
        from globalfunctions import getScriptDirs
        for sd in getScriptDirs():
            fullfn = os.path.join(sd, "interface", reportname + ".reportwindow.xml")
            if os.path.exists(fullfn):
                return XMLParser.parse(fullfn, ReportUserInputXMLHandler)

    @classmethod
    def parseRoutineUserInput(objclass, reportname):
        import os
        from globalfunctions import getScriptDirs
        for sd in getScriptDirs():
            fullfn = os.path.join(sd, "interface", reportname + ".routinewindow.xml")
            if os.path.exists(fullfn):
                return XMLParser.parse(fullfn, RoutineUserInputXMLHandler)

    @classmethod
    def parse(objclass, filename, handlerclass = XMLHandler):
        parser = make_parser()
        handler = handlerclass()
        parser.setContentHandler(handler)
        parser.parse(filename)
        return handler.getResult()

    @classmethod
    def loadRecordDefinitions(objclass):
        import os
        path = os.path.join("server", "interface")
        for fn in os.listdir(path):
            if fn.lower().endswith(".record.xml"):
                XMLParser.parse(os.path.join(path, fn))

        from globalfunctions import getScriptDirs
        for sd in getScriptDirs():
            path = os.path.join(sd, "interface")
            if not os.path.isdir(path): continue
            for fn in os.listdir(path):
                if fn.lower().endswith(".record.xml"):
                    XMLParser.parse(os.path.join(path, fn))

        from globalfunctions import getClassesIndex

        ci = getClassesIndex(reversed(getScriptDirs()))



        from RecordDef import RecordDef
        from globalfunctions import createRecordModuleAndClass
        for rdefs in RecordDef.instances.values():
            if not ci.has_key(rdefs[0].name):
                createRecordModuleAndClass(str(rdefs[0].name), None)


        record_recorddef = RecordDef()
        record_recorddef.name = "RawRecord"
        record_recorddef.tablename = "RawRecord"
        record_recorddef.inherits = "Embedded_Record"
        record_recorddef.is_persistent = False
        RecordDef.instances["RawRecord"] = [record_recorddef]
        record_recorddef = RecordDef()
        record_recorddef.name = "Embedded_Record"
        record_recorddef.tablename = "Embedded_Record"
        record_recorddef.inherits = ""
        record_recorddef.is_persistent = False
        RecordDef.instances["Embedded_Record"] = [record_recorddef]

        RecordDef.composeAll()

