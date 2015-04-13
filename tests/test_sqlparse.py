import unittest
from libs.funcs import getConfig, CONFIGPATH
from libs.sqlparse import parseSQL, cmdValidateSQL, apiValidateSQL, validateSQL

class TestSqlParse(unittest.TestCase):

    def setUp(self):
        self.q1 =  "SELECT [al].{SerNr}, [ar].{Qty}, [ar].{RoomType} FROM Alotment al "
        self.q1 += "INNER JOIN AlotmentRow ar ON [al].{internalId} = [ar].{masterId}"
        self.q2 =  "SELECT [al].{SerNr}, [ar].{Qty}, [ar].{RoomType}, " #Extra coma here
        self.q2 += "FROM Alotment al INNER JOIN AlotmentRow ar ON [al].{internalId} = [ar].{masterId};"
        self.q3 = "SELECT * FROM [NonExistentTable]"
        self.q4 = "SELECT SerNr FROM Alotment alias1 INNER JOIN Deposit alias1" #bad alias
        self.cfg = getConfig()

    def test_cmd(self):
        config = self.cfg
        config.set("mysql", "useapi", 0)

        res = cmdValidateSQL(parseSQL(self.q1), config)
        self.assertEqual(res, "", msg="This query is correct, but an [unknown] error ocurred. %s" % res)

        res = cmdValidateSQL(parseSQL(self.q2), config)
        self.assert_(res.find("'FROM") > -1, msg="The query parser has not detected the query [extra coma] error. %s" % res)

        res = cmdValidateSQL(parseSQL(self.q3), config)
        self.assert_(res.find("doesn't exist") > -1, msg="The query parser has not detected the [missing table] error. %s" % res)

        res = cmdValidateSQL(parseSQL(self.q4), config)
        self.assert_(res.find("Not unique table/alias") > -1, msg="The query parser has not detected the [alias] error. %s" % res)

    def test_api(self):
        prepare = lambda txt: parseSQL(txt).replace("\n", " ").replace(";", ";\n")

        config = self.cfg
        config.set("mysql", "useapi", 1)

        res = apiValidateSQL(prepare(self.q1), config)
        self.assertEqual(res, "", msg="This query is correct, but an [unknown] error ocurred.\n%s" % res)

        res = apiValidateSQL(prepare(self.q2), config)
        self.assert_(res.find("'FROM") > -1, msg="The query parser has not detected the query [extra coma] error. %s" % res)

        res = apiValidateSQL(prepare(self.q3), config)
        self.assert_(res.find("doesn't exist") > -1, msg="The query parser has not detected the [missing table] error. %s" % res)

        res = apiValidateSQL(parseSQL(self.q4), config)
        self.assert_(res.find("Not unique table/alias") > -1, msg="The query parser has not detected the [alias] error. %s" % res)

    def test_validate(self):
        tests = {"nodb": "MySQL database is not configured. Check playero.cfg file",
                    "nopass":"MySQL password is not configured. Check playero.cfg file",
                    "wrongdb":"ERROR 1049 Unknown database 'dbnone'",
                    "wrongpass":"ERROR 1045 Access denied for user"
                    }
        for checkpoint in tests:
            config = getConfig() #re read
            config.set("mysql", "useapi", 1)
            if checkpoint == "nodb":
                config.set("mysql", "dbname", "databasename")
            elif checkpoint == "nopass":
                config.set("mysql", "pass", "******")
            elif checkpoint == "wrongdb":
                config.set("mysql", "dbname", "dbnone")
            elif checkpoint == "wrongpass":
                config.set("mysql", "pass", "666")
            config.write(open(CONFIGPATH, "wb")) #write wrong config

            res = validateSQL(self.q1)
            self.assert_(res.find(tests[checkpoint]) > -1, msg="%s, %s" % (checkpoint, res))

            self.cfg.write(open(CONFIGPATH, "wb")) # rewrite good config

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSqlParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
