# -*- coding: utf-8 -*-
import unittest
from libs.tools import *

class TestTools(unittest.TestCase):

    def test_latinToAscii(self):
        assert latinToAscii(u"Hönig") == "Honig"
        assert latinToAscii(u"€") == ""

    def test_embeddedImport(self):
        button = embeddedImport("Embedded_ButtonObj")
        assert hasattr(button, "Embedded_ButtonObj")

    def test_includeZipLib(self):
        includeZipLib("cache.py") #no zip available
        assert True

    def test_isNumber(self):
        assert isNumber(1) == True
        assert isNumber("No") == False
        assert isNumber(int) == False

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSqlParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
