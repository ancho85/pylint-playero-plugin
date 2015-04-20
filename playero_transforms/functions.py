from astroid import MANAGER, node_classes, raw_building
from astroid.builder import AstroidBuilder
from libs.funcs import getClassInfo, getModName, findPaths, allCoreClasses, getRecordsInfo
from libs.cache import cache
from libs.tools import hashIt
from playero_transforms.classes import methodTextBuilder, buildInstantiator

def function_transform(callFunc):
    fparent = callFunc.frame().parent
    if isinstance(callFunc.func, node_classes.Name):
        funcName = callFunc.func.name
        if funcName == "hasattr":
            left = callFunc.args[0]
            right = callFunc.args[1]
            if isinstance(left, node_classes.Name) and isinstance(right, node_classes.Const):
                if left.name == "self":
                    parentclass = left.frame().parent
                    if hasattr(parentclass, "locals"):
                        if right.value not in parentclass.locals:
                            newFunc = raw_building.build_function(right.value)
                            parentclass.add_local_node(newFunc, right.value)
        elif funcName in ("NewRecord", "NewReport", "NewWindow"):
            arg = callFunc.args[0]
            if isinstance(arg, node_classes.Const):
                newFunc = functionBuilder(name=funcName, classname=arg.value, parent=funcName[3:])
                fparent.add_local_node(newFunc[0], funcName)
    elif isinstance(callFunc.func, node_classes.Getattr):
        module = callFunc.root()
        if not hasattr(module, "name"): return
        modname = getModName(module.name)
        if not modname: return
        paths, pathType = findPaths(modname)
        if paths or pathType or modname in allCoreClasses:
            insName = callFunc.func.attrname
            if insName in ("getRecord", "getMasterRecord"):
                getter = instanciatorBuilder(modname, pathType, insName)
                if fparent:
                    fparent.add_local_node(getter, insName)
                else:
                    callFunc.frame().add_local_node(getter, insName)

@cache.store
def functionBuilder(name, classname, parent=""):
    attributes, methods = getClassInfo(classname, parent)
    methodTextDic = methodTextBuilder(hashIt(methods))
    methsTxt = ["    %s" % methodTextDic[x] for x in methodTextDic if x != "__init__"]
    attrsTxt = ["%s%s=%s" % ("            self.", x, attributes[x]) for x in sorted(attributes)]
    txt = '''
def %s(rname):
    class %s(object):
        def __init__(self):
            self.__failsafe__ = None
%s
%s
    return %s()
''' % (name, classname, "\n".join(attrsTxt), "\n".join(methsTxt), classname)
    fake = AstroidBuilder(MANAGER).string_build(txt)
    return fake.locals[name]

@cache.store
def instanciatorBuilder(modname, pathType, insName):
    records = getRecordsInfo(modname, pathType)[0]
    xmlfields = records.get(modname, {})
    attributes, methods = getClassInfo(modname)
    newInst = buildInstantiator(modname, insName, hashIt((xmlfields, attributes, methods)))
    return newInst[0]
