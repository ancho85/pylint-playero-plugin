from astroid import MANAGER
from astroid.builder import AstroidBuilder
from libs.funcs import *
from libs.tools import hashIt, xmlValue


notFound = set()

def classes_transform(module):
    modname = getModName(module.name)
    if not modname: return
    if modname in notFound: return
    paths, pathType = findPaths(modname)
    if paths or pathType:
        found = False
        if pathType == RECORD:
            found = buildRecordModule(module)
        elif pathType == REPORT:
            found = buildReportModule(module)
        elif pathType == ROUTINE:
            found = buildRoutineModule(module)
        if not found: notFound.add(modname)
    elif modname.endswith("Doc"):
        found = buildDocumentModule(module)
    elif modname in allCoreClasses:
        baseClassBuilder(module, modname)
    else:
        notFound.add(modname)

###classes_transform_methods###
def buildRecordModule(module):
    modname = getModName(module.name)
    records = getRecordsInfo(modname, RECORD)[0]
    if modname not in records: return
    xmlfields = records.get(modname, {})
    for fields in xmlfields:
        if records[modname][fields] == "detail":
            module.locals[fields] = buildIterator(modname, fields)
        else:
            module.locals[fields] = records[modname][fields]
    attributes, methods = getClassInfo(modname, getModName(module.parent.name))

    for insBuilder in ("bring", "getMasterRecord", "load", "getRecord"):
        module.locals[insBuilder] = buildInstantiator(modname, insBuilder, hashIt((xmlfields, attributes, methods)))

    module.locals.update([(attrs, {0:attributes[attrs]}) for attrs in attributes if not attrs.startswith("_") and attrs not in module.locals])
    methodTextDic = methodTextBuilder(hashIt(methods))
    module.locals.update([(meths, buildMethod(meths, methodTextDic[meths])) for meths in methodTextDic if meths not in module.locals])
    return True

def buildReportModule(module):
    return genericBuilder(module, "Report")

def buildRoutineModule(module):
    return genericBuilder(module, "Routine")

def buildDocumentModule(module):
    return genericBuilder(module, "Document")

def genericBuilder(module, buildIdx):
    res = False
    buildType = {
                "Document": [RECORD, ".documents."],
                "Report"  : [REPORT, ".reports."],
                "Routine" : [ROUTINE,".routines."]
    }
    if buildIdx not in buildType: return res
    ext = buildType[buildIdx][0]
    #cls = buildType[buildIdx][1]
    modname = getModName(module.name)
    if buildIdx == "Document":
        modname = modname.split("Doc")[0]
    classtype = module.basenames[0]
    records = getRecordsInfo(modname, extensions=ext)[0]
    xmlfields = records.get(modname, {})
    attributes, methods = getClassInfo(modname, parent=classtype)
    module.locals["getRecord"] = buildInstantiator(modname, "getRecord", hashIt((xmlfields, attributes, methods)))
    if any([xmlfields, attributes, methods]):
        res = True
    return res

def baseClassBuilder(module, baseclass):
    xmlfields = {}
    if baseclass in reportClasses:
        records = getRecordsInfo("Transaction", extensions=RECORD)[0]
        xmlfields = records.get("Transaction", {})
        attributes, methods = getClassInfo("Embedded_Report", parent="Embedded_Record")
    elif baseclass in routineClasses:
        attributes, methods = getClassInfo("Embedded_Routine", parent="Embedded_Record")
    elif baseclass in otherClasses:
        attributes, methods = getClassInfo("Embedded_Window", parent="Embedded_Record")
    methodTextDic = methodTextBuilder(hashIt(methods))
    module.locals.update([(meths, buildMethod(meths, methodTextDic[meths])) for meths in methodTextDic if meths not in module.locals])
    module.locals.update([(attr, {0:attributes[attr]}) for attr in attributes if attr not in module.locals])
    module.locals["getRecord"] = buildInstantiator(baseclass, "getRecord", hashIt((xmlfields, attributes, methods)))


def buildIterator(modname, detailfield):
    fake = AstroidBuilder(MANAGER).string_build(getIteratorString(modname, detailfield))
    return fake.locals[detailfield]

@cache.store
def getIteratorString(modname, detailfield):
    details = getRecordsInfo(modname, RECORD)[1]
    detailname = details[modname][detailfield]
    detrecords = getRecordsInfo(detailname, RECORD)[0]
    fieldTxt  = ["%s%s=%s" % ("        self.", x, xmlValue(detrecords[detailname][x])) for x in detrecords[detailname]]
    methods = getClassInfo(modname, parent="Record")[1]
    methodTextDic = methodTextBuilder(hashIt(methods))
    methsTxt = [methodTextDic[x] for x in methodTextDic if x != "__init__"]
    txt = '''
class %s(object):
    def __iter__(self): return self
    def count(self): pass
    def remove(self, int): pass
    def insert(self, int, row): pass
    def append(self, row): pass
    def clear(self): pass
    def __init__(self, *args):
        self.__fail__ = None
%s
%s
''' % (detailfield, "\n".join(fieldTxt), "\n".join(methsTxt))
    return txt

@cache.store
def buildInstantiator(name, instancerName, fieldsMethodsHashed):
    (xmlfields, attributes, methods) = hashIt(fieldsMethodsHashed, unhash=True)
    instantiatorname = "%s_%s" % (name, instancerName)
    fieldTxt  = ["%s%s=%s" % ("        self.", x, xmlValue(xmlfields[x])) for x in xmlfields if xmlfields[x] != "detail"]
    fieldTxt += ["%s%s=%s()" % ("        self.", x, x) for x in xmlfields if xmlfields[x] == "detail"]
    itersTxt  = ["%s" % getIteratorString(name, x) for x in xmlfields if xmlfields[x] == "detail"]
    attrsTxt  = ["%s%s=%s" % ("        self.", x, attributes[x]) for x in sorted(attributes)]
    methodTextDic = methodTextBuilder(hashIt(methods))
    methsTxt = [methodTextDic[x] for x in methodTextDic if x not in ("__init__", "fieldNames")]
    methsTxt += ["%s" % ("    def fieldNames(self): return ['%s']" % "','".join(xmlfields))]
    newClass  = '''
class %s(object):
    def __init__(self, *args):
        self.__fail__ = None
%s
%s
%s
%s
''' % (instantiatorname, "\n".join(fieldTxt), "\n".join(attrsTxt), "\n".join(methsTxt), "\n".join(itersTxt))
    fake = AstroidBuilder(MANAGER).string_build(newClass)
    if name == "EmployeeMovement":
        from libs.tools import logHere
        logHere(newClass)
    return fake.locals[instantiatorname]

@cache.store
def buildMethod(method, methodText):
    fake = AstroidBuilder(MANAGER).string_build(methodText[4:])
    return  {0:fake[method]}

@cache.store
def methodTextBuilder(hashedMethods):
    txtDic = {}
    methods = hashIt(hashedMethods, unhash=True)
    for meth in methods:
        newMethod = "    def %s(" % meth
        args = methods[meth]
        for idx in args:
            if hasattr(args[idx], "keys"): #it's a dict, defaults
                newMethod += "".join("%s='%s'," % (k, v) for k, v in args[idx].items())
            elif args[idx].startswith("*"):
                sep = "," if newMethod.find("*") > -1 else ""
                newMethod += "%s%s" % (sep, args[idx])
            else:
                newMethod += "%s," % args[idx]
        newMethod += "): pass"
        txtDic[meth] = newMethod
    return txtDic

def buildStringModule(text):
    return AstroidBuilder(MANAGER).string_build(text)




