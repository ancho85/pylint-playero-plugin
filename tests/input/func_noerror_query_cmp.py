# pylint:disable=R0201

from OpenOrange import *

class AttributeCompare(object):

    def __init__(self):
        self.Option = None
        self.OtherOption = ""

    def getRecorda(self):
        ac = AttributeCompare()
        ac.Option = 1
        ac.OtherOption = "Enabled"
        return ac

    def run(self):
        specs = self.getRecorda()
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
