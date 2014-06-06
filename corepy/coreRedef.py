#encoding: UTF-8
import core.modulesIndex
from functions import *
from cache import cache

import os
root_path = os.getcwd()
modulesindex = core.modulesIndex.getClassesIndex(getScriptDirs())

@cache.store
def getWindowsInfo():
    minfo = {}
    for sd in getScriptDirs(999):
        d = os.path.join(sd, "interface")
        if not os.path.exists(d):
            continue
        for d in os.listdir(d):
            if d.lower().endswith(".window.xml"):
                recordname = d.split('.')[0]
                windowname = recordname + "Window"
                minfo[windowname] = {
                    "RecordName": recordname,
                    "Title": recordname
                }
    return minfo


@cache.store
def getModulesInfo():

    def trtry(msg):
        res = msg
        try:
            res = tr(msg)
        except UnicodeEncodeError:
            from GeneralPyTools import latinToAscii
            res = latinToAscii(msg)
        except Exception:
            res = repr(msg)
        return res

    from xml.sax import make_parser, handler

    class ModuleHandler(handler.ContentHandler):

        #pylint: disable=W0231
        def __init__(self):
            self.name = ""
            self.label = ""
            self.entries = {"Records": [], "Reports": [], "Routines": [], "Settings": []}

        def startElement(self, name, attrs):
            if name == "module":
                self.name = attrs["name"]
                self.label = attrs["label"]
            if name == "recordentry":
                self.entries["Records"].append({"Image": attrs.get("image", ""), "Name": attrs.get("name", ""), "Label": trtry(attrs.get("label", ""))})
            if name == "reportentry":
                self.entries["Reports"].append({"Image": attrs.get("image", ""), "Name": attrs.get("name", ""), "Label": trtry(attrs.get("label", ""))})
            if name == "routineentry":
                self.entries["Routines"].append({"Image": attrs.get("image", ""), "Name": attrs.get("name", ""), "Label": trtry(attrs.get("label", ""))})
            if name == "settingentry":
                self.entries["Settings"].append({"Image": attrs.get("image", ""), "Name": attrs.get("name", ""), "Label": trtry(attrs.get("label", ""))})

        def endElement(self, name):
            pass

        def characters(self, data):
            pass
    minfo = {}
    for sd in getScriptDirs(999999):
        d = os.path.join(sd, "interface")
        if not os.path.exists(d):
            continue
        for d in os.listdir(d):
            if d.lower().endswith(".module.xml"):
                parser = make_parser()
                parser.setFeature(handler.feature_namespaces, 0)
                xmlhandler = ModuleHandler()
                parser.setContentHandler(xmlhandler)
                parser.parse(open(os.path.join(sd, "interface", d), "rb"))
                if xmlhandler.name in minfo.keys():
                    minfo[xmlhandler.name]["Label"] = trtry(xmlhandler.label)
                    for r in xmlhandler.entries["Records"]:
                        if r["Name"] not in [x["Name"] for x in minfo[xmlhandler.name]["Records"]]:
                            minfo[xmlhandler.name]["Records"].append(r)
                    for r in xmlhandler.entries["Reports"]:
                        if r["Name"] not in [x["Name"] for x in minfo[xmlhandler.name]["Reports"]]:
                            minfo[xmlhandler.name]["Reports"].append(r)
                    for r in xmlhandler.entries["Routines"]:
                        if r["Name"] not in [x["Name"] for x in minfo[xmlhandler.name]["Routines"]]:
                            minfo[xmlhandler.name]["Routines"].append(r)
                    for r in xmlhandler.entries["Settings"]:
                        if r["Name"] not in [x["Name"] for x in minfo[xmlhandler.name]["Settings"]]:
                            minfo[xmlhandler.name]["Settings"].append(r)
                else:
                    minfo[xmlhandler.name] = {
                        "Code": xmlhandler.name,
                        "Label": trtry(xmlhandler.label),
                        "Records": xmlhandler.entries["Records"],
                        "Reports": xmlhandler.entries["Reports"],
                        "Routines": xmlhandler.entries["Routines"],
                        "Settings": xmlhandler.entries["Settings"]
                        }
    return minfo
