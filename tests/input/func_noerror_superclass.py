"""
Checks that Pylint does not complain about SuperClasses
"""
from OpenOrange import *

MyInvoice = SuperClass("Invoice", "SalesTransaction", __file__)
class Invoice(MyInvoice):
    pass
