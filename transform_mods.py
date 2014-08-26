from astroid.builder import AstroidBuilder
from astroid import MANAGER, node_classes
from astroid.exceptions import InferenceError
from funcs import getClassInfo

def modules_transform(module):
    modname = module.name
    if not modname: return
    buildSuperClassModule(module)

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
