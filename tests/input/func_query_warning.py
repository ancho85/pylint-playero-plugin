# pylint:disable=R0201,E6601

from OpenOrange import *

class QueryWarning(object):

    def run(self):
        qw = Query()
        qw.open()
