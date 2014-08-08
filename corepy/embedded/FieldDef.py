
class FieldDef(object):
    
    def __init__(self, name=None, type=None, length=None,persistent=True, linkto="", mastername=None):
        self.name = name
        self.type = type
        self.length = length
        self.linkto =  linkto
        self.persistent = persistent
        self.recordname = ""
        self.mastername = mastername

    def __str__(self):
        return "Field %s: %s" % (self.name, self.type)
        
    def parse(self, parent, attributes):
        self.name = attributes["name"]
        self.type = attributes["type"].lower()
        self.linkto = attributes.get("linkto", "")
        self.length = int(attributes.get("length", 0))
        self.recordname = attributes.get("recordname", 0)
        self.persistent = (attributes.get("persistent", "true").lower() == "true")
        self.nullable = (attributes.get("nullable", "true").lower() == "true")
        if self.type == "detail":
            self.mastername = parent.name
            parent.detailDefsDict[self.name] = self
            parent.detailDefs.append(self)
        else:
            parent.fieldDefsDict[self.name] = self
            parent.fieldDefs.append(self)
