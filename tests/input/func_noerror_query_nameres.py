from OpenOrange import *

class QueryNameRes(object):

    def getQuery(self):
        sqlStr = "SELECT cab.Office, cab.Computer, cab.SerNr, cab.TransDate FROM Alotment cab\n"
        having = "HAVING"
        if self:
            sqlStr += "LEFT JOIN (SELECT SerNr FROM Deposit) de ON\n"
            sqlStr += "(de.SerNr = cab.SerNr)\n"
        sqlStr += "GROUP BY cab.Office\n"
        if not self:
            sqlStr += " %s cab.Office " % having
            sqlStr += "IS NOT NULL\n"
            having = "AND "
        sqlStr += " %s cab.Computer IS NOT NULL\n" % having
        sqlStr += " %s cab.SerNr IS NOT NULL\n" % having
        sqlStr += " %s cab.TransDate IS NOT NULL\n" % having
        return sqlStr

    def run(self):
        query = Query()
        query.sql = self.getQuery()
        if query.open():
            pass
