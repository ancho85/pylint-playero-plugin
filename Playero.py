from astroid import MANAGER, node_classes
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes, raw_building
from astroid.exceptions import InferenceError
from funcs import *
from tools import hashIt

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

def modules_transform(module):
    modname = module.name
    if not modname: return
    buildSuperClassModule(module)

def function_transform(callFunc):
    if callFunc.func.as_string() == "hasattr":
        left = callFunc.args[0]
        right = callFunc.args[1]
        if isinstance(left, node_classes.Name) and isinstance(right, node_classes.Const):
            if left.name == "self":
                parentclass = left.frame().parent
                if right.value not in parentclass.locals:
                    newFunc = raw_building.build_function(right.value)
                    parentclass.add_local_node(newFunc, right.value)

def exec_transform(assnode):
    module = assnode.frame().parent
    if not module: return
    modname = getModName(module.name)
    if not modname: return
    paths, pathType = findPaths(modname)
    if paths or pathType or modname in allCoreClasses:
        if isinstance(assnode.expr, node_classes.BinOp): #something % somethingelse
            left = assnode.expr.left.as_string()
            right = assnode.expr.right.as_string()
            statement = "%s" % (left + " % " + right)
            dic = dict((key, key) for key in assnode.frame().locals)
            try:
                newstatement = eval(statement, {}, dic)
            except Exception, e:
                #logHere(assnode.frame().lookup("gr").next())
                #a = assnode.frame().locals['gr'][0].ilookup('gr').next()
                #inspectModule(a, "", "module", force=True)
                pass
            else:
                parsed = parseExecLine(newstatement, mode="single")
                if not parsed.errors:
                    if parsed.importfrom:
                        name = ifElse(parsed.alias, parsed.alias, parsed.importwhat)
                        newClass = raw_building.build_class(name)
                        assnode.root().add_local_node(newClass, name)
                    elif parsed.targets:
                        value = parsed.values[0]
                        newvalue = ""
                        if hasattr(value, "func"):
                            newvalue = value.func.id
                        elif hasattr(value, "s"):
                            newvalue = value.s
                        raw_building.attach_const_node(assnode.scope(), parsed.targets[0], newvalue)
        elif isinstance(assnode.expr, node_classes.Const):
            newstatement = eval(assnode.expr.as_string())
            parsed = parseExecLine(newstatement, mode="single")
            if not parsed.errors:
                for key, newvar in parsed.targets.iteritems():
                    value = parsed.values[key]
                    newvalue = ""
                    if hasattr(value, "func"):
                        newvalue = value.func.id
                    elif hasattr(value, "s"):
                        newvalue = value.s
                    raw_building.attach_const_node(assnode.scope(), newvar, newvalue)



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


###modules_transforms_methods###
def isRoutine(module):
    if len(module.body):
        if module.body[0].parent.name.find(".routines.") > -1:
            return True
    return False

def isReport(module):
    if len(module.body):
        if module.body[0].parent.name.find(".reports.") > -1:
            return True
    return False

def buildSuperClassModule(module):

    def assHasAssignedStmts(theAss):
        """ pylint's problem with lines like: "a = [x for x in tuple([1,2])]" """
        res = True
        try:
            for _ in theAss.assigned_stmts():
                pass
        except InferenceError:
            res = False
        return res

    parents = {}
    for assnodes in module.locals:
        ass = module.locals[assnodes][0]
        if not (
                isinstance(ass, node_classes.AssName)
                and isinstance(ass.statement(), node_classes.Assign)
                and assHasAssignedStmts(ass)
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

def get_embedded_locals():
    """ USELESS: because the path is added in the .pylintrc file"""
    from astroid.manager import _silent_no_wrap
    from os.path import join, abspath, dirname
    EMBEDDED = join(dirname(abspath(__file__)), 'corepy', "embedded")
    project = MANAGER.project_from_files([EMBEDDED], func_wrapper=_silent_no_wrap, project_name="embedded")

    for modules in project.get_children():
        for k, v in modules.locals.items():
            yield (k, v)


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

