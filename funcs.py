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
def getRecordsInfo():
    fields = {}
    for sd in getScriptDirs(255):
        interfacePath = os.path.join(__playeroPath__, sd, "interface")
        if os.path.exists(interfacePath):
            for filename in os.listdir(interfacePath):
                if filename.lower().endswith(".record.xml"):
                    recordname = filename.split('.')[0]
                    fields[recordname] = {}
                    filefullpath = os.path.join(__playeroPath__, sd, "interface", filename)
                    dh = parseRecordXML(filefullpath)
                    for fi in dh.fields:
                        fields[recordname][fi] = dh.fields[fi]
                    inheritance = dh.inheritance

                    while inheritance:
                        filefullpaths = findInheritancePath(inheritance)
                        inheritance = ""
                        for paths in filefullpaths:
                            dh = parseRecordXML(paths)
                            for fi in dh.fields:
                                fields[recordname][fi] = dh.fields[fi]
                            inheritance = dh.inheritance
    return fields

def findInheritancePath(name):
    filefullpaths = []
    for sd in getScriptDirs(255):
        interfacePath = os.path.join(__playeroPath__, sd, "interface")
        if os.path.exists(interfacePath):
            for filename in os.listdir(interfacePath):
                if filename.lower() == name.lower() + ".record.xml":
                    filefullpaths.append(os.path.join(__playeroPath__, sd, "interface", filename))
    return filefullpaths

def getFullPaths():
    paths = []
    res = getScriptDirs(255)
    for x in res:
        newpath = __playeroPath__+x
        paths.append(newpath)
    return paths
