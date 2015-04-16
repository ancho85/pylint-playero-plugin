from OpenOrange import *
from Routine import Routine

class DelTransaction(Routine):

    def run(self):
        specs = self.getRecord()
        print specs.TableName
