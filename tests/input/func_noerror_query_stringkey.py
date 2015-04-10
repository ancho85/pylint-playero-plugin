# pylint:disable=C6666,R0201

from OpenOrange import *
from Report import Report
from SQLQueryTools import sqlCurConvert

class ReportA(Report):

    def run(self):
        query = Query()
        query.sql = "SELECT Total, "
        query.sql += sqlCurConvert("Deposit", "Total", 2)
        query.sql += "FROM Deposit\n"
        query.sql += "WHERE Status = b|TRUE|\n"
        query.open()
