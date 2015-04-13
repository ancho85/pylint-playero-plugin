# -*- coding: utf-8 -*-

from libs.tools import latinToAscii, embeddedImport, includeZipLib, isNumber

latinToAscii(u"áéíóúÇ")

embeddedImport("Query")

includeZipLib("__init__") # No zip anymore, added for future coverage

isNumber(int) #covers TypeError
