# pylint:disable=R0201

from OpenOrange import *

errQuery = Query()
errQuery.sql = "SELECT * FROM [playero].{MissingTable}"
errQuery.open()
