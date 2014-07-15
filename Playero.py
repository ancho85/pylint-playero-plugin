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
    if pathType:
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
    modname = getModName(modname)
    if modname == "OpenOrange":
        module.locals.update(buildCore())
    else:
        buildSuperClassModule(module)
        buildExecModule(module)
        #if isRoutine(module):
        #    pass
        #if isReport(module):
        #    pass

        module.locals['CThread'] = buildCThread()

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

    module.locals.update([(attrs, {0:None}) for attrs in attributes if not attrs.startswith("_")])
    module.locals.update([(meths, buildMethod(meths)) for meths in methods if meths not in module.locals])

    if module.name.endswith("Window"): #Window Class
        if len(methods) == len(defaultMethods):
            path, pathType = findPaths(modname)
            if pathType == RECORD:
                realpath = path[0]
                dh = parseRecordXML(realpath)
                methods += list(getClassInfo(dh.name, dh.inheritance)[1])
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
    m, a, e = [], [], []
    if baseclass in reportClasses:
        records = getRecordsInfo("Transaction", extensions=RECORD)[0]
        attributes, methods = getClassInfo("Report", parent="Record")
        m += list(methods) + ["setView", "setAutoRefresh", "run"]
        a += records.get("Transaction", {}).keys() + list(attributes)
        a += ["reportid", "decimalsspec", "routinemode"]
        #e += ["StartDate", "EndDate", "DateField"]
    elif baseclass in routineClasses:
        attributes, methods = getClassInfo("Routine", parent="Record")
        m += list(methods) + ["background", "run"]
        a += list(attributes)
    elif baseclass in otherClasses:
        attributes, methods = getClassInfo("Window", parent="Record")
        m += list(methods) + ["filterPasteWindow"]
        a += list(attributes)
        #e += ["Currency", "Contact", "SupCode", "CustCode", "SerNr", "internalId"]
    else: return
    module.locals.update([(method, buildMethod(method)) for method in m if method not in module.locals])
    module.locals.update([(attr, {0:None}) for attr in a if attr not in module.locals])
    module.locals["getRecord"] = buildInstantiator(baseclass, "getRecord", hashIt((a+e, m)))


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

def buildExecModule(module):
    for assnode in module.body:
        if isinstance(assnode, node_classes.Exec):
            if isinstance(assnode.expr, node_classes.BinOp): #something % somethingelse
                left = assnode.expr.left.as_string()
                right = assnode.expr.right.as_string()
                statement = "%s" % (left + " % " + right)
                dic = {}
                dic.update([(key, key) for key in module.locals])
                newstatement = eval(statement, dic)
                parsed = parseExecLine(newstatement, mode="single")
                if not parsed.errors:
                    name = ifElse(parsed.alias, parsed.alias, parsed.importwhat)
                    module.locals[name] = buildMethod(name)
            elif isinstance(assnode.expr, node_classes.Const):
                newstatement = eval(assnode.expr.as_string())
                parsed = parseExecLine(newstatement, mode="single")
                if not parsed.errors:
                    for newvar in parsed.targets:
                        txt  = "class %s(object):\n" % (newvar)
                        txt += "\tpass\n"
                        module.locals[newvar] = AstroidBuilder(MANAGER).string_build(txt).locals[newvar]



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

@cache.store
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
    coreTxt = open(os.path.join(os.path.dirname(__file__), "corepy","coreRedef.py"), "r").read()
    fake = AstroidBuilder(MANAGER).string_build(coreTxt)
    return fake.locals

###plugin's default methods###

def register(linter):
    """required method to auto register this checker"""
    if cache.collectStats:
        from checkers_classes import CacheStatisticWriter
        linter.register_checker(CacheStatisticWriter(linter, cache))

MANAGER.register_transform(scoped_nodes.Module, modules_transform)
MANAGER.register_transform(scoped_nodes.Class, classes_transform)
MANAGER.register_transform(node_classes.CallFunc, function_transform)

