# pylint:disable=R0201

from OpenOrange import *
from Transaction import Transaction

class Alotment(Transaction):

    def run3(self):
        query4 = Query()
        query4.sql = "SELECT SerNr FROM Alotment\n"
        query4.sql += "WHERE?AND OriginType = i|%s| \n" % self.Origin.get('Invoice', 0)
        query4.sql += "AND SerNr = i|%s| " % self.Origin[self.name()]
        query4.open()
