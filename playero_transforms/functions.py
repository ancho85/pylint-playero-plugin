from astroid import node_classes
from astroid import raw_building

def function_transform(callFunc):
    if isinstance(callFunc.func, node_classes.Name):
        name = callFunc.func.name
        if name == "hasattr":
            left = callFunc.args[0]
            right = callFunc.args[1]
            if isinstance(left, node_classes.Name) and isinstance(right, node_classes.Const):
                if left.name == "self":
                    parentclass = left.frame().parent
                    if hasattr(parentclass, "locals"):
                        if right.value not in parentclass.locals:
                            newFunc = raw_building.build_function(right.value)
                            parentclass.add_local_node(newFunc, right.value)
        elif name == "NewRecord":
            pass
        elif name == "NewReport":
            pass
        elif name == "NewWindow":
            pass
