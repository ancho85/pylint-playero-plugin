class ScrollArea(object):
	def __init__(self):
		self.__labelColor = None
		self.__labelFont = None
		self.__labelSize = None
		self.__viewVerticalLines = True
		self.__viewHorizontalLines = True
		self.__widthV = 10
		self.__widthH = 10
		self.__heightV = 10
		self.__heightH = 10
		self.__bgColor = None
		self.__structure = None
	def getDataDict(self):
		return {
			"labelColor": self.__labelColor,
			"labelFont": self.__labelFont,
			"labelSize": self.__labelSize,
			"viewVerticalLines": self.__viewVerticalLines,
			"viewHorizontalLines": self.__viewHorizontalLines,
			"widthV": self.__widthV,
			"widthH": self.__widthH,
			"heightV": self.__heightV,
			"heightH": self.__heightH,
			"bgColor": self.__bgColor,
			"structure": self.__structure.getSerializable()
		}
	def setStructure(self, structure):
		self.__structure = structure
	def getStructure(self):
		return self.__structure
	def setLabelColor(self, color):
		self.__labelColor = color
	def setPercentVertical(self, percent):
		pass
	def setBackGroundColor(self, color):
		self.__bgColor = color
	def viewVerticalLines(self, bool):
		self.__viewVerticalLines = bool
	def viewHorizontalLines(self, bool):
		self.__viewHorizontalLines = bool
	def setLabelFont(self, fontname, fontsize):
		self.__labelFont = fontname
		self.__labelSize = fontsize
	def setWidthV(self, w):
		self.__widthV = w
	def setWidthH(self, w):
		self.__widthH = w
	def setHeightH(self, h):
		self.__heightH = h
	def setHeightV(self, h):
		self.__heightV = h
