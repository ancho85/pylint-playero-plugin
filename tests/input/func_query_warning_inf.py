# pylint:disable=C6666,R0201,E6601

from OpenOrange import *
import string

class AlotmentRow(object):

    def getRecorda(self):
        class newObj(object):
            Labels = "100,200"
        return newObj()

    def run3(self):
        record = self.getRecorda()
        qinf = Query()
        qinf.sql = "SELECT SerNr, "
        sumseq = string.join(record.Labels.split(","), "+")
        qinf.sql += "SUM(%s) AS Budget " %  sumseq
        qinf.sql += "FROM [Alotment]"
        qinf.open()
