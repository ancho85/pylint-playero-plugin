import os
import difflib
from cache import cache
from parse import parseSettingsXML, parseRecordXML

__playeroPath__ = "e:/Develop/desarrollo/python/ancho/workspace/Playero/"

@cache.store
def getScriptDirs(level=255):
    settingsFile = __playeroPath__+"settings/settings.xml"
    dh = parseSettingsXML(settingsFile)
    res = dh.scriptdirs[:level+1]
    res.reverse()
    return res

@cache.store
def getRecordsInfo(modulename):
    fields = {}
    details = {}
    paths = findPaths(modulename)
    for level in paths:
        filename = paths[level]['file']
        fullpath = paths[level]['fullpath']
        recordname = filename.split('.')[0]
        if recordname not in fields:
            fields[recordname] = {}
            details[recordname] = {}
        dh = parseRecordXML(fullpath)
        for fi in dh.fields:
            if fi not in fields[recordname]:
                fields[recordname][fi] = dh.fields[fi]
        for de in dh.details:
            if de not in details[recordname]:
                details[recordname][de] = dh.details[de]
        inheritance = dh.inheritance
        while inheritance:
            paths2 = findPaths(inheritance)
            inheritance = ""
            for level2 in paths2:
                fullpath2 = paths2[level2]['fullpath']
                dh = parseRecordXML(fullpath2)
                for fi in dh.fields:
                    if fi not in fields[recordname]:
                        fields[recordname][fi] = dh.fields[fi]
                inheritance = dh.inheritance
    return (fields, details)

@cache.store
def findPaths(name, instant=False):
    paths = {}
    level = 0 #to keep order
    nalo = "%s%s" % (name.lower(), ".record.xml")
    searchType = ["exact","percent"]
    for passType in searchType:
        if paths and passType == "percent": continue #if I have paths there is no need to do a percent match
        for sd in getScriptDirs(255):
            interfacePath = os.path.join(__playeroPath__, sd, "interface")
            if os.path.exists(interfacePath):
                for filename in [f for f in os.listdir(interfacePath) if f.endswith(".record.xml")]:
                    filo = filename.lower()
                    if passType == "exact":
                        if filo == nalo:
                            uniquePath = os.path.join(__playeroPath__, sd, "interface", filename)
                            paths[level] = {"fullpath":uniquePath, "file":filename}
                            level += 1
                            if instant: break
                    elif passType == "percent":
                        idx = 0
                        if len(name)>5: idx=5 #files starting with the same 5 letter
                        if filo[:idx] != nalo[:idx]: continue
                        matchpercent = difflib.SequenceMatcher(None, filo, nalo).ratio()
                        if matchpercent > 0.91:
                            uniquePath = os.path.join(__playeroPath__, sd, "interface", filename)
                            paths[level] = {"fullpath":uniquePath, "file": name + ".record.xml"}
                            level += 1
                            if instant: break
    if not paths:
        for coremodule in (x for x in ("User","LoginDialog") if x == name):
            filename = "%s.record.xml" % coremodule
            userpath = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), "corexml", filename))
            paths = {0:{"fullpath":userpath, "file":filename}}
    return paths

def getFullPaths(extraDir=""):
    paths = []
    res = getScriptDirs(255)
    for x in res:
        newpath = os.path.join(__playeroPath__, x, extraDir)
        paths.append(newpath)
    return paths
