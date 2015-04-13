"""
Checks that Pylint does not complain about reserved words
"""
from OpenOrange import *

ParentInvoice = SuperClass("Invoice", "SalesTransaccion", __file__)
class Invoice(ParentInvoice):
    rec = NewRecord("Invoice")
    print rec.SerNr

ParentInvoiceWindow = SuperClass("InvoiceWindow", "SalesTransactionWindow", __file__)
class InvoiceWindow(ParentInvoiceWindow):
    win = NewWindow("InvoiceWindow")
    win.printInvoiveDraft()
    win.getTitle()

ParentInvoiceResume = SuperClass("InvoiceResume", "Report", __file__)
class InvoiceResume(ParentInvoiceResume):
    rep = NewReport("InvoiceResume")
    rep.defaults()
    rep.getRecord()
