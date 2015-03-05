import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..")) #pylint_playero_plugin path added to environment
from libs.funcs import getConfig
from libs.sqlparse import parseSQL, cmdValidateSQL, apiValidateSQL

class TestSqlParse(unittest.TestCase):

    def getCommonConfig(self):
        config = getConfig()
        config.set("mysql", "connect", "1")
        config.set("mysql", "dbname", "playero")
        config.set("mysql", "host", "127.0.0.1")
        config.set("mysql", "user", "travis")
        config.set("mysql", "pass", "")
        return config

    def test_cmd(self):
        config = self.getCommonConfig()
        config.set("mysql", "useapi", "0")

        txt = """SELECT [al].{SerNr}, [ar].{Qty}, [ar].{RoomType} FROM Alotment al
                 INNER JOIN AlotmentRow ar ON [al].{internalId} = [ar].{masterId}"""
        txt = "%s%s%s" % ("START TRANSACTION;\n", parseSQL(txt), ";\nROLLBACK;\n")
        res = cmdValidateSQL(txt, config)
        self.assertEqual(res, "")


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSqlParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
