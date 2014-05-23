import os
import difflib
from cache import cache
from parse import parseSettingsXML, parseRecordXML
from pyparse import parseScript

__playeroPath__ = "e:/Develop/desarrollo/python/ancho/workspace/Playero/"
if (os.name == "posix"):
    __playeroPath__ = "/home/ancho/Develop/Playero/"

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
    if not name: return paths
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

def getFullPaths(extraDirs):
    return [os.path.join(__playeroPath__, x, y) for x in getScriptDirs(255) for y in extraDirs]

@cache.store
def getClassInfo(modulename, parent=""):
    attributes, methods, inheritance = set(), set(), {}
    paths = getFullPaths(extraDirs=["records", "windows", "tools", "routines", "documents", "reports"])
    paths.append(os.path.join(__playeroPath__,"core"))
    for path in paths:
        if os.path.exists(path):
            for filename in [f for f in os.listdir(path) if f.endswith(".py") and f.split(".py")[0] in (modulename, parent)]:
                fullfilepath = os.path.join(path, filename)
                parse = parseScript(fullfilepath)
                [attributes.add(x) for x in parse.attributes]
                [methods.add(x) for x in parse.methods]
                inheritance = parse.inheritance
    if modulename in inheritance:
        heirattr, heirmeths = getClassInfo(inheritance[modulename])
        [attributes.add(x) for x in heirattr]
        [methods.add(x) for x in heirmeths]
    methods.add("forceDelete")
    methods = sorted(methods)
    attributes = sorted(attributes)
    return (attributes, methods)

def logHere(value, filename="log.log"):
    HERE = os.path.dirname(os.path.abspath(__file__))
    logfile = os.path.join(HERE, 'logs',filename)
    f = file(logfile,"a")
    f.write(str(value)+"\n")

if __name__ == "__main__":
    ok =  ["PayMode","CredCardType"] #lineending failure
    ok += ["Invoice", "PySettings","AccountSettings","Cheque"]
    ok += ["CreditCard","Bank","GasStationSettings","SerNrControl","User","Coupon","SLRetencionDoc","SLRetencionDocWindow","Retencion"]
    ok += ["Transaction","ContactWay"]
    ok = ["ValuesIncome"]
    for b in ok:
        print "     processing", b
        attr, meth= getClassInfo(b)
        for at in attr:
            print at
        for mt in meth:
            print mt
