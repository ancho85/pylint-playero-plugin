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
def getRecordsInfo(modulename=""):
    fields = {}
    for sd in getScriptDirs(255):
        interfacePath = os.path.join(__playeroPath__, sd, "interface")
        if os.path.exists(interfacePath):
            for filename in os.listdir(interfacePath):
                if filename.lower().endswith(".record.xml"):
                    recordname = filename.split('.')[0]
                    if modulename and recordname != modulename: continue
                    if recordname not in fields:
                        fields[recordname] = {}
                    filefullpath = os.path.join(__playeroPath__, sd, "interface", filename)
                    dh = parseRecordXML(filefullpath)
                    for fi in dh.fields:
                        if fi not in fields[recordname]:
                            fields[recordname][fi] = dh.fields[fi]
                    inheritance = dh.inheritance
                    while inheritance:
                        filefullpaths = findPaths(inheritance)
                        inheritance = ""
                        for paths in filefullpaths:
                            dh = parseRecordXML(paths)
                            for fi in dh.fields:
                                if fi not in fields[recordname]:
                                    fields[recordname][fi] = dh.fields[fi]
                            inheritance = dh.inheritance
    return fields

def findPaths(name, instant=False):
    filefullpaths = []
    for sd in getScriptDirs(255):
        interfacePath = os.path.join(__playeroPath__, sd, "interface")
        if os.path.exists(interfacePath):
            for filename in os.listdir(interfacePath):
                if filename.lower() == name.lower() + ".record.xml":
                    filefullpaths.append(os.path.join(__playeroPath__, sd, "interface", filename))
                    if instant: break
    return filefullpaths

def getFullPaths(extraDir=""):
    paths = []
    res = getScriptDirs(255)
    for x in res:
        newpath = os.path.join(__playeroPath__, x, extraDir)
        paths.append(newpath)
    return paths
