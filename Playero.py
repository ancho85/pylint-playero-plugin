from astroid import MANAGER, node_classes
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes
from funcs import *

notFound = set()

def classes_transform(module):
    modname = getModName(module.name)
    if modname in notFound: return
    found = False
    searchExtensions = ".record.xml,.window.xml"
    if findPaths(modname, extensions=searchExtensions, instant=True): #Record Class
        records, details = getRecordsInfo(modname, extensions=searchExtensions)
        if modname not in records: return
        for fields in records[modname]:
            if records[modname][fields] == "detail":
                detailname = details[modname][fields]
                detrecords = getRecordsInfo(detailname)[0]
                module.locals[fields] = buildIterator(modname, fields, detrecords[detailname])
            else:
                module.locals[fields] = records[modname][fields]
        modparent = getModName(module.parent.name)
        attributes, methods = getClassInfo(modname, modparent)
        instanceFields = list(records[modname]) + list(attributes)
        module.locals["bring"] = buildInstantiator(modname, "bring", instanceFields, methods)
        module.locals["getMasterRecord"] = buildInstantiator(modparent, "getMasterRecord", instanceFields, methods)

        module.locals.update([(attr, {0:None}) for attr in attributes if not attr.startswith("_")])
        module.locals.update([(meth, buildMethod(modname, meth)) for meth in methods if meth not in module.locals])

        if module.name.endswith("Window"): #Window Class
            if len(methods) == len(defaultMethods):
                realpath = findPaths(modname, searchExtensions, instant=True)[0]["fullpath"]
                dh = parseRecordXML(realpath)
                methods += list(getClassInfo(dh.name, dh.inheritance)[1])
            module.locals["getRecord"] = buildInstantiator(modname, "getRecord", instanceFields, methods)
        found = True
    else: #Check for Reports and Routines
        searchExtensions = ".reportwindow.xml,.routinewindow.xml"
        if findPaths(modname, extensions=searchExtensions, instant=True):
            classtype = module.basenames[0]
            if classtype not in ("Report","Routine"):
                rootname =  module.bases[0].root().name
                if rootname.find(".reports.")>-1: classtype = "Report"
                elif rootname.find(".routines.")>-1: classtype = "Routine"
            if classtype in ("Report","Routine"):
                records, details = getRecordsInfo(modname, extensions=searchExtensions)
                attributes, methods = getClassInfo(modname, parent=classtype)
                instanceFields = list(records[modname]) + list(attributes)
                module.locals["getRecord"] = buildInstantiator(modname, "getRecord", instanceFields, methods)
                found = True
    if not found:
        notFound.add(modname)


def modules_transform(module):
    modname = module.name
    if not modname: return
    modname = getModName(modname)
    if modname == "OpenOrange":
        module.locals.update(buildCore())
    else:
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
    module.locals['CThread'] = buildCThread()


###classes_transform_methods###
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
