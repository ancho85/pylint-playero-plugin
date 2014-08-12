import os

class Embedded_Document(object):
    def __init__(self):
        self.__parameter = None
        self.__field_decimals__ = {}
        self.documentspec = None
        self.record = None
    def setParameter(self, p):
        self.__parameter = p
    def getParameter(self):
        return self.__parameter
    def currentPageNr(self):
        return 0
    def getDocumentSpec(self):
        return self.documentspec
    def setDocumentSpec(self, docinfo, record):
        self.documentspec = docinfo
        self.record = record
    def clearPrinter(self, document):
        self.documentspec = document
        self.documentspec = None

    def printDocument(self):
        record = self.record
        if not hasattr(record, "_one_preview") or not record._one_preview:
            document = self.getDocumentSpec()
            if document:
                if document.ShowOnlyOnePreview:
                    record.printAllCopies(False, None, None)
                    self.clearPrinter(document)
                    if hasattr(record,"afterPrint"):
                        record.afterPrint(document)
                    return True
        return False
