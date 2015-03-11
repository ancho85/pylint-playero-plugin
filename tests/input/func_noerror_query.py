# pylint:disable=C6666

from OpenOrange import *
from Routine import Routine

class InvoiceAlter(Routine):

    Status = 1

    def getRecorda(self):
        class newObj(object):
            def fieldNames(self):
                return ["ShowOther", "ShowAlotment", str(self)]
            def fields(self, fn):
                class fieldValue(object):
                    def getValue(self): return bool(fn + str(self))
                return fieldValue()
        return newObj()

    def getAlotmentQuery(self):
        specs = self
        sql = "SELECT 'Alotment' as RecordName, det.RoomType\n"
        sql += "FROM Alotment cab INNER JOIN AlotmentRow det on cab.internalId = det.masterId\n"
        sql += "WHERE?AND cab.Status = i|%s|\n" % specs.Status
        return sql

    def run(self):
        specs = self.getRecorda()
        query = Query()
        query.sql = " SELECT RecordName, RoomType FROM (\n"
        union = ""
        for fn in specs.fieldNames():
            if fn.startswith("Show"):
                if specs.fields(fn).getValue():
                    recname = fn[4:]
                    if hasattr(self, "get%sQuery" % recname):
                        MyMethod = getattr(self, "get%sQuery" % recname)
                        query.sql += union
                        query.sql += MyMethod()
                    union = "\nUNION ALL\n"

        query.sql += ") AS final \n"
        query.sql += "ORDER BY RoomType"
        query.open()
