import os

class Embedded_Document(object):
    def __init__(self):
        self.__parameter = None
        self.__field_decimals__ = {}
    def setParameter(self, p):
        self.__parameter = p
    def getParameter(self):
        return self.__parameter
    def currentPageNr(self):
        return 0
