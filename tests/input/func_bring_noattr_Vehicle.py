# pylint:disable=R0201,W0622
from OpenOrange import *

ParentVehicle = SuperClass("Vehicle", "Master", __file__)
class Vehicle(ParentVehicle):

    def doStuff(self):
        from PySettings import PySettings
        pys = PySettings.bring()
        print pys.NonExistant
