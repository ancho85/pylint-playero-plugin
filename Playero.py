from astroid import MANAGER
from astroid.builder import AstroidBuilder
from astroid import scoped_nodes

def hashlib_transform(module):
    if module.name == 'PayRollSettings':
        fake = AstroidBuilder(MANAGER).string_build('''

class Class_ZKclockOfficeIP(object):
    def __iter__(self):
        return self
''')
        module.locals["ZKclockOfficeIP"] = fake.locals["Class_ZKclockOfficeIP"] #For record rows


def register(linter):
    pass

MANAGER.register_transform(scoped_nodes.Class, hashlib_transform)

