# pylint:disable=R0201

from OpenOrange import *

class MyWindow(object):

    def run(self):
        query = Query()
        query.sql = "SHOW INNODB STATUS"
        query.open()
