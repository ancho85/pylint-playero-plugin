import os
import sys
import unittest
from libs.pyparse import parseScript
from libs.funcs import getPlayeroPath

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

    def test_funcDefDefaults(self):
        filepath = os.path.join(getPlayeroPath(), "standard", "reports", "AccountList.py")
        par = parseScript(filepath)
        self.failUnless(par.defaults["Type"] == 5)

    def test_inheritance(self):
        bases = {"User.py": "Master", "Master.py": "Record"}
        for fn, inhe in bases.iteritems():
            filepath = os.path.join(getPlayeroPath(), "base", "records", fn)
            par = parseScript(filepath)
            self.failUnless(par.inheritance[fn[:-3]] == inhe)

        cores = {"Record.py": "RawRecord", "RawRecord.py": "Embedded_Record"}
        for fn, inhe in cores.iteritems():
            filepath = os.path.join(getPlayeroPath(), "core", fn)
            par = parseScript(filepath)
            self.failUnless(par.inheritance[fn[:-3]] == inhe)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPyParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
