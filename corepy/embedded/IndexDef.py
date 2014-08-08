
class IndexDef(object):
    
    def __init__(self, name=None, fieldnames=[], unique=False, primary=False):
        self.name = name
        self.fieldnames = []
        self.unique = unique
        self.primary = primary
        
    def parse(self, parent, attributes):
        parent.indexDefs.append(self)
        self.name = attributes["name"]
        self.unique = (attributes.get("unique", "false").lower() == "true")
        self.primary = (attributes.get("primary", "false").lower() == "true")
    
class IndexFieldDef(object):
    
    def __init__(self, fieldname=None, keylength=0):
        self.fieldname = fieldname
        self.keylength = keylength
        
    def parse(self, parent, attributes):
        self.fieldname = attributes["fieldname"]
        self.keylength = int(attributes.get("keylength", 0))
        parent.fieldnames.append(self)
