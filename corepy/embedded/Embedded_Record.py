import os
from RecordDef import RecordDef
from FieldDef import FieldDef


class Embedded_Record(object):

    def __init__(self, recorddef=None):
        object.__init__(self)
        if not recorddef:
            self.__recorddef__  = RecordDef.get(self.__class__.__name__)
        else:
            self.__recorddef__  = recorddef
        self.__fields__ = {}
        self.__oldfields__ = {}
        self.__details__ = {}
        self._new = True
        self._modified = True
        self._master_record = None
        self.__listeners = []
        from Field import Field
        from Embedded_Field import Embedded_DetailField
        for fdef in self.__recorddef__.fieldDefs:
            self.__fields__[fdef.name] = Field(self, fdef)
            self.__oldfields__[fdef.name] = Field(self, fdef)
        for ddef in self.__recorddef__.detailDefs:
            f = Embedded_DetailField(self, ddef)
            self.__details__[ddef.name] = f

    #WON'T FIX: PYLINT'S CONFLICT
    #def __getattribute__(self, name):
    #    try:
    #        try:
    #            return object.__getattribute__(self, "__fields__")[name].getValue()
    #        except KeyError, e:
    #            try:
    #                return object.__getattribute__(self, "__details__")[name].getValue()
    #            except KeyError, e:
    #                raise AttributeError
    #    except AttributeError, e:
    #        return object.__getattribute__(self, name)

    def __setattr__(self, name, v):
        if self.hasField(name):
            return self.fields(name).setValue(v)
        else:
            return object.__setattr__(self, name, v)

    def name(self):
        if self.__recorddef__.name is None: return "Record"
        return self.__recorddef__.name

    def createField(self, name, type, length, persistent, linkto):
        from Field import Field
        fdef = FieldDef(name, type, length, persistent, linkto)
        self.__fields__[name] = Field(self, fdef)
        self.__oldfields__[name] = Field(self, fdef)

    def hasField(self, fn):
        if hasattr(self, "__fields__"): return self.__fields__.has_key(fn)
        if not hasattr(self, "__recorddef__"): return False
        return self.__recorddef__.fieldDefsDict.has_key(fn)

    def isLocal(self):
        return self.__recorddef__.is_local

    def isPersistent(self):
        return self.__recorddef__.is_persistent

    def load(self):
        if self.isLocal():
            f = open(os.path.join("local", self.name() + ".data"), "rb")
            f.readline() #nombre del registro
            fnames = f.readline().replace("\n","").split("\t")
            r = self.__class__()
            for row in f.readlines():
                values = row.replace("\n","").split("\t")
                for fn, value in zip(fnames, values):
                    setattr(r, fn, value)
                filter_fnames = filter(lambda fn: not self.fields(fn).isNone(), self.fieldNames())
                if not filter_fnames or filter(lambda fn: not r.fields(fn).isNone() and r.fields(fn).getValue() == self.fields(fn).getValue(), filter_fnames):
                    for fn in self.fieldNames():
                        setattr(self, fn, getattr(r, fn))
                    return True
            return False
        return False

    def calculateDetailNames(self):
        return [f.name for f in self.__recorddef__.detailDefs]

    def calculateFieldNames(self):
        if len(self.__recorddef__.fieldDefs) != len(self.__fields__):
            return [f for f in self.__fields__.keys()]
        else:
            return [f.name for f in self.__recorddef__.fieldDefs]

    def fieldNames(self):
        return self.calculateFieldNames()

    def detailNames(self):
        if self.name() and self.name() != "Record" and self.__class__.__module__ != "functions":
            #~ if self.__class__.__detailnames is None:
            #~ devuelve lista vacia a veces, no se por que. mejorar! (AT)
            if not hasattr(self.__class__, '__detailnames') or not self.__class__.__detailnames:
                self.__class__.__detailnames = self.calculateDetailNames()
            return self.__class__.__detailnames
        else:
            return self.calculateDetailNames()

    def fields(self, fn):
        try:
            return self.__fields__[fn]
        except KeyError, e:
            return None

    def oldFields(self, fn):
        try:
            return self.__oldfields__[fn]
        except KeyError, e:
            return None

    def details(self, dn):
        try:
            return self.__details__[dn]
        except KeyError, e:
            return None


    def setNew(self, v):
        self._new = v

    def setModified(self, v):
        if not self.isPersistent(): return
        self._modified = v

    def isModified(self):
        if not self.isPersistent(): return False
        return self._modified

    def isNew(self):
        return self._new

    def isDetail(self):
        return self.__recorddef__.isDetail()

    def afterLoad(self):
        pass

    def setLoadedType(self, ltype):
        self.loadded_type = ltype

    def getFieldDisplayValue(self, fn):
        return fn

    def tableName(self):
        return self.__recorddef__.name

    def setFocusOnField(self, fn, rfn=None, rownr=None):
        for l in self.__listeners:
            l.setFocusOnField(fn, rfn, rownr)

    def getMasterRecord(self):
        return self._master_record

    def afterDelete(self):
        return True

    def afterCopy(self):
        pass
    def refresh(self):
        pass

    def getAttachAsString(self, attachid):
        from globalfunctions import NewRecord
        a = NewRecord("Attach")
        a.internalId = attachid
        if a.load():
            return a.Value

    def addListener(self, l):
        self.__listeners.append(l)

    def removeListener(self, l):
        self.__listeners.remove(l)

    def fieldModified(self, fn, value):
        self._modified = True
        if self._master_record: self._master_record._modified = True
        for l in self.__listeners:
            l.fieldModified(fn, value)

    def getFieldLabel(self, fname, fvalue=None, rowfname=None, rowfvalue=None):
        from globalfunctions import getWindowsInfo
        gwi = getWindowsInfo()
        res = ""
        for win in gwi.keys():
            if (self.name() == gwi[win]["RecordName"]):
                exec("from %s import %s" %(win,win))
                exec("rwin = %s()" %(win))
                res = rwin.getFieldLabel(fname,fvalue,rowfname,rowfvalue)
        return res

    class Listener(object):
        def fieldModified(self, fn, value):
            pass
