"""
Checks that Pylint does not complain about SuperClass transform
"""
from OpenOrange import *

ParentMyRecord = SuperClass("MyRecord", "MyInheritance", __file__)
class MyRecord(ParentMyRecord):
    pass
