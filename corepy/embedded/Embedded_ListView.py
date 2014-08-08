from Embedded_ListViewItem import Embedded_ListViewItem

class Embedded_ListView(object):
	class Listener(object):
		def listViewModified(self):
			pass
	def addListener(self, l):
		self.listeners.add(l)
	class ListViewItemListener(Embedded_ListViewItem.Listener):
		def __init__(self, listview, listviewitem):
			self.listview = listview
			self.listviewitem = listviewitem
		def listViewItemModified(self):
			self.listview.notifyModification()
		def childAdded(self, child):
			self.listview.registerItem(child)
	def __init__(self):
		self.listeners = set()
		self.treemode = False
		self.columns = []
		self.children = []
		self.items_by_id = {}
	def registerItem(self, item):
		self.items_by_id[id(item)] = item
	def itemSelected_by_id(self, id):
		self.items_by_id[id].selected()
	def setTreeMode(self):
		self.treemode = True
		self.notifyModification()
	def setColumns(self, colnames):
		self.columns = colnames
	def clear(self):
		self.columns = []
		self.children = []
	def notifyModification(self):
		for l in self.listeners:
			l.listViewModified()
	def appendChild(self, child):
		childlistener = self.__class__.ListViewItemListener(self, child)
		child.addListener(childlistener)
		self.registerItem(child)
		self.children.append(child)
	def getColumnCount(self):
		return len(self.columns)
	def getListView(self):
		return self
