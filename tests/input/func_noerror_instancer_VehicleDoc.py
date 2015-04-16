from OpenOrange import *
from Document import Document

class VehicleDoc(Document):

    def run(self):
        var = self.getRecord()
        self.setStringValue("Chapa", var.Plate)
