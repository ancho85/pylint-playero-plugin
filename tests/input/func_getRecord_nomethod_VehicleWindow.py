from OpenOrange import *

ParentVehicleWindow = SuperClass("VehicleWindow", "Window", __file__)
class VehicleWindow(ParentVehicleWindow):

    def doWin(self):
        veRecord = self.getRecord() #returns buffered instance of AirMilesCard
        veRecord.pasteHookedVehicle1()
