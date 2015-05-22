# pylint:disable=R0201,W0110

from OpenOrange import *

class AttributeCompare(object):

    def __init__(self):
        self.Option = None
        self.OtherOption = ""
        self.dbinfo = {}

    def getRecorda(self):
        ac = AttributeCompare()
        ac.Option = 1
        ac.OtherOption = "Enabled"
        return ac

    def run(self):
        specs = self.getRecorda()

        if (not specs.Option) or \
           (not specs.OtherOption) or \
           (specs.Option and specs.OtherOption):
            message("Combinacion de parametros no permitida")
            return
        tname = ""
        if (not tname in self.dbinfo.keys()):
            pass

        query = Query()
        query.sql = "SELECT SerNr, internalId, SUM(Total) FROM Alotment\n"
        if specs.Option == 1:
            query.sql += "GROUP BY SerNr\n"
        if specs.Option == 2:
            query.sql += "GROUP BY internalId\n"
        if False:
            query.sql += "GROUP BY TransDate\n"
        if not True:
            query.sql += "GROUP BY TransTime\n"
        a = specs.OtherOption
        if not a or specs.OtherOption != a:
            query.sql += "HAVING SerNr > 0\n"
        query.open()

        query2 = Query()
        query2.sql = "SELECT SerNr, internalId, SUM(Total) FROM Alotment\n"
        if False:
            query2.sql += "GROUP BY SerNr\n"
        else:
            query2.sql += "GROUP BY internalId\n"
        query2.open()

    def run2(self):
        query3 = Query()
        a, b, c, d, e, f, g = range(0, 7)
        scriptsDir = getScriptDirs(999999)
        if not len(filter(lambda x: x.find("Flota")>0, scriptsDir)):
            a = 6
            b = 5
        if not len(filter(lambda x: x.find("PayRollPy")>0, scriptsDir)):
            c = 4
        if not len(filter(lambda x: x.find("Copeg")>0, scriptsDir)):
            d = 3
        if not len(filter(lambda x: x.find("Ansa")>0, scriptsDir)):
            e = 2
        if not len(filter(lambda x: x.find("GasStationFrontier")>0, scriptsDir)):
            f = 1
            g = 0
        query3.sql = "SELECT %s" % (",".join(a, b, c, d, e, f, g))
        query3.open()
