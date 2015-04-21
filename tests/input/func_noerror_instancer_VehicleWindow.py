from OpenOrange import *

ParentVehicleWindow = SuperClass("VehicleWindow", "Window", __file__)
class VehicleWindow(ParentVehicleWindow):

    def doWin(self):
        veRecord = self.getRecord() #returns buffered instance of AirMilesCard
        print veRecord.Code
        veRecord.pasteHookedVehicle()

modlevelVehicle = VehicleWindow.getRecord()
print modlevelVehicle.Code
