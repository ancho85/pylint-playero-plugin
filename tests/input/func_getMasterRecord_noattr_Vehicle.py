# pylint:disable=R0201,W0622
from OpenOrange import *

ParentVehicle = SuperClass("Vehicle", "Master", __file__)
class Vehicle(ParentVehicle):
    pass

ParentVehicleRow = SuperClass("VehicleRow", "Record", __file__)
class VehicleRow(ParentVehicleRow):

    def doRow(self):
        veMaster = self.getMasterRecord()
        print veMaster.Plate
        veMaster.pasteHookedVehicle()
        veMaster.pasteHookedVehicle1()
