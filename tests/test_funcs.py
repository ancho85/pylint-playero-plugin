import os
import sys
import unittest
import ConfigParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..")) #pylint_playero_plugin path added to environment

class TestFuncs(unittest.TestCase):

    def test_buildPaths(self):
        config = ConfigParser.ConfigParser()
        configLocation = os.path.join(HERE, "..", "config", "playero.cfg")
        config.readfp(open(configLocation))
        config.set("paths", "posix", os.path.join(HERE, "..", "Playero/"))
        config.set("plugin_paths", "posix", os.path.join(HERE, ".."))
        config.write(open(configLocation, "wb"))
        from libs.funcs import buildPaths
        recPaths, repPaths, rouPaths, corePaths = buildPaths()
        print sorted(recPaths)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFuncs))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
