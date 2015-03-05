import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.join(HERE, ".."))) #pylint_playero_plugin path added to environment
from libs.pyparse import parseScript

class TestPyParse(unittest.TestCase):

    def test_embeddedRecordDef(self):
        filepath = os.path.join(HERE, '..', 'corepy', 'embedded', 'RecordDef.py')
        par = parseScript(filepath)
        self.assertTrue([attr for attr in ("base_class", "instances", "InternalIdDef") if attr in par.attributes])
        self.assertTrue([meth for meth in ("isDetail", "getParentDef", "getRecordClass") if meth in par.methods])
        self.assertEqual(par.inheritance["DetailRecordDef"], "RecordDef")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPyParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
