from xml.sax import handler
from tools import latinToAscii

###RECORD###

def parseRecordXML(filename):
    from xml.sax import make_parser
    from xml.sax.handler import feature_namespaces
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    dh = XMLRecordHandler()
    parser.setContentHandler(dh)
    parser.parse(open(filename))
    return dh

class XMLRecordHandler(handler.ContentHandler):

    def __init__(self):
        self.fields = {}
        self.periods = {}
        self.periodsSubFields = []
        self.comboradioFieldName = ""
        self.comboradioLabel = ""
        self.comboradio = {}

    def startElement(self, name, attrs):
        hasFieldName = False
        if attrs.has_key("fieldname"):
            fieldname = str(attrs.get("fieldname",""))
            label = tr(latinToAscii(attrs.get("label")))
            hasFieldName = True
        if name in ("radiobutton","combobox"):
            self.comboradio[fieldname] = {}
            self.comboradioFieldName = fieldname
            self.comboradioLabel = tr(latinToAscii(attrs.get("label")))
        elif name == "radiooption":
            value = str(attrs.get("value"))
            self.comboradio[self.comboradioFieldName][value] = tr(latinToAscii(attrs.get("label")))
            self.comboradio[self.comboradioFieldName]["label"] = self.comboradioLabel
        elif name == "combooption":
            value = str(attrs.get("value"))
            self.comboradio[self.comboradioFieldName][value] = tr(latinToAscii(attrs.get("label")))
            self.comboradio[self.comboradioFieldName]["label"] = self.comboradioLabel
        elif name == "checkbox":
            self.fields[fieldname] = {'label': label, 'value':fieldname}
        else:
            if hasFieldName:
                self.fields[fieldname] = {'label': label, 'value':None}
        if name == "period":
            fromfieldname = str(attrs.get("fromfieldname",""))
            tofieldname = str(attrs.get("tofieldname",""))
            self.periods[fromfieldname] = {}
            self.periods[fromfieldname][tofieldname] = tr(latinToAscii(attrs.get("label")))
            self.periodsSubFields.append(tofieldname)


    def endElement(self, name):
        if name in ("radiobutton", "combobox"):
            self.comboradioFieldName = ""
            self.comboradioLabel = ""
