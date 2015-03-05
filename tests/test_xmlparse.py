import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..")) #pylint_playero_plugin path added to environment
from libs.xmlparse import parseRecordXML, parseRecordRowName, parseWindowRecordName, parseSettingsXML

def getFilePath(filename):
    return os.path.join(HERE, 'res', filename)

class TestXmlParse(unittest.TestCase):

    def test_record(self):
        filepath = getFilePath("res_record.xml")
        par = parseRecordXML(filepath)
        self.assertEqual(par.inheritance, "Master")
        self.failIf(par.isPersistent)
        self.failUnless("Data" in par.fields and par.fields["Data"] == "string")
        self.assertFalse("Activities" not in par.details)
        self.assert_(par.name == "RecordDataSearch")

    def test_row(self):
        filepath = getFilePath("res_rowrec.xml")
        par = parseRecordRowName(filepath)
        self.assertEqual(par.name, "AccessGroupReportRow")

    def test_window(self):
        filepath = getFilePath("res_window.xml")
        par = parseWindowRecordName(filepath)
        self.assertEqual(par.name, "LoginDialog")

    def test_setting(self):
        filepath = getFilePath("res_setting.xml")
        par = parseSettingsXML(filepath)
        self.failUnless(["base", "standard"] == par.scriptdirs)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestXmlParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
