from astroid import MANAGER
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes
from funcs import getRecordsInfo, findPaths

def hashlib_transform(module):
    modname = module.name
    if findPaths(modname, instant=True):
        records = getRecordsInfo(modname)
        for fields in records[modname]:
            if records[modname][fields] == "detail":
                module.locals[fields] = buildIterator(fields)
            else:
                module.locals[fields] = records[modname][fields]

def buildIterator(name):
    fake = AstroidBuilder(MANAGER).string_build('''
class Class_%s(object):
    def __iter__(self):
        return self
''' % name)
    return fake.locals["Class_"+name]

def register(linter):
    pass

MANAGER.register_transform(scoped_nodes.Class, hashlib_transform)

