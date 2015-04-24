import unittest
from libs.funcs import *

class TestFuncs(unittest.TestCase):

    def test_buildPaths(self):

        recPaths, repPaths, rouPaths, corePaths = buildPaths()
        findTxt = lambda x, y: x.find(y) > -1

        assert findTxt(recPaths["Task"][0], "base")
        assert findTxt(recPaths["Department"][0], "StdPy")
        assert findTxt(recPaths["Department"][1], "standard")

        assert findTxt(repPaths["ListWindowReport"][0], "base")
        assert findTxt(repPaths["ExpensesList"][0], "StdPy")
        assert findTxt(repPaths["ExpensesList"][1], "standard")

        assert findTxt(rouPaths["GenNLT"][0], "StdPy")
        assert findTxt(rouPaths["GenNLT"][1], "standard")
        assert findTxt(corePaths["Field"][0], "embedded")

        self.assertFalse([k for (k, v) in rouPaths.iteritems() if findTxt(v[0], "base")]) #no routines in base

    def test_recordInheritance(self):
        recf, recd = getRecordInheritance("Invoice")
        assert all([f1 in recf for f1 in ("SalesMan", "InvoiceDate", "CustCode", "Currency", "ShiftDate", "OriginNr", "SerNr", "attachFlag")])
        assert all([d in recd for d in ("CompoundItemCosts", "Payments", "Items", "Taxes", "Installs")])

        recf, recd = getRecordInheritance("AccessGroup")
        assert all([f2 in recf for f2 in ("PurchaseItemsAccessType", "InitialModule", "Closed", "internalId")])
        assert all([d in recd for d in ("PurchaseItems", "Customs", "Modules")])

    def test_recordsInfo(self):
        recf, recd = getRecordsInfo("Department", RECORD)
        assert recf["Department"]["AutoCashCancel"] == "integer" #From StdPy
        assert recf["Department"]["DeptName"]       == "string" #From standard
        assert recf["Department"]["Closed"]         == "Boolean" #From Master
        assert recf["Department"]["internalId"]     == "internalid" #From Record
        assert recd["Department"]["OfficePayModes"] == "DepartmentOfficePayModeRow" #Recordname from detail

        repf, repd = getRecordsInfo("Balance", REPORT)
        assert repf["Balance"]["LabelType"]         == "string" #StdPy
        assert repf["Balance"]["ExplodeByLabel"]    == "boolean" #Standard
        assert repf["Balance"]["internalId"]        == "internalid" #Record
        assert not repd["Balance"] #Empty dict, no detail

        rouf, roud = getRecordsInfo("GenNLT", ROUTINE)
        assert rouf["GenNLT"]["ExcludeInvalid"]     == "boolean"
        assert rouf["GenNLT"]["Table"]              == "string"
        assert not roud["GenNLT"]

        rouf, roud = getRecordsInfo("LoginDialog", RECORD)
        assert rouf["LoginDialog"]["Password"]      == "string" #embedded
        assert not roud["LoginDialog"]

    def test_classInfo(self):
        attr, meth = getClassInfo("Invoice")
        assert attr["DEBITNOTE"]     == 2
        assert attr["ATTACH_NOTE"]   == 3
        assert attr["rowNr"]         == 0
        assert attr["ParentInvoice"] == "SuperClass"
        assert isinstance(attr["DocTypes"], list)
        assert isinstance(attr["Origin"], dict)
        assert all([m in meth for m in ("getCardReader", "logTransactionAction", "updateCredLimit",
            "generateTaxes", "roundValue", "getOriginType", "bring", "getXML", "createField")])
        assert meth["fieldIsEditable"][0] == "self"
        assert meth["fieldIsEditable"][1] == "fieldname"
        assert meth["fieldIsEditable"][2] == {"rowfieldname":'None'}
        assert meth["fieldIsEditable"][3] == {"rownr":'None'}

        attr, meth = getClassInfo("User", "Master")
        assert attr["buffer"] == "RecordBuffer"
        assert all([m in meth for m in ("store", "save", "load")])

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFuncs))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
