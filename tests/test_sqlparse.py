import unittest
from libs.funcs import getConfig
from libs.sqlparse import parseSQL, cmdValidateSQL, apiValidateSQL, validateSQL

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

    def test_validate(self):
        bkpConfig = getConfig() #original good config

        HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        configLocation = os.path.join(HERE, "config", "playero.cfg")
        tests = {"nodb": "MySQL database is not configured. Check playero.cfg file",
                    "nopass":"MySQL password is not configured. Check playero.cfg file",
                    "wrongdb":"ERROR 1049 Unknown database 'dbnone'",
                    "wrongpass":"ERROR 1045 Access denied for user"
                    }
        for checkpoint in tests:
            config = self.readNewConfig(configLocation) #re read
            config.set("mysql", "useapi", 1)
            if checkpoint == "nodb":
                config.set("mysql", "dbname", "databasename")
            elif checkpoint == "nopass":
                config.set("mysql", "pass", "******")
            elif checkpoint == "wrongdb":
                config.set("mysql", "dbname", "dbnone")
            elif checkpoint in "wrongpass":
                config.set("mysql", "pass", "666")
            self.writeNewConfig(config, configLocation) #write wrong config

            res = validateSQL(self.q1)
            self.assert_(res.find(tests[checkpoint]) > -1, msg=res)
            self.writeNewConfig(bkpConfig, configLocation) # rewrite good config

    def readNewConfig(self, configLocation):
        config = ConfigParser.ConfigParser()
        config.readfp(open(configLocation))
        return config

    def writeNewConfig(self, config, configLocation):
        config.write(open(configLocation, "wb"))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSqlParse))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
