from xml.sax import handler
from xml.sax import make_parser, parseString
from xml.sax.handler import feature_namespaces
from xml.sax._exceptions import SAXParseException

###RECORD###

def parseRecordXML(filename):
    dh = XMLRecordHandler()
    try:
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        parser.setContentHandler(dh)
        parser.parse(open(filename, "r"))
    except SAXParseException:
        fixedTxt = reformatXml(filename)
        parseString(fixedTxt, dh)
    return dh

class XMLRecordHandler(handler.ContentHandler):

    def __init__(self):
        self.fields = {}
        self.details = {}
        self.isPersistent = True
        self.inheritance = ""
        self.name = ""

    def startElement(self, name, attrs):
        if name.lower() not in ("record", "detailrecord", "reportwindow", "routinewindow", "index", "indexfield"):
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
                self.isPersistent = attrs.get("persistent").lower() == "true"
            if attrs.has_key("name"):
                self.name = str(attrs.get("name"))

    def endElement(self, name):
        pass

def parseRecordRowName(filename):
    dh = XMLRecordRowHandler()
    try:
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        parser.setContentHandler(dh)
        parser.parse(open(filename, "r"))
    except SAXParseException:
        fixedTxt = reformatXml(filename)
        parseString(fixedTxt, dh)
    return dh

class XMLRecordRowHandler(handler.ContentHandler):
    def __init__(self):
        self.name = ""
    def startElement(self, name, attrs):
        if name.lower() == "detailrecord":
            self.name = str(attrs.get("name"))

###WINDOW###
def parseWindowRecordName(filename):
    dh = XMLWindowRecordNameHandler()
    try:
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        parser.setContentHandler(dh)
        parser.parse(open(filename, "r"))
    except SAXParseException:
        if not dh.name:
            fixedTxt = reformatXml(filename)
            parseString(fixedTxt, dh)
    return dh

class XMLWindowRecordNameHandler(handler.ContentHandler):
    def __init__(self):
        self.name = ""
    def startElement(self, name, attrs):
        if name.lower() == "window":
            self.name = str(attrs.get("recordname"))

###SETTINGS###
def parseSettingsXML(filename):
    dh = XMLSettingsHandler()
    try:
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        parser.setContentHandler(dh)
        parser.parse(open(filename, "r"))
    except SAXParseException:
        fixedTxt = reformatXml(filename)
        parseString(fixedTxt, dh)
    return dh

class XMLSettingsHandler(handler.ContentHandler):

    def __init__(self):
        self.scriptdirs = []
        self.sd = []
        for _ in range(255):
            self.sd.append(None)

    def startElement(self, name, attrs):
        if name == "scriptdir":
            self.sd[int(attrs.get('level', 0))] = str(attrs.get('path', None))

    def endDocument(self):
        for i in self.sd:
            if i:
                self.scriptdirs.append(i)

def reformatXml(filename):
    openedfile = open(filename, "r")
    import re
    from libs.tools import latinToAscii
    readedfile = openedfile.read()
    joinnodes = re.compile(r"\s=\s\"")
    separatenodes = re.compile(r'([a-z]+="[a-z]*")', re.IGNORECASE)
    newread = joinnodes.sub("=\"", readedfile)
    res = re.sub(separatenodes, r' \1', newread)
    res = latinToAscii(res)
    openedfile.close()
    return res
