# pylint:disable=C6666,R0201

from OpenOrange import *
from User import User
from RetroactiveAccounts import RetroactiveAccounts

class HeirFinder(RetroactiveAccounts):

    def doReplacements(self, txt):
        d = {1:"ONE", 2:"TWO"}
        us = User.bring("USER")
        txt = txt.replace(":1", us.Name + d[1])
        return txt

    def run(self):
        query8 = self.getQuery()
        query8.sql = self.doReplacements(query8.sql)
        #pylint:disable=E6601
        query8.open() #there will be missing tables here
