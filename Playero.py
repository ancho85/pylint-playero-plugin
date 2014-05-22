from astroid import MANAGER, node_classes
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes
from funcs import getRecordsInfo, findPaths, getClassInfo, logHere

built = ["Record","RawRecord"]


def classes_transform(module):
    modname = module.name
    if modname in built: return
    if findPaths(modname, instant=True):
        records, details = getRecordsInfo(modname)
        for fields in records[modname]:
            if records[modname][fields] == "detail":
                detailname = details[modname][fields]
                detrecords = getRecordsInfo(detailname)[0]
                module.locals[fields] = buildIterator(modname, fields, detrecords[detailname])
            else:
                module.locals[fields] = records[modname][fields]
        attributes, methods = getClassInfo(modname)
        instanceFields = list(records[modname]) + list(attributes)
        module.locals["bring"] = buildBring(modname, instanceFields, methods)

        module.locals.update([(attr, {0:None}) for attr in attributes])
        module.locals.update([(meth, buildMethod(modname, meth)) for meth in methods if meth not in module.locals])


def modules_transform(module):
    parents = []
    for assnodes in module.locals:
        ass = module.locals[assnodes][0]
        if not (
                isinstance(ass, node_classes.AssName) and
                isinstance(ass.statement(), node_classes.Assign)
                ): continue
        else:
            for supers in [ #list comprehention of SuperClass' calls
                            superCall for superCall in ass.assigned_stmts()
                            if isinstance(superCall, node_classes.CallFunc) and
                            superCall.as_string().startswith("SuperClass")
            ]:
                for arg in [classString for classString in supers.args if isinstance(classString, node_classes.Const)]:
                    parents.append(arg.value)
    if parents:
        #XXX SuperClass built is not a independent instance
        #XXX InvoiceTaxRow at Copeg's Invoice.py broke the system.
        a = parents[0]
        if a == "InvoiceTaxRow": a = parents[1]
        module.locals['SuperClass'] = buildSuperClass(a)
        module.locals["WTF"] = buildSuperClass(parents[0])


###classes_transform_methods###
def buildIterator(name, detailfield, fields):
    itername = "%s_%s" % (name, detailfield)
    built.append(itername)
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    fake = AstroidBuilder(MANAGER).string_build('''
class %s(object):
    def __iter__(self):
        return self

    def count(): pass
    def remove(int): pass
    def insert(int, *args): pass

    def __init__(self, *args):
        self.__fail__ = None
%s
''' % (itername, "\n".join(fieldTxt)))
    return fake.locals[itername]


def buildBring(name, fields, methods):
    bringname = "%s_%s" % (name, "bring")
    built.append(bringname)
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    methsTxt = ["%s%s%s" % ("    def ", x, "(self, **kwargs): pass") for x in methods]
    fake = AstroidBuilder(MANAGER).string_build('''
class %s(object):
    def __init__(self, *args):
        self.__fail__ = None
%s
%s
''' % (bringname, "\n".join(fieldTxt), "\n".join(methsTxt)))
    return fake.locals[bringname]


def buildMethod(name, method):
    methodname = "%s_%s" % (name, method)
    fake = AstroidBuilder(MANAGER).string_build("def %s(self, **kwargs): pass" % methodname)
    return  {0:fake[methodname]}


###modules_transforms_methods###
def buildSuperClass(classname):
    superclassname = "%s_%s" % ("SuperClass",classname)
    attributes, methods = getClassInfo(classname)
    methsTxt = ["%s%s%s" % ("        def ", x, "(self, *args, **kwargs): pass") for x in methods]
    txt = '''
def %s(classname, superclassname, filename):
    class %s(object):
%s

        return %s
''' % (superclassname, classname, "\n".join(methsTxt), classname)
    fake = AstroidBuilder(MANAGER).string_build(txt)
    return fake.locals[superclassname]


def register(linter):
    pass


MANAGER.register_transform(scoped_nodes.Module, modules_transform)
MANAGER.register_transform(scoped_nodes.Class, classes_transform)
