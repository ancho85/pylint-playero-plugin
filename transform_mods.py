from astroid.builder import AstroidBuilder
from astroid import MANAGER, node_classes
from astroid.exceptions import InferenceError
from funcs import getClassInfo
from tools import logHere

def modules_transform(module):
    modname = module.name
    if not modname: return
    buildSuperClassModule(module)
    buildNewRecordModule(module)
    buildNewReportModule(module)

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

def assHasAssignedStmts(theAss):
    """ pylint's problem with lines like: "a = [x for x in tuple([1,2])]" """
    res = True
    try:
        for _ in theAss.assigned_stmts():
            pass
    except InferenceError:
        res = False
    return res

def buildSuperClassModule(module):
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
                module.locals['SuperClass'] = classBuilder("SuperClass", heir, dad)

def classBuilder(name, classname, parent=""):
    methods = getClassInfo(classname, parent)[1]
    methsTxt = ["%s%s%s" % ("        def ", x, "(self, *args, **kwargs): pass") for x in methods]
    txt = '''
def %s(classname, superclassname, filename):
    class %s(object):
%s
    return %s()
''' % (name, classname, "\n".join(methsTxt), classname)
    fake = AstroidBuilder(MANAGER).string_build(txt)
    return fake.locals[name]

def buildNewRecordModule(module):
    parents = {}
    for assnodes in module.locals:
        ass = module.locals[assnodes][0]
        if not (
                isinstance(ass, node_classes.AssName)
                and isinstance(ass.statement(), node_classes.Assign)
                and assHasAssignedStmts(ass)
                ): continue
        else:
            for supers in [ #list comprehention of NewRecord's calls
                            superCall for superCall in ass.assigned_stmts()
                            if isinstance(superCall, node_classes.CallFunc)
                            and superCall.as_string().startswith("NewRecord")
            ]:
                parents[ass.name] = []
                for arg in supers.args:
                    if isinstance(arg, node_classes.Const):
                        parents[ass.name].append(arg.value)
                    elif isinstance(arg, node_classes.Name):
                        for iarg in [x for x in arg.infered() if isinstance(x, node_classes.Const)]:
                            parents[ass.name].append(iarg.value)
    for newr in parents:
        if len(parents[newr]):
            module.locals["NewRecord"] = classBuilder("NewRecord", parents[newr][0])

def buildNewReportModule(module):
    parents = {}
    for assnodes in module.locals:
        ass = module.locals[assnodes][0]
        if not (
                isinstance(ass, node_classes.AssName)
                and isinstance(ass.statement(), node_classes.Assign)
                and assHasAssignedStmts(ass)
                ): continue
        else:
            for supers in [ #list comprehention of NewReport's calls
                            superCall for superCall in ass.assigned_stmts()
                            if isinstance(superCall, node_classes.CallFunc)
                            and superCall.as_string().startswith("NewReport")
            ]:
                parents[ass.name] = []
                for arg in supers.args:
                    if isinstance(arg, node_classes.Const):
                        parents[ass.name].append(arg.value)
                    elif isinstance(arg, node_classes.Name):
                        for iarg in [x for x in arg.infered() if isinstance(x, node_classes.Const)]:
                            parents[ass.name].append(iarg.value)
    for newr in parents:
        if len(parents[newr]):
            module.locals["NewReport"] = classBuilder("NewReport", parents[newr][0], "Embedded_Report")
