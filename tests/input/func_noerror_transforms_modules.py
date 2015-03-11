"""
Checks that Pylint does not complain about reserved words
"""
# pylint:disable=C6666
from OpenOrange import *

ParentInvoice = SuperClass("Invoice", "SalesTransaccion", __file__)
class Invoice(ParentInvoice):
    rec = NewRecord("Invoice")

ParentInvoiceWindow = SuperClass("InvoiceWindow", "SalesTransactionWindow", __file__)
class InvoiceWindow(ParentInvoiceWindow):
    win = NewWindow("InvoiceWindow")

ParentInvoiceResume = SuperClass("InvoiceResume", "Report", __file__)
class InvoiceResume(ParentInvoiceResume):
    rep = NewReport("InvoiceResume")
