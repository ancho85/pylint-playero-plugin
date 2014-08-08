from xml.sax import make_parser, handler

from globalfunctions import getSettingsFileName

class SettingsFile(object):
	# this actually ain't a file but who cares?

	class SettingsFileHandler(handler.ContentHandler):
		def __init__(self):
			self.__currentElement = None
			self.timezone = None
			self.database = None
			self.services = []
		def startElement(self, name, attrs):
			self.__currentElement = name
			if name == "timezone":
				self.timezone = ""
			elif name == "database":
				self.database = attrs
			elif name == "service-entry":
				self.services.append({
					"class": attrs["class"]
				})
		def endElement(self, name):
			self.__currentElement = None
		def characters(self, data):
			if self.__currentElement == "timezone":
				self.timezone += data

	def __init__(self, xmlfile):
		parser = make_parser()
		parser.setFeature(handler.feature_namespaces, 0)
		xmlhandler = self.__class__.SettingsFileHandler()
		parser.setContentHandler(xmlhandler)
		parser.parse(xmlfile)
		self._xmlhandler = xmlhandler
		self.__timezone = xmlhandler.timezone

	@classmethod
	def getInstance(cls, xmlfile=None):
		if not xmlfile:
			xmlfile = getSettingsFileName()
		return cls(xmlfile)

	def getTimezone(self):
		return self.__timezone

	def getDatabase(self):
		return self._xmlhandler.database

	def getServices(self):
		return self._xmlhandler.services
