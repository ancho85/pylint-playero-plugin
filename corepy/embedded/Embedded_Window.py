from Embedded_Record import Embedded_Record
from Embedded_ListView import Embedded_ListView
from globalfunctions import rawAction

class RecordListener(Embedded_Record.Listener):
    def __init__(self, window):
        self.__window = window
    def fieldModified(self, fn, value):
        if not hasattr(self.__window, "windowid"):
            return
        from globalfunctions import rawAction
        #~ print self.__window
        rawAction("Window", self.__window.windowid, "fieldModified", fn, value=(value,))
    def setFocusOnField(self, fn, rfn, rownr):
        rawAction("Window", self.__window.windowid, "setFocusOnField", value=(fn, rfn, rownr))

class Embedded_Window(object):
    class ListViewListener(Embedded_ListView.Listener):
        def __init__(self, window, name, listview):
            self.__window = window
            self.__name = name
            self.__listview = listview
        def listViewModified(self):
            if not hasattr(self.__window, "windowid"):
                return
            from globalfunctions import rawAction
            rawAction("Window", self.__window.windowid, "listViewModified", self.__name, value=(self.__listview,))

    def __init__(self):
        self.windowid = id(self)
        self.followStatus = False
        self.ListWindowSortFields = ()
        self.ListWindowFilter = ""
        self._FieldOptions = {}
        self.__recordListener = RecordListener(self)
        self.__listviews = {}
        self.__scrollareaviews = {}
    def setFieldOptions(self, fieldname, options):
        self._FieldOptions[fieldname] = options
    def getFieldOptions(self, fieldname):
        return self._FieldOptions.get(fieldname, ())
    def beforeInsertRow(self, detailfieldname, rownr):
        return True
    def beforeDeleteRow(self, detailfieldname, rownr):
        return True

    def open(self):
        return True

    def setTabPageVisibility(self, tabname, pagename, doshow):
        return rawAction("Window", self.windowid, "setTabPageVisibility", tabname, pagename, doshow, doReturn=False)

    def setFocus(self, *args, **kwargs):
        pass
    #~ def getRecord(self):
        #~ #used in webmode
        #~ return self.__record__
    def getTitle(self):
        from functions import *
        rec = self.getRecord()
        if not rec:
            return self.getOriginalTitle()
        else:
            #~ t = "%s %s"%(self.getOriginalTitle(), getattr(rec, rec.uniqueKey()[0]))
            t = tr( self.getOriginalTitle() )
            uniqueKeys = rec.uniqueKey()
            if uniqueKeys:
                t += " %s" % getattr(rec, rec.uniqueKey()[0])
        #from Company import Company
        #lcom = Company.getLoguedCompanies()
        #if (len(lcom) > 1):
        #    t = "[%s] %s" %(Company.getCurrent().Code,t)
        if rec.isPersistent() and not rec.internalId:
            t += ": " + tr("New")
        elif rec.isModified():
            t += ": " + tr("Modified")
        return t
    #~ def getOriginalTitle(self):
        #~ return ""
    def getReportView(self, name):
        import threading
        windowId = threading.currentThread().session.addWindow(self)
        return {
            'windowId': windowId,
            'name': name
        }
    def getImageView(self, name):
        class ImageView:
            def __init__(self, windowId, name):
                self.windowId = windowId
                self.name = name
                self.data = ''
            def setImage(self, data):
                self.data = data
                from ClientServerTools import getClientConnection
                cc = getClientConnection()
                if cc:
                    cc.setImage(self)
            def clearImage(self):
                self.data = ''
            def getImage(self):
                return self.data
            def getName(self):
                return self.name
        import threading
        #~ windowId = self.windowid
        windowId = threading.currentThread().session.addWindow(self)
        return ImageView(windowId, name)
    def close(self):
        from globalfunctions import rawAction
        rawAction("Window", self.windowid, "close")
    def setToggleFollowStatus(self, v):
        self.followStatus = v
    def getListWindowSortFields(self):
        return self.ListWindowSortFields
    def setListWindowSortFields(self, v):
        self.ListWindowSortFields = v
    def getListWindowFilter(self):
        return self.ListWindowFilter
    #~ def setListWindowFilter(self, v):
        #~ self.ListWindowFilter = v
    def setListWindowFilterSafe(self, fieldlist, value):
        v = ""

        if value and fieldlist:
            v = "("
            fconditions = []
            for f in fieldlist:
                fconditions.append( "{%s} LIKE s|%%%s%%|"%(f, value) )
            v += " OR ".join(fconditions)
            v += ") WHERE?AND ({Closed} is NULL or {Closed}=i|0|)"

        # access group filter
        from User import User
        from functions import currentUser
        u = User.bring(currentUser())
        record = self.getRecord()
        if u.AccessGroup and record:
            from AccessGroup import AccessGroup
            ag = AccessGroup.bring(u.AccessGroup)
            recordname = record.__class__.__name__
            record_filter = {
                0: None,
                1: ("Office", "Office"),
                2: ("Code", "User"),
                3: ("Department", "Department"),
                4: ("Code", "Asignee")
            }[ag.getRecordVisibility(recordname)]
            record_filter_clause = ""
            if record_filter:
                record_filter_data = getattr(u, record_filter[0])
                record_filter_clause = " WHERE?AND {%s}=s|%s|" % (record_filter[1], record_filter_data)
            v += record_filter_clause

        self.ListWindowFilter = v
    def setMatrixRowBGColor(self, name, rownr, color):
        pass
    def refresh(self):
        record = self.getRecord()
        if record:
            from globalfunctions import rawAction
            for fn in record.fieldNames():
                rawAction("Window", self.windowid, "fieldModified", fn, record.fields(fn).getValue())
            for dn in record.detailNames():
                rawAction("Window", self.windowid, "fieldModified", dn, record.details(dn).getValue())
    def reloadRecord(self):
        record = self.getRecord()
        from globalfunctions import NewRecord
        new_record = NewRecord(record.name())
        if hasattr(new_record, "internalId"):
            new_record.internalId = record.internalId
            if new_record.load():
                self.setRecord(new_record)
    def setFieldDecimals(self, *args, **kwargs):
        pass
    def name(self):
        return self.__class__.__name__
    def getOriginalTitle(self):
        #try:
        #    from ParserNew import WindowParser
        #    w = WindowParser.get_instance(self.name()[:-6])
        #    return w.title
        #except:
        if True:
            if self.__record__:
                from functions import tr
                return tr(self.__record__.__class__.__name__)
            else:
                return ""
    def setRecord(self, record):
        rewrite = False
        if hasattr(self, "__record__") and self.__record__:
            self.__record__.removeListener(self.__recordListener)
            rewrite = True
        self.__record__ = record
        self.__record__.addListener(self.__recordListener)
        if rewrite:
            self.refresh()
            #~ for fn in self.__record__.fieldNames():
                #~ self.__recordListener.fieldModified(fn, self.__record__.fields(fn).getValue())
            #~ for fn in self.__record__.detailNames():
                #~ self.__recordListener.fieldModified(fn, self.__record__.details(fn).getValue())

    def getRecord(self):
        return self.__record__
    def setRowFieldDecimals(self, *args, **kwargs):
        pass
    def getId(self):
        return self.windowid
    def getListView(self,name):
        if not name in self.__listviews:
            from ListView import ListView
            lv = ListView()
            lv.addListener(self.__class__.ListViewListener(self, name, lv))
            self.__listviews[name] = lv
        return self.__listviews[name]
    def getFieldLabel(self, fname, fvalue=None, rowfname=None, rowfvalue=None):
        from globalfunctions import getWindowsInfo, utf8, tr
        gwi = getWindowsInfo()
        #print fname, fvalue, rowfname, rowfvalue
        res = ""
        if (fvalue != None):  fvalue = utf8(fvalue)
        if (rowfvalue != None): rowfvalue = utf8(rowfvalue)
        if (not "FieldsData" in gwi.keys()):
            return res
        if (fname):
            obj = gwi["FieldsData"].get(fname,"")
            if (obj):
                res = gwi["FieldsData"][fname]["Label"]
            else:
                return tr(res)
        else:
            return tr(res)
        if (fvalue):
            obj = gwi["FieldsData"][fname].get("OptionValues","")
            if (obj):
                res = "%s?" %(tr(res))
                #alert((fvalue,gwi["FieldsData"][fname]["OptionValues"]))
                if (fvalue in gwi["FieldsData"][fname]["OptionValues"]):
                    idx = gwi["FieldsData"][fname]["OptionValues"].index(fvalue)
                    res = gwi["FieldsData"][fname]["OptionLabels"][idx]
                else:
                    return tr(res)
            else:
                return tr(res)
        if (rowfname):
            obj = gwi["FieldsData"][fname].get("Columns","")
            if (obj):
                obj = gwi["FieldsData"][fname]["Columns"].get(rowfname,"")
                if (obj):
                    res = gwi["FieldsData"][fname]["Columns"][rowfname]["Label"]
                else:
                    return tr(res)
            else:
                return tr(res)
        if (rowfvalue):
            obj = gwi["FieldsData"][fname]["Columns"][rowfname].get("OptionValues","")
            if (obj):
                res = "%s?" %(tr(res))
                if (rowfvalue in gwi["FieldsData"][fname]["Columns"][rowfname]["OptionValues"]):
                    idx = gwi["FieldsData"][fname]["Columns"][rowfname]["OptionValues"].index(rowfvalue)
                    res = gwi["FieldsData"][fname]["Columns"][rowfname]["OptionLabels"][idx]
                else:
                    return tr(res)
            else:
                return tr(res)
        else:
            return tr(res)
        return tr(res)
    class ScrollAreaView(object):
        class Listener(object):
            def onModified(self):
                pass
        def __init__(self):
            self.listeners = set()
            self.scrollArea = None
        def addListener(self, l):
            self.listeners.add(l)
        def removeListener(self, l):
            self.listeners.remove(l)
        def notifyModification(self):
            for l in self.listeners:
                l.onModified()
        def setScrollArea(self, sa):
            self.scrollArea = sa
            self.notifyModification()
        def getScrollArea(self):
            return self.scrollArea
        def clear(self):
            pass
            #~ self.scrollArea = None
            #~ self.notifyModification()
        def show(self):
            pass
        def repaintArea(self):
            pass

    class ScrollAreaViewListener(ScrollAreaView.Listener):
        def __init__(self, window, name, scrollareaview):
            self.__window = window
            self.__name = name
            self.__scrollareaview = scrollareaview
        def onModified(self):
            if not hasattr(self.__window, "windowid"):
                return
            rawAction("Window", self.__window.windowid, "scrollAreaViewModified", self.__name, value=(self.__scrollareaview.getScrollArea(),))

    def getScrollAreaView(self, name):
        if not name in self.__scrollareaviews:
            self.__scrollareaviews[name] = self.__class__.ScrollAreaView()
            self.__scrollareaviews[name].addListener(self.__class__.ScrollAreaViewListener(self, name, self.__scrollareaviews[name]))
        return self.__scrollareaviews[name]

    def currentField(self):
        return rawAction("Window", self.windowid, "getCurrentField", doReturn=True)
    def currentMatrixName(self):
        return rawAction("Window", self.windowid, "getCurrentMatrix", doReturn=True)
    def currentRow(self, fieldname):
        return rawAction("Window", self.windowid, "getCurrentRow", fieldname, doReturn=True)

    def getMatrixColumns(self, matrixname):
        #from ParserNew import WindowParser
        #windownode = WindowParser.get_instance(self.name()[:-6]).tree
        #try:
        #    matrixnode = windownode.find_first("matrix", name=matrixname)
        #except:
        #    matrixnode = windownode.find_first("matrix", fieldname=matrixname)
        #columnnodes = matrixnode.find_all('matrixcolumn')
        #return [col.attrs["fieldname"] for col in columnnodes]
        return []

    def setStyle(self, style):
        pass

    def filterPasteWindow(self, fieldname):
        return True
