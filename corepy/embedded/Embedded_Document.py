import os

class Embedded_Document(object):
    def __init__(self):
        self.__parameter = None
    def setParameter(self, p):
        self.__parameter = p
    def getParameter(self):
        return self.__parameter
