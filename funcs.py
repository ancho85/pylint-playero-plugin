import os
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

def findPaths(name, instant=False):
    paths = {}
    level = 0 #to keep order
    for sd in getScriptDirs(255):
        interfacePath = os.path.join(__playeroPath__, sd, "interface")
        if os.path.exists(interfacePath):
            for filename in os.listdir(interfacePath):
                if filename.lower() == name.lower() + ".record.xml":
                    uniquePath = os.path.join(__playeroPath__, sd, "interface", filename)
                    paths[level] = {"fullpath":uniquePath,"file":filename}
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
