from OpenOrange import *

ParentVehicle = SuperClass("Vehicle", "Master", __file__)
class Vehicle(ParentVehicle):

    def defaults(self):
        from AirMilesCard import AirMilesCard
        amcBring = AirMilesCard.bring(1) #returns buffered instance of AirMilesCard
        amcLoad = AirMilesCard()
        amcLoad.load() #creates a fresh instance of AirMilesCard

        print amcBring.Code
        amcBring.isFlotaPrepaid()

        print amcLoad.Code
        print amcLoad.Closed
        amcLoad.checkCode()
        amcLoad.isFlotaPrepaid()

ParentVehicleRow = SuperClass("VehicleRow", "Record", __file__)
class VehicleRow(ParentVehicleRow):

    def doRow(self):
        veMaster = self.getMasterRecord() #returns buffered instance of AirMilesCard
        print veMaster.Code
        veMaster.pasteHookedVehicle()
