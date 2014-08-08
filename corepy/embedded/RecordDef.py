from FieldDef import FieldDef

class RecordDef(object):
    base_class = "Record"
    instances = {}
    InternalIdDef = FieldDef()
    InternalIdDef.name = "internalId"
    InternalIdDef.type = "internalid"
    
    def __init__(self):
        self.fieldDefsDict = {}
        self.fieldDefs = []
        self.detailDefsDict = {}
        self.detailDefs = []
        self.indexDefs = []
        self.composed = False
        self.pos = None
        self.recordclass = None

    def __str__(self):
        return "RecordDef %s\n" % self.name + '\n'.join([str(f) for f in self.fieldDefs])
        
    def release(self):
        try:
            if id(RecordDef.instances[self.name]) == id(self):
                del RecordDef.instances[self.name]
        except:
            pass
            
    def isDetail(self):
        return False
        
    def parse(self, parent, attributes):
        self.name = attributes.get("name")
        self.tablename = attributes.get("tablename", "")
        if self.name in ("Record", "DetailRecord"):
            self.inherits = attributes.get("inherits", "Embedded_Record")
        else:
            self.inherits = attributes.get("inherits", self.__class__.base_class)
        self.is_local = attributes.get("local", "false").lower()=="true"
        self.is_setting = attributes.get("setting", "false").lower() == "true"
        self.is_persistent = attributes.get("persistent", "true").lower() == "true"
        try:
            self.pos = len(RecordDef.instances[self.name])
            if self.pos > 0:
                RecordDef.instances[self.name][self.pos-1].inherits = self.name
            RecordDef.instances[self.name].append(self)
        except KeyError, e:
            self.pos = 0
            RecordDef.instances[self.name] = [self]

    @classmethod
    def composeAll(objclass):
        for name, rdefs in RecordDef.instances.items():
            for rdef in rdefs:
                if not rdef.composed: 
                    rdef.compose()
                        
            
    def getParentDef(self):
        if self.inherits == self.name:
            return self.__class__.get(self.name, self.pos+1)
        else:
            try:
                return self.__class__.get(self.inherits, 0)
            except KeyError, e:
                return None
            
            
    def compose(self):
        #print self.__cl
        if self.composed: return
        try:
            parentdef = self.getParentDef()
        except:
            raise Exception("Could not load parent record definition. Record: %s. Missing parent: %s."%(self.name, self.inherits))
        if not parentdef: return
        if not parentdef.composed: 
            parentdef.compose()
        for pfdef in reversed(parentdef.fieldDefs):
            if not self.fieldDefsDict.has_key(pfdef.name):
                self.fieldDefs = [pfdef] + self.fieldDefs
                self.fieldDefsDict[pfdef.name] = pfdef
        for pfdef in reversed(parentdef.detailDefs):
            if not self.detailDefsDict.has_key(pfdef.name):
                self.detailDefs = [pfdef] + self.detailDefs
                self.detailDefsDict[pfdef.name] = pfdef

    @classmethod
    def get(self, name, pos=0):
        return RecordDef.instances[name][pos]
        
    def calculateDetailNames(self):
        return []

    def calculateFieldNames(self):
        return ["internalId"]

    def getRecordClass(self, ):
        if not self.recordclass:
            exec("from %s import %s as CLS" % (self.name, self.name))
            self.recordclass = CLS
        return self.recordclass

class DetailRecordDef(RecordDef):
    base_class = "DetailRecord"
    
    def isDetail(self):
        return True
