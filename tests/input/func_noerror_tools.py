# -*- coding: utf-8 -*-
# pylint:disable=C6666

from libs.tools import latinToAscii, embeddedImport, includeZipLib, isNumber

latinToAscii(u"áéíóúÇßþ")

embeddedImport("Query")

includeZipLib("__init__") # No zip anymore, added for future coverage

isNumber(int) #covers TypeError
