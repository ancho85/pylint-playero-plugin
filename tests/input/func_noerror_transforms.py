"""
Checks that Pylint does not complain about reserved words
"""
from OpenOrange import *

ParentMyRecord = SuperClass("MyRecord", "MyInheritance", __file__)
class MyRecord(ParentMyRecord):

    rec = NewRecord("MyRec")
    win = NewWindow("MyWin")
    rou = NewReport("MyRep")
