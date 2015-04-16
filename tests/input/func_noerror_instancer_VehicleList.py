from OpenOrange import *
from Report import Report

class VehicleList(Report):

    def run(self):
        record = self.getRecord() #returns buffered instance of VehicleList Report
        print record.MoreData
