import os
import difflib
from cache import cache
from parse import parseSettingsXML, parseRecordXML, parseRecordRowName, parseWindowRecordName
from pyparse import parseScript

defaultAttributes = ["rowNr"]
defaultMethods = ["forceDelete", "afterCopy", "printDocument"]

@cache.store
def getPlayeroPath():
    import ConfigParser
    try:
        config = ConfigParser.SafeConfigParser()
        config.read("config/playero.cfg")
        res = config.get('paths', os.name)
    except ConfigParser.NoSectionError:
        res = "e:/Develop/desarrollo/python/ancho/workspace/Playero/"
        if (os.name == "posix"):
            res = "/home/ancho/Develop/Playero/"
    return res

__playeroPath__ = getPlayeroPath()

@cache.store
def getScriptDirs(level=255):
    settingsFile = __playeroPath__+"settings/settings.xml"
    dh = parseSettingsXML(settingsFile)
    res = dh.scriptdirs[:level+1]
    res.reverse()
    return res

@cache.store
def getRecordsInfo(modulename, extensions=".record.xml"):
    fields = {}
    details = {}
    paths = findPaths(modulename, extensions)
    for level in paths:
        fullpath = paths[level]['fullpath']
        recordname = paths[level]['realname']
        if recordname not in fields:
            fields[recordname] = {}
            details[recordname] = {}
        dh = parseRecordXML(fullpath)
        fields[recordname].update([(fi, dh.fields[fi]) for fi in dh.fields])
        details[recordname].update([(de, dh.details[de]) for de in dh.details])
        inheritance = dh.inheritance
        if not inheritance: inheritance = "Record"
        heirFields, heirDetails = getRecordInheritance(inheritance)
        fields[recordname].update(heirFields)
        details[recordname].update(heirDetails)
    return (fields, details)

@cache.store
def getRecordInheritance(inheritance):
    """Recursive search of inheritance"""
    fields = {}
    details = {}
    paths = findPaths(inheritance)
    if not paths: return fields
    for level in paths:
        fullpath = paths[level]["fullpath"]
        dh = parseRecordXML(fullpath)
        fields.update([(fi, dh.fields[fi]) for fi in dh.fields])
        details.update([(de, dh.details[de]) for de in dh.details])
        inheritance = dh.inheritance
    if not inheritance: inheritance = "Record"
    if inheritance != "RawRecord":
        heirFields, heirDetails = getRecordInheritance(inheritance)
        fields.update(heirFields)
        details.update(heirDetails)
    return (fields, details)

@cache.store
def findPaths(name, extensions=".record.xml", instant=False):
    paths = {}
    if not name: return paths
    level = 0 #to keep order
    tupledExtensions = tuple(extensions.split(","))
    nalo = ["%s%s" % (name.lower(), ext) for ext in tupledExtensions]
    searchType = ["exact","percent"]
    for passType in searchType:
        if paths and passType == "percent": continue #if I have paths there is no need to do a percent match
        for sd in getScriptDirs(255):
            interfacePath = os.path.join(__playeroPath__, sd, "interface")
            if os.path.exists(interfacePath):
                for filename in [f for f in os.listdir(interfacePath) if f.endswith(tupledExtensions)]:
                    filo = filename.lower()
                    if passType == "exact":
                        if filo in nalo:
                            uniquePath = os.path.join(__playeroPath__, sd, "interface", filename)
                            if filename.endswith(".window.xml"):
                                dh = parseWindowRecordName(uniquePath)
                                uniquePath = os.path.join(__playeroPath__, sd, "interface", "%s.record.xml" % dh.name)
                                if not os.path.exists(uniquePath): #a window redef but no record
                                    path = findPaths(dh.name, extensions=".record.xml", instant=True)
                                    uniquePath = path[0]["fullpath"]
                            paths[level] = {"fullpath":uniquePath, "realname":filename.split('.')[0]}
                            level += 1
                            if instant: break
                    elif passType == "percent" and name not in ("Routine","Report") and name.lower().endswith("row"):
                        for namelower in nalo:
                            matchpercent = difflib.SequenceMatcher(isjunk=lambda x: x in tupledExtensions,
                                                                    a=filo,
                                                                    b=namelower
                                                                ).ratio()
                            if matchpercent > 0.91:
                                uniquePath = os.path.join(__playeroPath__, sd, "interface", filename)
                                dh = parseRecordRowName(uniquePath)
                                if name == dh.name:
                                    paths[level] = {"fullpath":uniquePath, "realname": dh.name}
                                    level += 1

    if not paths:
        for coremodule in (x for x in ("User","LoginDialog") if x == name):
            filename = "%s.record.xml" % coremodule
            userpath = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), "corexml", filename))
            paths = {0:{"fullpath":userpath, "realname":filename.split('.')[0]}}
    return paths

def getFullPaths(extraDirs):
    return [os.path.join(__playeroPath__, x, y) for x in getScriptDirs(255) for y in extraDirs]

@cache.store
def getClassInfo(modulename, parent=""):
    attributes, methods, inheritance = set(), set(), {}
    paths = getFullPaths(extraDirs=["records", "windows", "tools", "routines", "documents", "reports"])
    paths.append(os.path.join(__playeroPath__,"core"))
    searchInList = [modulename]
    if parent and parent != modulename:
        searchInList.append(parent)
    for path in paths:
        if os.path.exists(path):
            for filename in [f for f in os.listdir(path) if f.endswith(".py") and f.split(".py")[0] in searchInList]:
                fullfilepath = os.path.join(path, filename)
                parse = parseScript(fullfilepath)
                attributes.update(x for x in parse.attributes)
                methods.update(x for x in parse.methods)
                inheritance = parse.inheritance
    if modulename in inheritance:
        heir = inheritance[modulename]
        if not heir: heir = "Master"
        heirattr, heirmeths = getClassInfo(heir)
        attributes.update(x for x in heirattr)
        methods.update(x for x in heirmeths)
    if parent not in ("Report","Routine"):
        attributes.update(x for x in defaultAttributes)
        methods.update(x for x in defaultMethods)
    methods = sorted(methods)
    attributes = sorted(attributes)
    return (attributes, methods)

def logHere(value, filename="log.log"):
    HERE = os.path.dirname(os.path.abspath(__file__))
    logfile = os.path.join(HERE, 'logs', filename)
    f = file(logfile, "a")
    f.write("%s\n" % str(value))

def getModName(modname):
    if modname.find(".")>-1:
        modname = modname.split(".")[-1:][0] #extra.StdPy.records.Delivery -> Delivery
    if modname.endswith("Window"):
        modname = modname.split("Window")[0]
    return modname

def ifElse(condition, trueVal, falseVal):
    res = falseVal
    if isinstance(condition, str):
        condition = ifElse(len(condition.strip()), condition, "")
    if condition: res = trueVal
    return res

if __name__ == "__main__":
    ok =  ["PayMode", "CredCardType"] #lineending failure
    ok += ["Invoice", "PySettings", "AccountSettings", "Cheque"]
    ok += ["CreditCard", "Bank", "GasStationSettings", "SerNrControl", "User", "Coupon", "SLRetencionDoc", "SLRetencionDocWindow", "Retencion"]
    ok += ["Transaction", "ContactWay"]
    for b in ok:
        print "     processing", b
        attr, meth = getClassInfo(b)
        for at in attr:
            print at
        for mt in meth:
            print mt

