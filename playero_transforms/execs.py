from astroid import node_classes
from astroid import raw_building
from libs.pyparse import parseExecLine
from libs.funcs import *
import ast

def exec_transform(assnode):
    modname = getModName(getattr(assnode.root(), "name", ""))
    if not modname: return
    paths, pathType = findPaths(modname)
    if paths or pathType or modname in allCoreClasses:
        if isinstance(assnode.expr, node_classes.BinOp): #something % somethingelse
            build_binary_op(assnode)
        elif isinstance(assnode.expr, node_classes.Const):
            build_constant(assnode)

def build_binary_op(assnode):
    left = assnode.expr.left.as_string()
    right = assnode.expr.right.as_string()
    statement = "%s" % (left + " % " + right)
    dic = dict((key, key) for key in assnode.frame().locals)
    try:
        new_statement = eval(statement, {}, dic)
    except Exception:
        return
    parsed = parseExecLine(new_statement, mode="single")
    if parsed.errors: return
    if parsed.importfrom:
        name = parsed.alias or parsed.importwhat
        newClass = raw_building.build_class(name)
        assnode.root().add_local_node(newClass, name)
    elif parsed.targets:
        value = parsed.values[0]
        new_value = ""
        if isinstance(value, ast.Name):
            new_value = value.id
        raw_building.attach_const_node(assnode.scope(), parsed.targets[0], new_value)

def build_constant(assnode):
    new_statement = eval(assnode.expr.as_string())
    parsed = parseExecLine(new_statement, mode="single")
    if parsed.errors: return
    for key, newvar in parsed.targets.iteritems():
        value = parsed.values[key]
        new_value = ""
        if isinstance(value, ast.Call):
            new_value = value.func.id
        elif isinstance(value, ast.Str):
            new_value = value.s
        raw_building.attach_const_node(assnode.scope(), newvar, new_value)
