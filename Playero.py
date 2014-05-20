from astroid import MANAGER
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes
from funcs import getRecordsInfo, findPaths, getClassInfo

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
        attributes, methods = getClassInfo(modname)
        instanceFields = list(records[modname]) + list(attributes)
        module.locals["bring"] = buildBring(modname, instanceFields)

        module.locals.update([(attr, {0:None}) for attr in attributes])
        module.locals.update([("_"+meth, buildMethod(modname, meth)) for meth in methods])


def buildIterator(name, detailfield, fields):
    itername = "%s_%s" % (name, detailfield)
    built.append(itername)
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    fake = AstroidBuilder(MANAGER).string_build('''
class %s(object):
    def __iter__(self):
        return self

    def count(): pass

    def __init__(self, *args):
        self.__fail__ = None
%s
''' % (itername, "\n".join(fieldTxt)))
    return fake.locals[itername]


def buildBring(name, fields):
    bringname = "%s_%s" % (name, "bring")
    built.append(bringname)
    fieldTxt = ["%s%s%s" % ("        self.", x," = None") for x in fields]
    fake = AstroidBuilder(MANAGER).string_build('''
class %s(object):
    def __init__(self, *args):
        self.__fail__ = None
%s
''' % (bringname, "\n".join(fieldTxt)))
    return fake.locals[bringname]


def buildMethod(name, method):
    methodname = "%s_%s" % (name, method)
    fake = AstroidBuilder(MANAGER).string_build("def %s(): pass" % methodname)
    return  {0:fake[methodname]}

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

