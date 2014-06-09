from xml.sax import handler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces
from xml.sax._exceptions import SAXParseException

###RECORD###

def parseRecordXML(filename):
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    dh = XMLRecordHandler()
    parser.setContentHandler(dh)
    parser.parse(open(filename, "r"))
    return dh

class XMLRecordHandler(handler.ContentHandler):

    def __init__(self):
        self.fields = {}
        self.details = {}
        self.isPersistent = True
        self.inheritance = ""
        self.name = ""

    def startElement(self, name, attrs):
        if name.lower() not in ("record", "detailrecord", "reportwindow", "routinewindow"):
            if attrs.has_key("name"):
                fieldname = str(attrs.get("name",""))
                fieldtype = str(attrs.get("type"))
                self.fields[fieldname] = fieldtype
                if fieldtype == "detail":
                    self.details[fieldname] = str(attrs.get("recordname"))
        else:
            if attrs.has_key("inherits"):
                self.inheritance = str(attrs.get("inherits"))
            if attrs.has_key("persistent"):
                self.isPersistent = bool(attrs.get("persistent"))
            if attrs.has_key("name"):
                self.name = str(attrs.get("name"))

    def endElement(self, name):
        pass

def parseRecordRowName(filename):
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    dh = XMLRecordRowHandler()
    parser.setContentHandler(dh)
    parser.parse(open(filename, "r"))
    return dh

class XMLRecordRowHandler(handler.ContentHandler):
    def __init__(self):
        self.name = ""
    def startElement(self, name, attrs):
        if name.lower() == "detailrecord":
            self.name = str(attrs.get("name"))

###WINDOW###
def parseWindowRecordName(filename):
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    dh = XMLWindowRecordNameHandler()
    parser.setContentHandler(dh)
    openedfile = open(filename, "r")
    try:
        parser.parse(openedfile)
    except SAXParseException:
        if not dh.name:
            fixedfile = reformatXml(openedfile)
            parser.parse(fixedfile)
    openedfile.close()
    return dh

class XMLWindowRecordNameHandler(handler.ContentHandler):
    def __init__(self):
        self.name = ""
    def startElement(self, name, attrs):
        if name.lower() == "window":
            self.name = str(attrs.get("recordname"))

###SETTINGS###
def parseSettingsXML(filename):
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    dh = XMLSettingsHandler()
    parser.setContentHandler(dh)
    parser.parse(open(filename, "r"))
    return dh

class XMLSettingsHandler(handler.ContentHandler):

    def __init__(self):
        self.scriptdirs = []
        self.sd = []
        for i in range(255):
            self.sd.append(None)

    def startElement(self, name, attrs):
        if name == "scriptdir":
            self.sd[int(attrs.get('level', 0))] = self.unicodeToStr(attrs.get('path', None))

    def endDocument(self):
        for i in self.sd:
            if i:
                self.scriptdirs.append(i)

    def unicodeToStr(self, value):
        res = ""
        try:
            res = str(value)
        except:
            res = repr(value)
        return res

def reformatXml(openedfile):
    import re
    readedfile = openedfile.read()
    joinnodes = re.compile(r"\s=\s\"")
    separatenodes = re.compile(r'([a-z]+="[a-z]*")', re.IGNORECASE)
    newread = joinnodes.sub("=\"", readedfile)
    res = re.sub(separatenodes, r' \1', newread)
    import cStringIO
    fileobj = cStringIO.StringIO()
    fileobj.write(res)
    return fileobj
