from astroid import MANAGER
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes
from funcs import getRecordsInfo, findPaths

def hashlib_transform(module):
    modname = module.name
    if findPaths(modname, instant=True):
        records, details = getRecordsInfo(modname)
        for fields in records[modname]:
            if records[modname][fields] == "detail":
                detailname = details[modname][fields]
                detrecords, detdetails = getRecordsInfo(detailname)
                module.locals[fields] = buildIterator(modname, fields, detrecords[detailname])
            else:
                module.locals[fields] = records[modname][fields]
        module.locals["bring"] = buildBring(modname, records[modname])

def buildIterator(name, detailfield, fields):
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    fake = AstroidBuilder(MANAGER).string_build('''
class %s_%s(object):
    def __iter__(self):
        return self

    def __init__(self, *args):
        self.__fail__ = None
%s
''' % (name, detailfield, "\n".join(fieldTxt)))
    return fake.locals["%s_%s" % (name, detailfield)]

def buildBring(name, fields):
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    fake = AstroidBuilder(MANAGER).string_build('''
class %sBring(object):
    def __init__(self, *args):
        self.__fail__ = None
%s
''' % (name, "\n".join(fieldTxt)))
    return fake.locals[name+"Bring"]

def register(linter):
    pass

MANAGER.register_transform(scoped_nodes.Class, hashlib_transform)
