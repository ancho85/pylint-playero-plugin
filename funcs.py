import os
from cache import cache
from parse import parseSettingsXML, parseRecordXML, parseWindowRecordName
from pyparse import parseScript
from tools import logHere
import ConfigParser

RECORD = ".record.xml"
REPORT = ".reportwindow.xml"
ROUTINE = ".routinewindow.xml"
WINDOW = ".window.xml"
EMBCORE = ".py"
reportClasses  = ["Report", "ReportA"]
routineClasses = ["Routine", "RoutineA"]
otherClasses   = ["Window", "WindowA"]
allCoreClasses = reportClasses + routineClasses + otherClasses

def getConfig():
    config = ConfigParser.ConfigParser()
    configLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config", "playero.cfg")
    f = open(configLocation, "r")
    config.readfp(f) #the configuration file can change, so it must be opened every time
    f.close()
    return config

@cache.store
def getPlayeroPath():
    try:
        config = getConfig()
        res = config.get('paths', os.name)
    except ConfigParser.NoSectionError:
        res = "e:/Develop/desarrollo/python/ancho/workspace/Playero/"
        if (os.name == "posix"):
            res = "/home/ancho/Develop/Playero/"
    return res

@cache.store
def getEmbeddedPath():
    try:
        config = getConfig()
        res = config.get('plugin_paths', os.name)
    except ConfigParser.NoSectionError:
        res = "e:/Develop/desarrollo/python/other/pylint-playero-plugin"
        if (os.name == "posix"):
            res = "/home/ancho/Develop/pylint-playero-plugin"
    return res

@cache.store
def getScriptDirs(level=255):
    settingsFile = getPlayeroPath()+"settings/settings.xml"
    dh = parseSettingsXML(settingsFile)
    res = dh.scriptdirs[:level+1]
    res.reverse()
    return res

def buildPaths():
    recPaths, repPaths, rouPaths, winPaths, corePaths = {}, {}, {}, {}, {}
    for coremodule in ("User","LoginDialog"):
        recPaths[coremodule] = {0: str(os.path.join(os.path.dirname(os.path.realpath(__file__)), "corepy", "xml", "%s.record.xml" % coremodule))}

    #for filelist in [os.listdir(ip) for ip in getFullPaths(["interface"]) if os.path.exists(ip)]:

    for sd in getScriptDirs(255):
        interfacePath = os.path.join(getPlayeroPath(), sd, "interface")
        if os.path.exists(interfacePath):
            for filename in os.listdir(interfacePath):
                uniquePath = "%s/%s" % (interfacePath, filename)
                realname = filename.split('.')[0]

                if filename.endswith(RECORD):
                    dicPaths = recPaths
                elif filename.endswith(REPORT):
                    dicPaths = repPaths
                elif filename.endswith(ROUTINE):
                    dicPaths = rouPaths
                elif filename.endswith(WINDOW):
                    dicPaths = winPaths
                else: continue

                if realname not in dicPaths:
                    dicPaths[realname] = {}
                dicPaths[realname].update([(len(dicPaths[realname]), uniquePath)])

    for winname in [windef for windef in winPaths if windef not in recPaths]:
        for wpaths in winPaths[winname].values():
            dh = parseWindowRecordName(wpaths)
            recPaths[winname] = recPaths.get(dh.name)

    for cpth in [os.path.join(getEmbeddedPath(), "corepy", "embedded")]:
        for filename in os.listdir(cpth):
            uniquePath = "%s/%s" % (cpth, filename)
            realname = filename.split('.')[0]
            if filename.endswith(EMBCORE):
                if realname not in corePaths:
                    corePaths[realname] = {}
                corePaths[realname].update([(len(corePaths[realname]), uniquePath)])

    return (recPaths, repPaths, rouPaths, corePaths)

@cache.store
def getRecordsInfo(modulename, extensions=RECORD):
    fields = {}
    details = {}
    paths, pathType = findPaths(modulename)
    if pathType != extensions: return (fields, details)
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
    paths, pathType = findPaths(inheritance)
    if pathType != RECORD or not paths: return (fields, details)
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

__recordPaths__, __reportPaths__, __routinePaths__, __corePaths__ = buildPaths()

@cache.store
def findPaths(name):
    foundPaths, pathType = __recordPaths__.get(name, {}), RECORD
    if not foundPaths:
        foundPaths, pathType = __reportPaths__.get(name, {}), REPORT
    if not foundPaths:
        foundPaths, pathType = __routinePaths__.get(name, {}), ROUTINE
    if not foundPaths:
        foundPaths, pathType = __corePaths__.get(name, {}), EMBCORE
    if not foundPaths: pathType = None
    return (foundPaths, pathType)

def getFullPaths(extraDirs):
    return [os.path.join(getPlayeroPath(), x, y) for x in getScriptDirs(255) for y in extraDirs]

@cache.store
def getClassInfo(modulename, parent=""):
    attributes, methods, inheritance = set(), set(), {}
    paths = getFullPaths(extraDirs=["records", "windows", "tools", "routines", "documents", "reports"])
    paths.append(os.path.join(getPlayeroPath(),"core"))
    paths.append(os.path.join(getEmbeddedPath(), "corepy", "embedded"))
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
    heir = inheritance.get(modulename, inheritance.get(parent, ''))
    if heir:
        heirattr, heirmeths = getClassInfo(heir)
        attributes.update(x for x in heirattr)
        methods.update(x for x in heirmeths)
    if len(methods) == 0 and len(attributes) == 0:
        from tools import filenameFromPath
        foundPath, foundName = findPaths(modulename)
        foundName = filenameFromPath(foundPath.get(0,"")).split(RECORD)[0]
        if foundName != modulename:
            attributes, methods = getClassInfo(foundName)
    methods = sorted(methods)
    attributes = sorted(attributes)
    return (attributes, methods)

def getModName(modname):
    if modname.find(".")>-1:
        modname = modname.split(".")[-1:][0] #extra.StdPy.records.Delivery -> Delivery
    if modname.endswith("Window") and modname != "Window":
        modname = modname.split("Window")[0]
    if modname.find("_")>-1:
        embpath = os.path.join(getEmbeddedPath(), "corepy", "embedded")
        corePath = False
        for _ in [f for f in os.listdir(embpath) if f.split(".py")[0] == modname]:
            corePath = True
        if not corePath:
            modname = None
    return modname

def ifElse(condition, trueVal, falseVal):
    res = falseVal
    if isinstance(condition, str):
        condition = ifElse(len(condition.strip()), condition, "")
    if condition: res = trueVal
    return res

def inspectModule(module, inspectValue="module", filename="inspect.log"):
    """inspects module functions. Ex: inspectValue='module.body[0].parent.name' """
    modname = module
    if hasattr(module, "name"):
        modname = getModName(module.name)
    if True:
        exe =  """logHere('Inspecting', '%s --> %s', type(%s), filename='%s')\n""" % (modname, inspectValue, inspectValue, filename)
        exe += """for x in [x for x in sorted(dir(%s)) if not x.startswith('_')]: \n""" % inspectValue
        exe += """    exec("xdir = type(%s.%%s)" %% x) \n""" % inspectValue
        exe += """    logHere(x, '----->', xdir, filename='%s')\n""" % filename
        exe += """    res = False\n"""
        exe += """    exec("res = callable(%s.%%s)" %% x) \n""" % inspectValue
        exe += """    if res:\n"""
        exe += """        try:\n"""
        exe += """            exec("funccall = %s.%%s()" %% x)\n""" % inspectValue
        exe += """            exec('funcname = \"----> function call %s\" % x')\n"""
        exe += """            import types\n"""
        exe += """            if isinstance(funccall, types.GeneratorType):\n"""
        exe += """                funcname += " GENERATOR"\n"""
        exe += """                funccall = [x for x in funccall]\n"""
        exe += """            logHere(funcname, 'VALUE:', funccall, filename='%s') \n""" % filename
        exe += """        except:\n"""
        exe += """            import inspect\n"""
        exe += """            exec("funcparameters = inspect.getargspec(%s.%%s)" %% x)\n""" % inspectValue
        exe += """            logHere('---->funcall %%s missing parameters: %%s' %% (x, funcparameters), filename='%s')\n""" % filename
        exe += """    else:\n"""
        exe += """        exec("logHere(('---->value %%s', %s.%%s), filename='%s')" %% (x,x))\n""" % (inspectValue, filename)
        exe += """    logHere("", filename='%s', whitespace=1)""" % filename
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
