# pylint:disable=R0201

from OpenOrange import *

class SubQuery(object):

    def run(self):
        query = Query()
        query.sql =  "SELECT Total\n"
        query.sql += "FROM Deposit\n"
        query.sql += "WHERE SerNr NOT IN (SELECT SerNr FROM Deposit) "
        query.open()
