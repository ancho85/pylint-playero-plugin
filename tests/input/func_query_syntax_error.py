# pylint:disable=C6666,R0201

from OpenOrange import *

errQuery = Query()
errQuery.sql = "SELECT SerNr, FROM Alotment"
errQuery.open()
