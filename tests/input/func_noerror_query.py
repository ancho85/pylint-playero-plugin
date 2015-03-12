# pylint:disable=C6666

from OpenOrange import *
from Routine import Routine
from Document import Document
from Label import Label
from SQLTools import codeOrder, monthCode

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

class AlotmentDoc(Document):

    classattr = "classattr"

    def getRecorda(self):
        class newObj(object):
            Status = 1
            RootLabel = "100"
            SerNr = "SerNr"
            def name(self):
                print str(self)
                return "Alotment"
        return newObj()

    def getExtra(self, val1, val2="2", val3="3", val4=4):
        specs = self.getRecorda()
        sql = "WHERE?AND [al].{%s} IN ('%s')\n" % ("SerNr", "','".join([val1, val3, val2]))
        sql += "WHERE?AND [al].{SerNr} = i|%i|\n" % specs.Status
        sql += "WHERE?AND SerNr = "
        if specs.Status == 1:
            sql += "%s" % val4
        if 1 in [0, 0]:
            pass
        else:
            sql += ""
        return sql

    def getExtra2(self, test):
        parent = self
        specs = self.getRecorda()
        #mydict = {1:1, 2:2}
        #mylist = [1, 2]
        listcomp = "listcomp"
        if test > 0:
            return specs.Status
        x =  "'%s', " % date("")
        x += "'%s', " % time("")
        x += "'%i', " % len(specs.RootLabel)
        x += "'%s', " % filter(None, ["1","2"])
        x += "'%s', " % map(str, specs.Status)
        #x += "'%s', " % ("""%s""" % mydict.keys())
        x += "'%s', " % self.classattr.replace("i", "a")[0]
        x += "'%s', " % self.classattr.split(",")[0]
        #x += "'%s', " % mylist.extend([2])
        x += "'%s', " % self.classattr
        #x += "'%s', " % ("""%s""" % mydict)
        x += "'%s', " % parent.record #Parent None attribute
        #x += "'%s', " % ("""%s""" % mylist + mylist)
        #x += "'%s', " % ("""%s""" % [a for a in mylist])
        #x += "'%s', " % "".join([("%s" % d) for d in listcomp])
        x += "'%s', " % "".join([str(b) for b in listcomp])
        x += "'%s' " % "".join([c.strip() for c in listcomp])
        return x

    def getExtra3(self):
        specs = self.getRecorda()
        subquery = Query()
        subquery.sql = "SerNr"
        return "ORDER BY %s, %s" % (specs.SerNr, subquery.sql)

    def run(self):
        specs = self.getRecorda()
        leaves = Label.getTreeLeaves(specs.RootLabel)
        query = Query()
        query.sql = "SELECT SerNr, %s,\n" % codeOrder("SerNr", leaves)
        query.sql += monthCode("[al].TransDate")
        query.sql += "\n, %s" % self.getExtra2(test=1)
        query.sql += "\n, %s" % self.getExtra2(test=0)
        query.sql += "\nFROM %s al\n" % specs.name()
        query.sql += self.getExtra("1", "2", val3="33")
        method = getattr(self, "getExtra3lala"[:-4])
        query.sql += method()
        query.open()
