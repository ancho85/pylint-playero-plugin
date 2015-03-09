import unittest
from libs.funcs import buildPaths

class TestFuncs(unittest.TestCase):

    def test_buildPaths(self):

        recPaths, repPaths, rouPaths, corePaths = buildPaths()
        findTxt = lambda x, y: x.find(y) > -1

        assert findTxt(recPaths["Task"][0], "base")
        assert findTxt(recPaths["Department"][0], "StdPy")
        assert findTxt(recPaths["Department"][1], "standard")

        assert findTxt(repPaths["ListWindowReport"][0], "base")
        assert findTxt(repPaths["ExpensesList"][0], "StdPy")
        assert findTxt(repPaths["ExpensesList"][1], "standard")

        assert findTxt(rouPaths["GenNLT"][0], "StdPy")
        assert findTxt(rouPaths["GenNLT"][1], "standard")
        assert findTxt(corePaths["Field"][0], "embedded")

        self.assertFalse([k for (k, v) in rouPaths.iteritems() if findTxt(v[0], "base")]) #no routines in base


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFuncs))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
