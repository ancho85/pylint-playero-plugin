WEBCLIENT = True

import sys
import os
import threading
from ClientServerTools import getClientConnection


_settingsfile = {"path": None}

def getSettingsFileName():
    return _settingsfile["path"]

def setSettingsFileName(path):
    _settingsfile["path"] = path

def getScriptDirs(levels=999):
    from xml.sax import make_parser, handler
    class ScriptDirsHandler(handler.ContentHandler):
        def __init__(self):
            self.scriptdirs = []
        def startElement(self, name, attrs):
            if name == "scriptdir":
                self.scriptdirs.append(attrs["path"])
    parser = make_parser()
    parser.setFeature(handler.feature_namespaces, 0)
    xmlhandler = ScriptDirsHandler()
    parser.setContentHandler(xmlhandler)
    parser.parse(open(getSettingsFileName(), "rb"))
    return list(reversed(xmlhandler.scriptdirs))

def logstring(s):
    #from core.functions import currentUser
    rawmsg = "%s %s\n" % (currentUser().encode("utf8"), s)
    open("OpenOrange.log","ab").write(rawmsg)

def decode(value):
    return ''.join([chr(ord(value[len(value)-1-i])+11) for c,i in zip(value, range(len(value)))])

def genPassword(value):
    tam = len(value)
    res = ""
    for i in range(tam):
        res += chr(ord(value[tam-1-i])-11)
    return res;

def getQueryLogging():
    return True

def sysprint(s):
    sys.stdout.write("%s\n" % s)
    sys.stdout.flush()

def hasConsole():
    return True

def NewRecord(rname):
    themod = __import__(rname)
    return themod()
    #res = None
    #try:
    #    exec("from %s import %s as CLS" % (rname, rname))
    #    res = CLS()
    #except Exception, e:
    #    import traceback
    #    traceback.print_exc()
    #return res

def NewWindow(wname):
    exec("from %s import %s as CLS" % (wname, wname))
    return CLS()

current_company = [""] # awful

def currentCompany():
    return current_company[0]

def setCurrentCompany(comp_code):
    current_company[0] = comp_code

def login(user=None, password=None):
    if user is None: return False
    return True

def getCommandLineParams():
    return {}

def getLanguage():
    from xml.sax import make_parser, handler
    class LanguageHandler(handler.ContentHandler):
        def __init__(self):
            self.lang = ""
            self._current_element = None
        def startElement(self, name, attrs):
            self._current_element = name
        def endElement(self, name):
            self._current_element = None
        def characters(self, data):
            if self._current_element == "language":
                self.lang += data
    parser = make_parser()
    parser.setFeature(handler.feature_namespaces, 0)
    xmlhandler = LanguageHandler()
    parser.setContentHandler(xmlhandler)
    parser.parse(open(getSettingsFileName(), "rb"))
    return xmlhandler.lang

def runningInBackground():
    return False

def curUser():
    return ""

def getRecordsInfo():
    from RecordDef import RecordDef
    minfo = {}
    for record_name in RecordDef.instances:
        rdef = RecordDef.get(record_name)
        fields = {}
        for fieldname in rdef.fieldDefsDict:
            linkto = rdef.fieldDefsDict[fieldname].linkto
            length = rdef.fieldDefsDict[fieldname].length
            fields[fieldname] = {
                "LinkTo": linkto,
                "Nullable": rdef.fieldDefsDict[fieldname].nullable,
                "RecordName": rdef.fieldDefsDict[fieldname].recordname,
                "MasterName": rdef.fieldDefsDict[fieldname].mastername,
                "Persistent": rdef.fieldDefsDict[fieldname].persistent,
                "Length": length,
                "Collation": "utf8_general_ci",
                "Type": rdef.fieldDefsDict[fieldname].type
            }
            if linkto and not length:
                r = NewRecord(linkto)
                if not r:
                    raise Exception("LinkTo not found. Record: %s. Linkto: %s. Fieldname: %s."%(record_name, linkto, fieldname))
                uk = r.uniqueKey()
                if len(uk) == 1:
                    try:
                        fields[fieldname]["Length"] = r.fields(uk[0]).getMaxLength()
                    except:
                        raise Exception("UniqueKey not found. Record: %s. Linkto: %s. Fieldname: %s."%(record_name, linkto, uk[0]))
        details = {}
        for detailname in rdef.detailDefsDict:
            details[detailname] = {
                "LinkTo": rdef.detailDefsDict[detailname].linkto,
                "Nullable": rdef.detailDefsDict[detailname].nullable,
                "RecordName": rdef.detailDefsDict[detailname].recordname,
                "MasterName": rdef.detailDefsDict[detailname].mastername,
                "Persistent": rdef.detailDefsDict[detailname].persistent,
                "Length": rdef.detailDefsDict[detailname].length,
                "Collation": "utf8_general_ci",
                "Type": rdef.detailDefsDict[detailname].type
            }
        indexes = {}
        for index in rdef.indexDefs:
            indexes[index.name] = {
                "Name": index.name,
                "Unique": index.unique,
                "Primary": index.primary,
                "FieldNames": [[f.fieldname, f.keylength] for f in index.fieldnames]
            }
        mdicc = {
            "Name": record_name,
            "Fields": fields,
            "TableName": rdef.tablename,
            "Persistent": rdef.is_persistent,
            "Indexes": indexes,
            "Details": details
        }
        minfo[record_name] = mdicc
    return minfo

def truncateLogFile():
    open("OpenOrange.log","w").close()

def getOpenWindowsList():
    return []

def getWindowsInfo():
    minfo = {}
    from functions import tr
    for sd in getScriptDirs():
        d = os.path.join(sd, "interface")
        if not os.path.exists(d): continue
        for d in os.listdir(d):
            if d.lower().endswith(".window.xml"):
                recordname = d.split('.')[0]
                windowname = recordname + "Window"
                minfo[windowname] = {
                    "RecordName": recordname,
                    "Title": recordname
                }
    return minfo

def getImagePath(img):
    for d in getScriptDirs():
        pathtest = os.path.join(d, "images", img)
        if os.path.exists(pathtest):
            return pathtest
    return os.path.join("images", img)

def graphicModeEnabled():
    return False #server

__messages_enabled__ = True
def disableMessages():
    __messages_enabled__ = False

def messagesEnabled():
    return __messages_enabled__

def displaymessage(msg, icon):
    cc = getClientConnection()
    #print "client connection: ", cc
    if cc:
        return cc.displaymessage(msg, icon)
    else:
        try:
            print "message: " + msg
        except Exception, e:
            pass

def askYesNo(msg):
    cc = getClientConnection()
    if cc:
        return cc.askYesNo(msg)
    else:
        try:
            print "askYesNo: " + msg
        except Exception, e:
            pass
    return False

def getSelection(msg, options, default=0):
    cc = getClientConnection()
    if cc:
        return cc.getSelection(msg, options, default)
    else:
        try:
            print "getSelection: " + msg
        except Exception, e:
            pass
    return ""

def getString(msg, default=""):
    cc = getClientConnection()
    if cc:
        return cc.getString(msg, default)
    else:
        try:
            print "getString: " + msg
        except Exception, e:
            pass
    return None

def postMessage(msg, *args):
    cc = getClientConnection()
    if cc:
        return cc.postMessage(msg)
    else:
        try:
            print "postMessage: " + msg
        except Exception, e:
            pass

def heartbeat():
    cc = getClientConnection()
    if cc:
        return cc.heartbeat()
    else:
        try:
            print "heartbeat"
        except Exception, e:
            pass

def notifyMessages(*args):
    cc = getClientConnection()
    if cc:
        return cc.notifyMessages(*args)
    else:
        try:
            print "notifyMessages: " + str(args)
        except Exception, e:
            pass

def getWebDir():
    from xml.sax import make_parser, handler
    class ScriptDirsHandler(handler.ContentHandler):
        def __init__(self):
            self.element=None
            self.webdir = ""
        def startElement(self, name, attrs):
            self.element = name.lower()
        def endElement(self, name):
            self.element = None
        def characters(self, data):
            if self.element == "webdir":
                self.webdir += data
    parser = make_parser()
    parser.setFeature(handler.feature_namespaces, 0)
    xmlhandler = ScriptDirsHandler()
    parser.setContentHandler(xmlhandler)
    parser.parse(open(getSettingsFileName(), "rb"))
    return xmlhandler.webdir


def beep():
    pass

def getModulesInfo():
    from xml.sax import make_parser, handler
    class ModuleHandler(handler.ContentHandler):
        def __init__(self):
            self.name = ""
            self.label = ""
            self.entries = {"Records":[], "Reports":[], "Routines":[], "Settings":[]}
        def startElement(self, name, attrs):
            if name == "module":
                self.name = attrs["name"]
                self.label = attrs["label"]
            if name == "recordentry":
                self.entries["Records"].append({"Image": attrs.get("image",""), "Name": attrs.get("name",""), "Label": tr(attrs.get("label",""))})
            if name == "reportentry":
                self.entries["Reports"].append({"Image": attrs.get("image",""), "Name": attrs.get("name",""), "Label": tr(attrs.get("label",""))})
            if name == "routineentry":
                self.entries["Routines"].append({"Image": attrs.get("image",""), "Name": attrs.get("name",""), "Label": tr(attrs.get("label",""))})
            if name == "settingentry":
                self.entries["Settings"].append({"Image": attrs.get("image",""), "Name": attrs.get("name",""), "Label": tr(attrs.get("label",""))})
        def endElement(self, name):
            pass
        def characters(self, data):
            pass
    minfo = {}
    from functions import tr
    for sd in getScriptDirs():
        d = os.path.join(sd, "interface")
        if not os.path.exists(d): continue
        for d in os.listdir(d):
            if d.lower().endswith(".module.xml"):
                parser = make_parser()
                parser.setFeature(handler.feature_namespaces, 0)
                xmlhandler = ModuleHandler()
                parser.setContentHandler(xmlhandler)
                parser.parse(open(os.path.join(sd,"interface", d), "rb"))
                if xmlhandler.name in minfo.keys():
                    minfo[xmlhandler.name]["Label"] =  tr(xmlhandler.label)
                    for r in xmlhandler.entries["Records"]:
                        if r["Name"] not in [x["Name"] for x in minfo[xmlhandler.name]["Records"]]: minfo[xmlhandler.name]["Records"].append(r)
                    for r in xmlhandler.entries["Reports"]:
                        if r["Name"] not in [x["Name"] for x in minfo[xmlhandler.name]["Reports"]]: minfo[xmlhandler.name]["Reports"].append(r)
                    for r in xmlhandler.entries["Routines"]:
                        if r["Name"] not in [x["Name"] for x in minfo[xmlhandler.name]["Routines"]]: minfo[xmlhandler.name]["Routines"].append(r)
                    for r in xmlhandler.entries["Settings"]:
                        if r["Name"] not in [x["Name"] for x in minfo[xmlhandler.name]["Settings"]]: minfo[xmlhandler.name]["Settings"].append(r)
                else:
                    minfo[xmlhandler.name] = {"Code": xmlhandler.name, "Label": tr(xmlhandler.label), "Records": xmlhandler.entries["Records"], "Reports": xmlhandler.entries["Reports"], "Routines": xmlhandler.entries["Routines"], "Settings": xmlhandler.entries["Settings"]}
    return minfo

def setToggleFollowStatus(b):
    pass

def setButtonActionVisibility(*args, **kwargs):
    pass

#print [x for x in getModulesInfo()["CRM"]["Records"] if x["Name"] == "ActivityListWindow"]
#print [x for x in getModulesInfo()["CRM"]["Reports"] if x["Name"] == "SubscriptionControl"]

def getOpenFileName(msg=""):
    cc = getClientConnection()
    #print "client connection: ", cc
    if cc:
        return cc.getOpenFileName(msg)

def embedded_saveFile(*args, **kwargs):
    cc = getClientConnection()
    #print "client connection: ", cc
    if cc:
        return cc.saveFile(*args, **kwargs)

def rawAction(*args, **kwargs):
    cc = getClientConnection()
    #print "client connection: ", cc
    if cc:
        return cc.rawAction(*args, **kwargs)

def embedded_getSaveFileName(msg, defaultfilename=None, filterstr=None):
    from functions import alert
    alert("Function not supported. Please use 'saveFile' function.")

def getApplicationType():
    return 1

def _webclientSendId(id):
    # should not be global
    cc = getClientConnection()
    #print "client connection: ", cc
    if cc:
        return cc._webclientSendId(id)

def findWindow(id):
    return threading.currentThread().session.getWindow(id)

def enableSwitchCompanyButton():
    pass

def getTimezone():
    from SettingsFile import SettingsFile
    return SettingsFile.getInstance().getTimezone()

def createRecordModuleAndClass(name, baseclassname):
    import new
    from Record import Record
    classobject = new.classobj(name, (Record, ), {})
    mod = new.module(name)
    mod.__dict__[name] = classobject
    sys.modules[name] = mod

import sys
import os
import os.path
import re

def getClassesIndex(scriptdirs):
    try:
        pidfile = open("openorange.pid","w")
        pidfile.write("%s" % os.getpid())
        pidfile.flush()
    except Exception, e:
        print e

    prefix = "" #"../"
    regexp = re.compile("class ([^\(:]*)[\(:]")
    res = {}
    for scriptdir in scriptdirs:
        px = os.path.split(scriptdir)[0]
        if (px != ""):
            px = os.path.normpath(px)
            px.replace("//","/")
            px.replace("\\\\","\\")
            px.replace("/",".")
            px.replace("\\",".")
            px += "."
        filesmap = {}
        for pydir in ['records','windows','reports','routines','documents', 'updates', 'webcontrollers', 'tools']:
            try:
                files = os.listdir(prefix + scriptdir + "/" + pydir)
            except OSError:
                continue
            for fn in files:
                if fn[-3:] == ".py":
                    filesmap[os.path.join(pydir, fn)] = os.path.getmtime(os.path.join(scriptdir, pydir, fn))
                    mod_name = fn[:-3]
                    mod_path =  scriptdir + "." + pydir + "." +mod_name
                    f = file(prefix + scriptdir + "/" + pydir + "/" + fn,"r")
                    classlines = filter(lambda x: x[0:5] == "class",f.readlines())
                    for classline in classlines:
                        classname = regexp.search(classline).group(1);
                        if not res.has_key(classname): res[classname] = []
                        mod_path =  mod_path[mod_path.rfind('/')+1:]
                        res[classname].append(px + mod_path)
        #cPickle.dump(filesmap, open(os.path.join(scriptdir, "mod.idx"), "wb"))
    #cPickle.dump(res, open("./tmp/mod.obj","wb"))
    res["RoutineWindow"] = ["core.RoutineWindow"]
    res["ReportWindow"] = ["core.ReportWindow"]
    res["Report"] = ["Report"]
    import functions
    functions.modules_index = res
    return res

def commit():
    #Database.getCurrentDB().commit()
    return True

def rollback():
    #Database.getCurrentDB().rollback()
    return True

def exitProgram():
    sys.exit(0)

def processEvents():
    pass


def currentCompanyHost():
    return ""

def currentWindow():
    from Embedded_Window import Embedded_Window
    return Embedded_Window()

def utf8(value):
    if isinstance(value, unicode):
        return value.encode("utf8")
    elif isinstance(value, str):
        return unicode(value, 'utf8', errors='replace')
        #elif isinstance(value, DBError):
        #   return utf8(value.__str__())
    else:
        try:
            return unicode(value, 'utf8', errors='replace')
        except:
            try:
                s = str(value)
            except:
                s = repr(value)
            return unicode(s, 'utf8', errors='replace')

def tr(*args):        # old definition was tr(msg, default=-1):
    eles = []
    for ele in args:
        if isinstance(ele, unicode):
            sele = ele
        else:
            if hasattr(ele, "__str__"):
                sele = ele.__str__() #__str__ funciona mejor cuando el objeto es un errorresponse
            else:
                sele = str(ele)
        a =  {True: langdict().get(ele,langdict("en").get(ele,ele)), False: sele}[bool(langdict().get(ele,langdict("en").get(ele,ele)))]
        eles.append("%s" %(a))
    if (eles):
        res = " ".join(eles)
    else:
        res = ""
    if isinstance(res, unicode): return res
    return unicode(res, 'utf8', 'replace')

def createServerConnection(automatic_login=True):
    import socket
    from ProtocolInterface import ClientProtocolInterface
    try:
        conn = ClientProtocolInterface("127.0.0.1", 3306)
        if automatic_login:
            u = "user"
            p = "password"
            if conn.login(u, p):
                return conn
        else:
            return conn
    except socket.error, e:
        raise Exception("Error connecting to server %s" % e)

def getServerConnection(automatic_login=True):
    ApplicationType = 1
    if ApplicationType == 1:
        #if not hasattr(threading.currentThread(), "server_connection") or not threading.currentThread().server_connection:
        threading.currentThread().server_connection = None
        threading.currentThread().server_connection = createServerConnection(automatic_login)
        return threading.currentThread().server_connection
    return None
