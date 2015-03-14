# pylint:disable=C6666,R0201

from OpenOrange import *
from Report import Report
from Window import Window
from Routine import Routine
from Document import Document
from Label import Label
from User import User
from Transaction import Transaction
from TaxSettings import TaxSettings
from FinSettings import FinSettings
from SQLTools import codeOrder, monthCode
from SQLQueryTools import sqlCurConvert

class InvoiceAlter(Routine):

    Status = 1

    def getRecorda(self):
        class newObj(object):
            def fieldNames(self):
                return ["ShowOther", "ShowAlotment"]
            def fields(self, fn):
                class fieldValue(object):
                    def getValue(self): return bool(fn)
                return fieldValue()
        return newObj()

    def getAlotmentQuery(self):
        sql = "SELECT 'Alotment' as RecordName, det.RoomType\n"
        sql += "FROM Alotment cab INNER JOIN AlotmentRow det on cab.internalId = det.masterId\n"
        sql += "WHERE?AND cab.Status = i|%s|\n" % self.Status
        return sql

    def run(self):
        # pylint:disable=W0201
        self.specs = self.getRecorda()
        query1 = Query()
        query1.sql = " SELECT RecordName, RoomType FROM (\n"
        union = ""
        for fn in self.specs.fieldNames():
            if fn.startswith("Show"):
                if self.specs.fields(fn).getValue():
                    recname = fn[4:]
                    if hasattr(self, "get%sQuery" % recname):
                        MyMethod = getattr(self, "get%sQuery" % recname)
                        query1.sql += union
                        query1.sql += MyMethod()
                    union = "\nUNION ALL\n"

        query1.sql += ") AS final \n"
        query1.sql += "ORDER BY RoomType"
        query1.open()

class AlotmentDoc(Document):

    classattr = "classattr"

    def getRecorda(self):
        class newObj(object):
            Status = 1
            RootLabel = "100"
            SerNr = "SerNr"
            Labels = "100,200"
            def name(self):
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
        mydict = {1:1, 2:2}
        mylist = [1, 2]
        listcomp = "listcomp," + "extra"
        if test > 0:
            return specs.Status
        x =  "'%s' as test_date\n, "       % date("")
        x += "'%s' as test_time\n, "       % time("")
        x += "'%i' as test_len\n, "        % len(specs.RootLabel)
        x += "'%s' as test_filter\n, "     % filter(None, ["1","2"])
        x += "'%s' as test_map\n, "        % "','".join(map(str, mylist))
        x += "'%s' as test_keys\n, "       % "','".join(mydict.keys())
        x += "'%s' as test_subscript\n,"   % ["SerNr","RoomType"][specs.Status]
        #x += "'%s' as test_classattr\n, "  % self.classattr
        x += '"%s" as test_dic\n, '        % mydict
        x += "'%s' as test_parentattr\n, " % parent.record #Parent None attribute
        x += '"%s" as test_binoplist\n, '  % mylist #+ mylist
        x += '"%s" as test_listcomp1\n, '  % "".join([a.strip() for a in listcomp.split(',')])
        x += '"%s" as test_listcomp2\n, '  % "".join([d for d in listcomp])
        x += '"%s" as test_listcomp3\n, '  % "".join([str(b) for b in listcomp])
        x += '"%s" as test_listcomp4\n,'   % "".join([c.strip() for c in listcomp])
        x += '"%s" as test_listcomp5\n,'   % [('s|%s|') % (z) for z in mylist]
        x += '"%s" as test_listcomp6\n,'   % "".join([y for y in ("a", "b")])
        # pylint:disable=E1101
        x += '"%s" as inferenceErr\n,'    % self.non.existant
        x += '"%s" as indexErr\n'    % mylist[2]
        return x

    def getExtra3(self):
        specs = self.getRecorda()
        subquery = Query()
        subquery.sql = "SerNr"
        return "ORDER BY %s, %s" % (specs.SerNr, subquery.sql)

    def getExtra4(self):
        specs = self.getRecorda()
        labels = None
        if specs.Labels:
            lis = []
            labs = specs.Labels.split(",")
            for lb in labs:
                lis.append("','".join(Label.getTreeLeaves(lb)))
            labels = "','".join(lis)
        return "WHERE?AND SerNr IN ('%s') " % labels

    def getExtra5(self, txt):
        txt = txt.replace(":1","RoomType IS NULL\n")
        return txt

    def getExtra6(self):
        txt = ""
        q = {}
        q["one"] = Query()
        q["one"].sql = "WHERE?AND SerNr IS NULL\n"
        q["two"] = Query()
        q["two"].sql = "WHERE?AND SerNr IS NOT NULL\n"
        slist = ["one", "two"]
        for index in slist:
            txt += q[index].sql
        return txt

    def getExtra7(self):
        specs = self.getRecorda()
        factor = 0.0
        if 1 > 0:
            factor = (float(specs.Status) / float(specs.Status))
        txt = "WHERE?AND (%s / 1) * %s > 0\n" % (1, factor)
        return txt

    def run(self):
        specs = self.getRecorda()
        leaves = Label.getTreeLeaves(specs.RootLabel)
        query7 = Query()
        query7.sql = "SELECT SerNr, %s,\n" % codeOrder("SerNr", leaves)
        query7.sql += monthCode("[al].TransDate")
        query7.sql += "\n, %s, \n" % self.getExtra2(test=1)
        query7.sql += self.getExtra2(0)
        query7.sql += "\nFROM %s al\n" % specs.name()
        query7.sql += self.getExtra("1", "2", val3="33")
        query7.sql += self.getExtra4()
        query7.sql += self.getExtra5("WHERE?AND :1")
        query7.sql += self.getExtra6()
        query7.sql += self.getExtra7()

        method = getattr(self, "getExtra3____"[:-4])
        query7.sql += method()
        query7.open()
        self.run2([100, 200])

    def run2(self, extraList):
        query2 = Query()
        query2.sql = self.getMore(extraList)
        query2.open()

    def getMore(self, moreList):
        return "SELECT * FROM Alotment WHERE SerNr IN ('%s')" % "','".join(moreList)

class Alotment(Transaction):

    def run3(self):
        query4 = Query()
        query4.sql = "SELECT SerNr FROM Alotment\n"
        query4.sql += "WHERE?AND OriginType = i|%s| \n" % self.Origin.get('Invoice', 0)
        query4.sql += "AND SerNr IN \n"
        query4.sql += (1, 2, 3)
        query4.sql += "AND SerNr = i|%s| " % self.Origin[self.name()]
        query4.open()
class ReportA(Report):

    def run(self):
        query5 = Query()
        query5.sql = "SELECT Total, "
        query5.sql += sqlCurConvert("Deposit", "Total", 2)
        query5.sql += "FROM Deposit\n"
        query5.sql += "WHERE Status = b|TRUE|\n"
        query5.open()

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

        query7 = Query()
        query7.sql = "SHOW INNODB STATUS"
        query7.open()

from RetroactiveAccounts import RetroactiveAccounts
class HeirFinder(RetroactiveAccounts):

    def doReplacements(self, txt):
        d = {1:"ONE", 2:"TWO"}
        us = User.bring("USER")
        txt = txt.replace(":1", us.Name + d[1])
        return txt

    def run(self):
        query = self.getQuery() #bug detected, getQuery setups a query name that may be different to the one defined here. Issue #24
        query.sql = self.doReplacements(query.sql)
        #pylint:disable=E6601
        query.open() #there will be missing tables here
