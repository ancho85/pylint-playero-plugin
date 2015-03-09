import os
import sys
import unittest
from libs.pyparse import parseScript

def getFilePath(filename):
    HERE = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(HERE, '..', 'corepy', 'embedded', filename)

class TestPyParse(unittest.TestCase):

    def test_embeddedRecordDef(self):
        filepath = getFilePath("RecordDef.py")
        par = parseScript(filepath)
        for attr in ("base_class", "instances", "InternalIdDef"):
            self.assertTrue(attr in par.attributes, msg="%s not in RecordDef attributes" % attr)
        for meth in ("isDetail", "getParentDef", "getRecordClass"):
            self.assert_(meth in par.methods, msg="%s not in RecordDef methods" % meth)
        self.assertEqual(par.inheritance["DetailRecordDef"], "RecordDef")

    def test_embeddedQuery(self):
        filepath = getFilePath("Query.py")
        par = parseScript(filepath)
        self.failUnless(["result", "sql"] == par.attributes.keys())
        self.assertFalse(bool([meth for meth in ("getSQL", "setSQL", "parseSQL") if meth not in par.methods]))
        self.failIf(par.inheritance["Query"] != "object")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPyParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
