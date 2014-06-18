import os
from cache import cache
from parse import parseSettingsXML, parseRecordXML, parseRecordRowName, parseWindowRecordName
from pyparse import parseScript

defaultAttributes = ["rowNr"]
defaultMethods = ["forceDelete", "afterCopy", "printDocument", "afterDelete"]
RECORD = ".record.xml"
REPORT = ".reportwindow.xml"
ROUTINE = ".routinewindow.xml"
WINDOW = ".window.xml"

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

def buildPaths():
    recPaths, repPaths, rouPaths = {}, {}, {}
    for coremodule in ("User","LoginDialog"):
        recPaths[coremodule] = {0: str(os.path.join(os.path.dirname(os.path.realpath(__file__)), "corexml", "%s.record.xml" % coremodule))}

    for sd in getScriptDirs(255):
        interfacePath = os.path.join(__playeroPath__, sd, "interface")
        if os.path.exists(interfacePath):
            for filename in os.listdir(interfacePath):
                uniquePath = os.path.join(__playeroPath__, sd, "interface", filename)
                realname = filename.split('.')[0]

                if filename.endswith(RECORD):
                    dicPaths = recPaths
                elif filename.endswith(REPORT):
                    dicPaths = repPaths
                elif filename.endswith(ROUTINE):
                    dicPaths = rouPaths

                if realname not in dicPaths:
                    dicPaths[realname] = {}
                dicPaths[realname].update([(len(dicPaths[realname]), uniquePath)])

                if id(dicPaths) == id(recPaths) and realname.endswith("Row"):
                    dh = parseRecordRowName(uniquePath)
                    if dh.name not in dicPaths:
                        dicPaths[dh.name] = {0: uniquePath}
    return (recPaths, repPaths, rouPaths)

def buildWindowPaths(recPaths):
    for sd in getScriptDirs(255):
        interfacePath = os.path.join(__playeroPath__, sd, "interface")
        if os.path.exists(interfacePath):
            for filename in [f for f in os.listdir(interfacePath) if f.endswith(WINDOW)]:
                realname = filename.split('.')[0]
                if realname not in recPaths:
                    uniquePath = os.path.join(__playeroPath__, sd, "interface", filename)
                    dh = parseWindowRecordName(uniquePath)
                    recPaths[realname] = recPaths.get(dh.name)
    return recPaths

@cache.store
def getRecordsInfo(modulename, extensions=RECORD):
    fields = {}
    details = {}
    paths = findPaths(modulename, extensions)
    for level in paths:
        fullpath = paths[level]
        recordname = modulename
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
    paths = findPaths(inheritance, extensions=RECORD)
    if not paths: return (fields, details)
    for level in paths:
        fullpath = paths[level]
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

__recordPaths__, __reportPaths__, __routinePaths__ = buildPaths()
__windowPaths__ = buildWindowPaths(__recordPaths__)

@cache.store
def findPaths(name, extensions=RECORD):
    foundPaths = {}
    if extensions == RECORD:
        foundPaths = __recordPaths__.get(name, {})
        if not foundPaths:
            foundPaths = __windowPaths__.get(name, {})
    elif extensions == REPORT:
        foundPaths = __reportPaths__.get(name, {})
    elif extensions == ROUTINE:
        foundPaths = __routinePaths__.get(name, {})
    return foundPaths

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

def inspectModule(module, inspectName, inspectValue):
    """inspects module functions. Ex: inspectName='DelTransaction', inspectValue='module.body[0].parent.name' """
    modname = getModName(module.name)
    if modname == inspectName:
        logHere("Inspecting %s --> %s" % (modname, inspectValue))
        exe =  """for x in [x for x in sorted(dir(%s)) if not x.startswith('_')]: \n""" % inspectValue
        exe += """    exec("xdir = dir(%s.%%s)" %% x) \n""" % inspectValue
        exe += """    logHere((x, '----->', xdir))\n"""
        exe += """    res = False\n"""
        exe += """    exec("res = callable(%s.%%s)" %% x) \n""" % inspectValue
        exe += """    if res:\n"""
        exe += """        try:\n"""
        exe += """            exec("funccall = %s.%%s()" %% x)\n""" % inspectValue
        exe += """            exec('funcname = \"----> function call %s\" % x')\n"""
        exe += """            logHere((funcname, 'VALUE:', funccall)) \n"""
        exe += """        except:\n"""
        exe += """            logHere('---->funcall %s missing parameters' % x)\n"""
        exe += """    else:\n"""
        exe += """        exec("logHere(('---->value %%s', %s.%%s))" %% (x,x))\n""" % inspectValue
        exe += """    logHere("\\n\\n")"""
        exec(exe)


if __name__ == "__main__":
    """ok =  ["PayMode", "CredCardType"] #lineending failure
    ok += ["Invoice", "PySettings", "AccountSettings", "Cheque"]
    ok += ["CreditCard", "Bank", "GasStationSettings", "SerNrControl", "User", "Coupon", "SLRetencionDoc", "SLRetencionDocWindow", "Retencion"]
    ok += ["Transaction", "ContactWay"]
    for b in ok:
        print "     processing", b
        attr, meth = getClassInfo(b)
        for at in attr:
            print at
        for mt in meth:
            print mt"""
    recPaths, repPaths, rouPaths = buildPaths()
    for mod in sorted(recPaths):
        print mod
        for level in recPaths[mod]:
            print "--->", level, recPaths[mod][level]

