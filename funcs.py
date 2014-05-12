from cache import cache
__playeroPath__ = "e:/Develop/desarrollo/python/ancho/workspace/Playero/"

@cache.store
def getScriptDirs(level=255):

    def unicodeToStr(value):
        res = ""
        try:
            res = str(value)
        except:
            res = repr(value)
        return res
    from xml.sax import handler
    from xml.sax import make_parser
    from xml.sax.handler import feature_namespaces

    class XMLSettingsHandler(handler.ContentHandler):

        def __init__(self):
            self.scriptdirs = []
            self.sd = []
            for i in range(255):
                self.sd.append(None)

        def startElement(self, name, attrs):
            if name == "scriptdir":
                self.sd[int(attrs.get('level', 0))] = unicodeToStr(attrs.get('path', None))

        def endDocument(self):
            for i in self.sd:
                if i:
                    self.scriptdirs.append(i)

    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    dh = XMLSettingsHandler()
    parser.setContentHandler(dh)
    parser.parse(open(__playeroPath__+"settings/settings.xml", "r"))
    res = dh.scriptdirs[:level+1]
    res.reverse()
    dirpaths = []
    for scriptdir in res:
        for pydir in ['records', 'windows', 'reports', 'routines', 'documents', 'tools']:
            dirpaths.append(scriptdir+"/"+pydir)
    dirpaths.append("core")
    dirpaths.append("/python/python24/Lib/site-packages/windows")
    return dirpaths

@cache.store
def getRecordsInfo():
    import os
    fields = {}
    for sd in getScriptDirs(255):
        d = os.path.join(sd, "interface")
        if not os.path.exists(d):
            continue
        for d in os.listdir(d):
            if d.lower().endswith(".record.xml"):
                recordname = d.split('.')[0]
                fields[recordname] = {
                    "internalId": "integer",
                    "attachFlag": "boolean",
                    "syncVersion": "integer"
                }
    return fields

def getFullPaths():
    paths = []
    res = getScriptDirs(255)
    for x in res:
        newpath = __playeroPath__+x
        paths.append(newpath)
    return paths
