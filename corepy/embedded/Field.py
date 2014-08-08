from Embedded_OpenOrange import Embedded_Field
#from core.database.Database import Database
from decimal import Decimal

class Field(Embedded_Field):

    def __init__(self, record, fieldname_or_fielddef):
        Embedded_Field.__init__(self, record, fieldname_or_fielddef)

    def setValue(self, v):
        if isinstance(v, Decimal): v=float(v)
        return Embedded_Field.setValue(self, v)


    def getSQLValue(self):
        return None
        #return Database.getCurrentDB().parseFieldValue(self, False)

    def getPythonSQLValue(self):
        return None
        #return Database.getCurrentDB().parsePythonFieldValue(self)
