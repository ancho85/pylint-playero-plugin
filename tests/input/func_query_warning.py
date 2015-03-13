# pylint:disable=C6666,R0201

from OpenOrange import *
from RetroactiveAccounts import RetroactiveAccounts

class QueryWarning(RetroactiveAccounts):

    def run(self):
        query = self.getQuery()
        query.open()
