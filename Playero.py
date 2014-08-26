from astroid import MANAGER, node_classes
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes
from funcs import *
from tools import hashIt
from transform_mods import modules_transform
from transform_func import function_transform
from transform_exec import exec_transform

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
    elif modname in allCoreClasses:
        baseClassBuilder(module, modname)
    else:
        notFound.add(modname)

###classes_transform_methods###
def buildRecordModule(module):
    modname = getModName(module.name)
    records, details = getRecordsInfo(modname, RECORD)
    if modname not in records: return
    for fields in records[modname]:
        if records[modname][fields] == "detail":
            detailname = details[modname][fields]
            detrecords = getRecordsInfo(detailname, RECORD)[0]
            module.locals[fields] = buildIterator(modname, fields, detrecords[detailname])
        else:
            module.locals[fields] = records[modname][fields]
    attributes, methods = getClassInfo(modname, getModName(module.parent.name))
    instanceFields = list(records[modname]) + list(attributes)

    for insBuilder in ("bring", "getMasterRecord"):
        module.locals[insBuilder] = buildInstantiator(modname, insBuilder, hashIt((instanceFields, methods)))

    module.locals.update([(attrs, {0:None}) for attrs in attributes if not attrs.startswith("_") and attrs not in module.locals])
    module.locals.update([(meths, buildMethod(meths)) for meths in methods if meths not in module.locals])

    if module.name.endswith("Window"): #Window Class
        methods += list(getClassInfo("Window", "Embedded_Window")[1])
        module.locals.update([(meths, buildMethod(meths)) for meths in methods if meths not in module.locals])
        module.locals["getRecord"] = buildInstantiator(modname, "getRecord", hashIt((instanceFields, methods)))
    return True

def buildReportModule(module):
    return genericBuilder(module, "Report")

def buildRoutineModule(module):
    return genericBuilder(module, "Routine")

def genericBuilder(module, buildIdx):
    res = False
    buildType = {
                "Report": [REPORT, ".reports."],
                "Routine": [ROUTINE,".routines."]
    }
    if buildIdx not in buildType: return res
    ext = buildType[buildIdx][0]
    cls = buildType[buildIdx][1]
    modname = getModName(module.name)
    classtype = module.basenames[0]
    if classtype != buildIdx:
        rootname =  module.bases[0].root().name
        if rootname.find(cls)>-1: classtype = buildIdx
    if classtype == buildIdx:
        records = getRecordsInfo(modname, extensions=ext)[0]
        attributes, methods = getClassInfo(modname, parent=classtype)
        instanceFields = records.get(modname, {}).keys() + list(attributes)
        module.locals["getRecord"] = buildInstantiator(modname, "getRecord", hashIt((instanceFields, methods)))
        res = True
    return res

def baseClassBuilder(module, baseclass):
    if baseclass in allCoreClasses:
        if baseclass in reportClasses:
            records = getRecordsInfo("Transaction", extensions=RECORD)[0]
            attributes, methods = getClassInfo("Embedded_Report", parent="Embedded_Record")
            attributes += records.get("Transaction", {}).keys()
        elif baseclass in routineClasses:
            attributes, methods = getClassInfo("Embedded_Routine", parent="Embedded_Record")
        elif baseclass in otherClasses:
            attributes, methods = getClassInfo("Embedded_Window", parent="Embedded_Record")
        module.locals.update([(method, buildMethod(method)) for method in methods if method not in module.locals])
        module.locals.update([(attr, {0:None}) for attr in attributes if attr not in module.locals])
        module.locals["getRecord"] = buildInstantiator(baseclass, "getRecord", hashIt((attributes, methods)))


def buildIterator(name, detailfield, fields):
    itername = "%s_%s" % (name, detailfield)
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    methods = list(getClassInfo("Record", "Embedded_Record")[1])
    methsTxt = ["%s%s%s" % ("    def ", x, "(self, *args, **kwargs): pass") for x in methods if x != "__init__"]
    fake = AstroidBuilder(MANAGER).string_build('''
class %s(object):
    def __iter__(self):
        return self

    def count(): pass
    def remove(int): pass
    def insert(int, *args): pass
    def append(*args): pass
    def clear(*args): pass

    def __init__(self, *args):
        self.__fail__ = None
%s
%s
''' % (itername, "\n".join(fieldTxt), "\n".join(methsTxt)))
    return fake.locals[itername]

@cache.store
def buildInstantiator(name, instancerName, fieldsMethodsHashed):
    (fields, methods) = hashIt(fieldsMethodsHashed, unhash=True)
    instantiatorname = "%s_%s" % (name, instancerName)
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    methsTxt = ["%s%s%s" % ("    def ", x, "(self, *args, **kwargs): pass") for x in methods]
    fake = AstroidBuilder(MANAGER).string_build('''
class %s(object):
    def __init__(self, *args):
        self.__fail__ = None
%s
%s
''' % (instantiatorname, "\n".join(fieldTxt), "\n".join(methsTxt)))
    return fake.locals[instantiatorname]

@cache.store
def buildMethod(method):
    fake = AstroidBuilder(MANAGER).string_build("def %s(self, **kwargs): pass" % method)
    return  {0:fake[method]}


###plugin's default methods###

def register(linter):
    """required method to auto register this checker"""
    if cache.collectStats:
        from checkers_classes import CacheStatisticWriter
        linter.register_checker(CacheStatisticWriter(linter, cache))


MANAGER.register_transform(scoped_nodes.Module, modules_transform)
MANAGER.register_transform(scoped_nodes.Class, classes_transform)
MANAGER.register_transform(node_classes.CallFunc, function_transform)
MANAGER.register_transform(node_classes.Exec, exec_transform)

