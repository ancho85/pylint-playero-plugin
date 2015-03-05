from astroid import node_classes
from astroid import raw_building
from libs.pyparse import parseExecLine
from libs.funcs import *

def exec_transform(assnode):
    module = assnode.frame().parent
    if not module: return
    if not hasattr(module, "name"): return
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
