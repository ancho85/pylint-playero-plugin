import os
import sys
import unittest
import ConfigParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..")) #pylint_playero_plugin path added to environment
from libs.sqlparse import parseSQL, cmdValidateSQL

class TestSqlParse(unittest.TestCase):

    def getCommonConfig(self):
        config = ConfigParser.ConfigParser()
        configLocation = os.path.join(HERE, "..", "config", "playero.cfg")
        config.readfp(open(configLocation))
        config.set("mysql", "connect", "1")
        config.set("mysql", "dbname", "playero")
        config.set("mysql", "host", "127.0.0.1")
        config.set("mysql", "user", "root")
        config.set("mysql", "pass", "")
        return config

    def test_cmd(self):
        config = self.getCommonConfig()
        config.set("mysql", "useapi", "0")

        txt =  "SELECT [al].{SerNr}, [ar].{Qty}, [ar].{RoomType} FROM Alotment al "
        txt += "INNER JOIN AlotmentRow ar ON [al].{internalId} = [ar].{masterId}"
        res = cmdValidateSQL(parseSQL(txt), config)
        self.assertEqual(res, "", msg="This query is correct, but an [unknown] error ocurred")

        txt =  "SELECT [al].{SerNr}, [ar].{Qty}, [ar].{RoomType}, " #Extra coma here
        txt += "FROM Alotment al INNER JOIN AlotmentRow ar ON [al].{internalId} = [ar].{masterId};"
        res = cmdValidateSQL(parseSQL(txt), config)
        self.assert_(res.find("'FROM") > -1, msg="The query parser has not detected the query [extra coma] error")

        txt = "SELECT * FROM [Invoice]"
        res = cmdValidateSQL(parseSQL(txt), config)
        self.assert_(res.find("doesn't exist") > -1, msg="The query parser has not detected the [missing table] error")



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSqlParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
