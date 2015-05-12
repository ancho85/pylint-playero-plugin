# pylint:disable=R0201

from OpenOrange import *

class AttributeCompare(object):

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
        if specs.OtherOption:
            query.sql += "HAVING SerNr > 0\n"
        query.open()
