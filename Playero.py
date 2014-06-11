from astroid import MANAGER, node_classes
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes
from funcs import *

notFound = set()

def classes_transform(module):
    modname = getModName(module.name)
    if modname in notFound: return
    found = False
    if findPaths(modname, ".record.xml", True) or findPaths(modname, ".window.xml", True):
        found = buildRecordModule(module)
    elif findPaths(modname, ".reportwindow.xml", True):
        found = buildReportModule(module)
    elif findPaths(modname, ".routinewindow.xml", True):
        found = buildRoutineModule(module)
    if not found:
        notFound.add(modname)


def modules_transform(module):
    modname = module.name
    if not modname: return
    modname = getModName(modname)
    if modname == "OpenOrange":
        module.locals.update(buildCore())
    else:
        buildSuperClassModule(module)
        def isRoutine():
            return ifElse(module.body[0].parent.name.find(".routines.") > -1, True, False)
        def isReport():
            return ifElse(module.body[0].parent.name.find(".reports.") > -1, True, False)

        if isRoutine():
            module.locals['CThread'] = buildCThread()
        if isReport():
            pass




###classes_transform_methods###
def buildRecordModule(module):
    modname = getModName(module.name)
    searchExtensions = ".record.xml,.window.xml"
    records, details = getRecordsInfo(modname, searchExtensions)
    if modname not in records: return
    for fields in records[modname]:
        if records[modname][fields] == "detail":
            detailname = details[modname][fields]
            detrecords = getRecordsInfo(detailname)[0]
            module.locals[fields] = buildIterator(modname, fields, detrecords[detailname])
        else:
            module.locals[fields] = records[modname][fields]
    attributes, methods = getClassInfo(modname, getModName(module.parent.name))
    instanceFields = list(records[modname]) + list(attributes)

    for insBuilder in ("bring", "getMasterRecord"):
        module.locals[insBuilder] = buildInstantiator(modname, insBuilder, instanceFields, methods)

    module.locals.update([(attrs, {0:None}) for attrs in attributes if not attrs.startswith("_")])
    module.locals.update([(meths, buildMethod(modname, meths)) for meths in methods if meths not in module.locals])

    if module.name.endswith("Window"): #Window Class
        if len(methods) == len(defaultMethods):
            realpath = findPaths(modname, searchExtensions, instant=True)[0]["fullpath"]
            dh = parseRecordXML(realpath)
            methods += list(getClassInfo(dh.name, dh.inheritance)[1])
        module.locals["getRecord"] = buildInstantiator(modname, "getRecord", instanceFields, methods)
    return True

def buildReportModule(module):
    return genericBuilder(module, "Report")

def buildRoutineModule(module):
    return genericBuilder(module, "Routine")

def genericBuilder(module, buildIdx):
    res = False
    buildType = {
                "Report": [".reportwindow.xml", ".reports."],
                "Routine": [".routinewindow.xml",".routines."]
    }
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
        instanceFields = list(records[modname]) + list(attributes)
        module.locals["getRecord"] = buildInstantiator(modname, "getRecord", instanceFields, methods)
        res = True
    return res

def buildIterator(name, detailfield, fields):
    itername = "%s_%s" % (name, detailfield)
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    fake = AstroidBuilder(MANAGER).string_build('''
class %s(object):
    def __iter__(self):
        return self

    def count(): pass
    def remove(int): pass
    def insert(int, *args): pass
    def append(*args): pass

    def __init__(self, *args):
        self.__fail__ = None
%s
''' % (itername, "\n".join(fieldTxt)))
    return fake.locals[itername]


def buildInstantiator(name, instancerName, fields, methods):
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


def buildMethod(name, method):
    methodname = "%s_%s" % (name, method)
    fake = AstroidBuilder(MANAGER).string_build("def %s(self, **kwargs): pass" % methodname)
    return  {0:fake[methodname]}


###modules_transforms_methods###
def buildSuperClassModule(module):
    parents = {}
    for assnodes in module.locals:
        ass = module.locals[assnodes][0]
        if not (
                isinstance(ass, node_classes.AssName) and
                isinstance(ass.statement(), node_classes.Assign)
                ): continue
        else:
            for supers in [ #list comprehention of SuperClass' calls
                            superCall for superCall in ass.assigned_stmts()
                            if isinstance(superCall, node_classes.CallFunc)
                            and superCall.as_string().startswith("SuperClass")
            ]:
                parents[ass.name] = []
                for arg in [
                            classString for classString in supers.args
                            if isinstance(classString, node_classes.Const)
                            and not classString.value.endswith("Row")
                ]:
                    parents[ass.name].append(arg.value)
    if parents:
        for supers in parents:
            if len(parents[supers]) > 1:
                heir, dad = parents[supers][0], parents[supers][1]
                module.locals['SuperClass'] = buildSuperClass(heir, dad)

def buildSuperClass(classname, parent=""):
    methods = getClassInfo(classname, parent)[1]
    methsTxt = ["%s%s%s" % ("        def ", x, "(self, *args, **kwargs): pass") for x in methods]
    txt = '''
def %s(classname, superclassname, filename):
    class %s(object):
%s
    return %s()
''' % ("SuperClass", classname, "\n".join(methsTxt), classname)
    fake = AstroidBuilder(MANAGER).string_build(txt)
    return fake.locals["SuperClass"]

def buildCThread():
    txt = """
class CThread:
    def __init__(*args): pass
    def setName(*args): pass
    def start(*args): pass
"""
    fake = AstroidBuilder(MANAGER).string_build(txt)
    return fake.locals["CThread"]

def buildCore():
    import os
    coreTxt = open(os.path.join(os.path.dirname(__file__), "corepy","coreRedef.py"), "r").read()
    fake = AstroidBuilder(MANAGER).string_build(coreTxt)
    return fake.locals



def register(linter):
    pass


MANAGER.register_transform(scoped_nodes.Module, modules_transform)
MANAGER.register_transform(scoped_nodes.Class, classes_transform)
