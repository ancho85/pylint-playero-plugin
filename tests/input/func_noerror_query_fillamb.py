# pylint:disable=R0201,W0110

from OpenOrange import *

class AlotmentRow(object):

    def getRecorda(self):
        class newObj(object):
            Labels = "100,200"
        return newObj()

    def run3(self):
        record = self.getRecorda()
        labels = filter(lambda x: x.strip().find(':') < 0, record.Labels.split(','))
        qinf = Query()
        qinf.sql = "SELECT SerNr FROM [Alotment]"
        if (record.Labels):
            if len(labels):
                qinf.sql += " WHERE?AND ("
                OR = ""
                for lab in labels:
                    qinf.sql += OR + "SerNr = s|%s|" % lab
                    OR = " OR "
                qinf.sql += ")"
        qinf.open()
