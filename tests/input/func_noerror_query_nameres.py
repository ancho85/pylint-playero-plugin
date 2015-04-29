from OpenOrange import *

class QueryNameRes(object):

    def getQuery(self):
        sqlStr = "SELECT cab.Office, cab.Computer, cab.SerNr, cab.TransDate FROM Alotment cab\n"
        if True:
            sqlStr += "LEFT JOIN (SELECT SerNr FROM Deposit) de ON\n"
            sqlStr += "(de.SerNr = cab.SerNr)\n"
        return sqlStr

    def run(self):
        query = Query()
        query.sql = self.getQuery()
        if query.open():
            pass
