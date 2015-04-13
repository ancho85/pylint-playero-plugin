# pylint:disable=R0201

from OpenOrange import *
from User import User
from Window import Window
from TaxSettings import TaxSettings
from FinSettings import FinSettings

class WindowA(Window):

    def doMore(self, cond):
        txt = ""
        if cond:
            txt = ""
        return txt

    def run(self):
        tx = TaxSettings.bring()
        fcs = FinSettings.bring()
        value = User.getStockDepo(currentUser())
        query6 = Query()
        query6.sql = "SELECT * FROM Alotment WHERE SerNr IN ('%s')\n" % value
        query6.sql += "AND SerNr = s|%s|" % tx.CredPayTermAsCash
        query6.sql += self.doMore(not fcs.CLFromChangeValues)
        query6.open()
