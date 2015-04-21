from OpenOrange import *

ParentVehicle = SuperClass("Vehicle", "Master", __file__)
class Vehicle(ParentVehicle):

    def defaults(self):
        from AirMilesCard import AirMilesCard
        amcBring = AirMilesCard.bring("1") #returns buffered instance of AirMilesCard
        amcLoad = AirMilesCard()
        amcLoad.load() #creates a fresh instance of AirMilesCard

        print amcBring.Code
        amcBring.isFlotaPrepaid()

        print amcLoad.Code
        print amcLoad.Closed
        amcLoad.checkCode()
        amcLoad.isFlotaPrepaid()

        from DocumentLink import DocumentLink
        documentlink = DocumentLink.bring("ABC")
        print documentlink.Specs

        from PySettings import PySettings
        pys = PySettings.bring()
        print pys.LogTransactionsImportantChanges

ParentVehicleRow = SuperClass("VehicleRow", "Record", __file__)
class VehicleRow(ParentVehicleRow):

    def doRow(self):
        veMaster = self.getMasterRecord() #returns buffered instance of AirMilesCard
        print veMaster.Code
        veMaster.pasteHookedVehicle()

    def pasteCustCode(self):
        from Customer import Customer
        cus = Customer.bring(self.internalId)
        print cus.Name
