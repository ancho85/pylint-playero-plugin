import os
import sys
import unittest
from logilab.common import testlib
from pylint.testutils import make_tests, LintTestUsingFile, cb_test_gen, linter
import ConfigParser

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGINPATH = os.path.join(HERE, "..")

linter.prepare_import_path(PLUGINPATH)
linter.load_plugin_modules(['Playero'])
linter.global_set_option('required-attributes', ())  # remove required __revision__
linter.load_file_configuration(os.path.join(HERE, "..", "config", ".pylintrc"))

convs = ['C0111', 'C0103', 'C0301', 'C0303', 'C0304', 'C0321']
warns = ['W0141', 'W0142', 'W0212', 'W0312', 'W0401', 'W0403', 'W0511', 'W0512', 'W0614', 'W0622']
refac = ['R0903', 'R0904', 'R0913']
for disabled in convs + warns + refac:
    linter.disable(disabled)

config = ConfigParser.SafeConfigParser()
config.read(os.path.join(HERE, "..", "config", "playero.cfg"))
PLAYEROPATH = config.get('paths', os.name)
sys.path.append(os.path.join(PLAYEROPATH, "core"))
for scriptdir in ["base", "standard", "StdPy"]:
    for pydir in ['records', 'windows', 'reports', 'routines', 'documents','tools']:
        sys.path.append(os.path.join(PLAYEROPATH, scriptdir, pydir))
sys.path.append(os.path.join(PLUGINPATH, "corepy", "embedded"))

def tests():
    callbacks = [cb_test_gen(LintTestUsingFile)]

    input_dir = os.path.join(HERE, 'input')
    messages_dir = os.path.join(HERE, 'messages')

    return make_tests(input_dir, messages_dir, None, callbacks)


def suite():
    return testlib.TestSuite([unittest.makeSuite(test, suiteClass=testlib.TestSuite)
                              for test in tests()])


if __name__ == '__main__':
    testlib.unittest_main(defaultTest='suite')
