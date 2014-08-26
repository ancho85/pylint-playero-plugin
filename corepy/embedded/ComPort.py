from StringIO import StringIO

class ComPort(object):
	def __init__(self, portname):
		self.__portname = portname
		self.__out = StringIO()
		self.__in = StringIO("lalalalala")
	def setDtr(self, boolean):
		pass
	def setRts(self, boolean):
		pass
	def setParity(self, number):
		pass
	def setBaudRate(self, x):
		pass
	def setStopBits(self, number):
		pass
	def setDataBits(self, number):
		pass
	def setTimeout(self, number):
		pass
	def open(self):
		return True
	def close(self):
		return self.__out.close()
	def write(self, data):
		return self.__out.write(data)
	def bytesWaiting(self):
		return self.__in.len - self.__in.pos
	def getByte(self):
		return ord( self.__in.read(1) )
