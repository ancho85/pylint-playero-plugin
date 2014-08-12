import os

from globalfunctions import *
from Embedded_Record import * #Embedded_Record
from Embedded_Field import * #Embedded_Field
from Embedded_Window import * #Embedded_Window
from Embedded_Thread import * #Embedded_Thread
from Embedded_Document import * #Embedded_Document
from Embedded_ListView import * #Embedded_ListView
from Embedded_ListViewItem import *# Embedded_ListViewItem
from Embedded_Report import * #Embedded_Report
from Embedded_ScrollArea import * #ScrollArea
from Embedded_ButtonObj import *
from Embedded_Routine import *
from CThread import * #CThread


#root_path = os.path.join(os.getcwd(), "..")
root_path = os.getcwd()
print getScriptDirs()
modulesindex = getClassesIndex(getScriptDirs())
modulesindex["Record"] = ["core.Record"]
modulesindex["Window"] = ["core.Window"]
#print modulesindex["ActivityWindow"]

def SuperClass(classname, superclassname, filename):
    if classname == "Record":
        from Record import Record
        return Record
    #print "asking for superclass for", classname, superclassname,
    if not filename:
        m = __import__(modulesindex[classname][0], globals(), locals(), [classname])
        return getattr(m, classname)
    else:
        filename = os.path.normpath(filename)
        sd, modname = os.path.split(os.path.dirname(filename.replace("\\","/").replace("./","")))
        found = False
        #print "MI: ", modulesindex[classname]
        if classname in modulesindex:
            for mod in modulesindex[classname]:
                #print mod, mod.split(".")[:-2], sd.split("/")
                if found:
                    #print "returning", mod
                    m = __import__(mod, globals(), locals(), [classname])
                    return getattr(m, classname)
                if mod.split(".")[:-2] == sd.split("/"):
                    #print "FOUND"
                    found = True
        #print "OUT"
        return SuperClass(superclassname, "Record", None)
    return None
    #clsstruct = modulesindex[classname]
    #from

