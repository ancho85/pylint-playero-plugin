from astroid.builder import AstroidBuilder
from astroid import MANAGER, node_classes
from astroid.exceptions import InferenceError
from libs.funcs import getClassInfo, getModName, findPaths, allCoreClasses

def modules_transform(module):
    if not hasattr(module, "name"): return
    modname = getModName(module.name)
    if not modname: return
    paths, pathType = findPaths(modname)
    if paths or pathType or modname in allCoreClasses:
        buildSuperClassModule(module)
        buildNewRecordModule(module)
        buildNewReportModule(module)
        buildNewWindowModule(module)

def getFunctionArguments(module, funcTxt):
    res = []
    for assnodes in module.locals:
        ass = module.locals[assnodes][0]
        if not (
                isinstance(ass, node_classes.AssName)
                and isinstance(ass.statement(), node_classes.Assign)
                ): continue
        else:
            for supers in [ #list comprehention of funcTxt's calls
                            superCall for superCall in ass.assigned_stmts()
                            if isinstance(superCall, node_classes.CallFunc)
                            and superCall.as_string().startswith(funcTxt)
            ]:
                for arg in supers.args:
                    if isinstance(arg, node_classes.Const):
                        res.append(arg.value)
                    elif isinstance(arg, node_classes.Name):
                        for iarg in [x for x in arg.infered() if isinstance(x, node_classes.Const)]:
                            res.append(iarg.value)
    return res

def buildSuperClassModule(module):
    sclist = getFunctionArguments(module, "SuperClass")
    if not len(sclist) % 3 == 0: return
    while len(sclist):
        if not sclist[0].endswith("Row"):
            module.locals['SuperClass'] = classBuilder("SuperClass", sclist[0], sclist[1])
        sclist = sclist[3:]

def buildNewRecordModule(module):
    for arg in getFunctionArguments(module, "NewRecord"):
        module.locals["NewRecord"] = classBuilder("NewRecord", arg)

def buildNewReportModule(module):
    for arg in getFunctionArguments(module, "NewReport"):
        module.locals["NewReport"] = classBuilder("NewReport", arg, "Embedded_Report")

def buildNewWindowModule(module):
    for arg in getFunctionArguments(module, "NewWindow"):
        module.locals["NewWindow"] = classBuilder("NewWindow", arg, "Embedded_Window")


def classBuilder(name, classname, parent=""):
    attributes, methods = getClassInfo(classname, parent)
    methsTxt = ["%s%s%s" % ("        def ", x, "(self, *args, **kwargs): pass") for x in methods if x != "__init__"]
    attrsTxt = ["%s%s=%s" % ("            self.", x, attributes[x]) for x in sorted(attributes)]
    txt = '''
def %s(classname, superclassname, filename):
    class %s(object):
        def __init__(self):
            self.__failsafe__ = None
%s
%s
    return %s()
''' % (name, classname, "\n".join(attrsTxt),"\n".join(methsTxt), classname)
    fake = AstroidBuilder(MANAGER).string_build(txt)
    return fake.locals[name]
