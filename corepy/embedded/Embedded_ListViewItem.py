class Embedded_ListViewItem(object):
	class Listener(object):
		def listViewItemModified(self):
			pass
		def childAdded(self, child):
			pass
	class ListViewItemListener(Listener):
		def __init__(self, parent, child):
			self.parent = parent
			self.child = child
		def listViewItemModified(self):
			self.parent.notifyModification()
		def childAdded(self, child):
			for l in self.parent.listeners:
				l.childAdded(child)
	def addListener(self, l):
		self.listeners.add(l)
		self.notifyModification()
		for child in self.children:
			l.childAdded(child)
	def notifyModification(self):
		for l in self.listeners:
			l.listViewItemModified()
	def __init__(self, parent=None):
		self.listeners = set()
		self.children = []
		self.texts = {}
		self.parent = None
		if parent:
			parent.appendChild(self)
			self.parent = parent
	def appendChild(self, child):
		child.addListener(self.__class__.ListViewItemListener(self, child))
		self.children.append(child)
		for l in self.listeners:
			l.childAdded(child)
		self.notifyModification()
	def setColumnText(self, text, i):
		self.texts[i] = text
		self.notifyModification()
	def selected(self):
		pass
	def getListView(self):
		if not self.parent:
			return
		return self.parent.getListView()
	def getColumnText(self, idx):
		return self.texts[idx]
	def getParent(self):
		return self.parent
