# pylint:disable=R0201

from OpenOrange import *

errQuery = Query()
errQuery.sql = "SELECT SerNr FROM Alotment alias1 INNER JOIN Deposit alias1"
errQuery.open()
