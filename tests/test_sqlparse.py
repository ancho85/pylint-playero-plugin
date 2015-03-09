import os
import sys
import unittest
import ConfigParser
from libs.funcs import getConfig
from libs.sqlparse import parseSQL, cmdValidateSQL, apiValidateSQL

class TestSqlParse(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestSqlParse, self).__init__(*args, **kwargs)
        self.q1 =  "SELECT [al].{SerNr}, [ar].{Qty}, [ar].{RoomType} FROM Alotment al "
        self.q1 += "INNER JOIN AlotmentRow ar ON [al].{internalId} = [ar].{masterId}"
        self.q2 =  "SELECT [al].{SerNr}, [ar].{Qty}, [ar].{RoomType}, " #Extra coma here
        self.q2 += "FROM Alotment al INNER JOIN AlotmentRow ar ON [al].{internalId} = [ar].{masterId};"
        self.q3 = "SELECT * FROM [NonExistentTable]"

    def test_cmd(self):
        config = getConfig()
        config.set("mysql", "useapi", "0")

        res = cmdValidateSQL(parseSQL(self.q1), config)
        self.assertEqual(res, "", msg="This query is correct, but an [unknown] error ocurred. %s" % res)

        res = cmdValidateSQL(parseSQL(self.q2), config)
        self.assert_(res.find("'FROM") > -1, msg="The query parser has not detected the query [extra coma] error. %s" % res)

        res = cmdValidateSQL(parseSQL(self.q3), config)
        self.assert_(res.find("doesn't exist") > -1, msg="The query parser has not detected the [missing table] error. %s" % res)

    def test_api(self):
        prepare = lambda txt: parseSQL(txt).replace("\n", " ").replace(";", ";\n")

        config = getConfig()
        config.set("mysql", "useapi", "1")

        res = apiValidateSQL(prepare(self.q1), config)
        self.assertEqual(res, "", msg="This query is correct, but an [unknown] error ocurred.\n%s" % res)

        res = apiValidateSQL(prepare(self.q2), config)
        self.assert_(res.find("'FROM") > -1, msg="The query parser has not detected the query [extra coma] error. %s" % res)

        res = apiValidateSQL(prepare(self.q3), config)
        self.assert_(res.find("doesn't exist") > -1, msg="The query parser has not detected the [missing table] error. %s" % res)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSqlParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
