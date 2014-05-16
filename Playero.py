from astroid import MANAGER
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes
from funcs import getRecordsInfo, findPaths

built = ["Record","RawRecord"]

def hashlib_transform(module):
    modname = module.name
    if modname in built: return
    if findPaths(modname, instant=True):
        records, details = getRecordsInfo(modname)
        for fields in records[modname]:
            if records[modname][fields] == "detail":
                detailname = details[modname][fields]
                detrecords = getRecordsInfo(detailname)[0]
                module.locals[fields] = buildIterator(modname, fields, detrecords[detailname])
            else:
                module.locals[fields] = records[modname][fields]
        module.locals["bring"] = buildBring(modname, records[modname])

def buildIterator(name, detailfield, fields):
    built.append("%s_%s" % (name, detailfield))
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
    built.append("%s_%s" % (name, "bring"))
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    fake = AstroidBuilder(MANAGER).string_build('''
class %s_bring(object):
    def __init__(self, *args):
        self.__fail__ = None
%s
''' % (name, "\n".join(fieldTxt)))
    return fake.locals[name+"_bring"]

def register(linter):
    pass

MANAGER.register_transform(scoped_nodes.Class, hashlib_transform)

if __name__ == "__main__":
    class Test(object):
        def __init__(self):
            self.name = ""
            self.locals = {}

    test = Test()
    test.name = "Invoice"
    hashlib_transform(test)

