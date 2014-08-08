from datetime import date, time, datetime
import calendar

from Embedded_Record import Embedded_Record
class DetailRecordListener(Embedded_Record.Listener):
    def __init__(self, field):
        self.field = field
    def fieldModified(self, fn, value):
        self.field.notifyModification()

class RecordList(list):

    def __init__(self, field):
        list.__init__(self)
        self.masterId = None
        self._removedrecords = []
        self._field = field
        self.listener = DetailRecordListener(field)

    def removedRecordsCount(self):
        return len(self._removedrecords)

    def clearRemovedRecords(self):
        self._removedrecords = []

    def count(self):
        return len(self)

    def getRecordByRowId(self,row):
        for i in self:
            if i.internalId==row:
                return i
        return None

    def append(self, row):
        try:
            row.masterId = self.masterid
        except AttributeError, e:
            pass
        try:
            row.rowNr = self[-1].rowNr + 1
        except IndexError, e:
            row.rowNr = 0
        row._master_record = self._field._record
        list.append(self, row)
        row.addListener(self.listener)
        self.notifyModification()

    def remove(self, idx):
        remrec = self[idx]
        del self[idx]
        remrec._master_record = None
        self._removedrecords.append(remrec)
        remrec.removeListener(self.listener)
        self.notifyModification()
        for row in self[idx:]:
            row.rowNr -= 1

    def getRemovedRecord(self, idx):
        return self._removedrecords[idx]

    def appendRemovedRecord(self, r):
        return self._removedrecords.append(r)

    def clear(self):
        while len(self):
            self._removedrecords.append(self.pop())
        self.notifyModification()

    def notifyModification(self):
        self._field.notifyModification()

    def name(self):
        return self._field.name()


class Embedded_Field(object):

    ClearValues = {"integer": 0, "masterid": 0, "string": "", "memo": "", "blob": "", "value": 0.0, "internalid": 0, "date": date(1900,1,1), "time": time(0,0,0), "boolean": False, "set": "", "detail": RecordList}

    def getClearValue(self):
        return Embedded_Field.ClearValues[self.fielddef.type]

    def __init__(self, record, fielddef):
        object.__init__(self)
        self.fielddef = fielddef
        self.setValue = getattr(self, Embedded_Field.Setters[self.fielddef.type])
        self._value = None
        self._record = record
        self.setNone()

    def name(self):
        if self.fielddef.type == "detail":
            return self.fielddef.recordname
        else:
            return self.fielddef.name

    def setNone(self):
        self.setValue(None)

    def getValue(self):
        return self._value

    def setValue(self, v):
        self._value = v
        if self._value is None:
            self.is_none = True
            self._value = Embedded_Field.getClearValue()
        else:
            self.is_none = False
        self.notifyModification()

    def getLinkTo(self):
        return self.fielddef.linkto

    def getMaxLength(self):
        return self.fielddef.length

    def isNone(self):
        return self.is_none

    def setValue_String(self, v):
        self._value = v
        if self._value is None:
            self.is_none = True
            self._value = self.getClearValue()
        else:
            self.is_none = False
        self.notifyModification()

    """
    def setValue_Memo(self, v):
        self._value = v
        if self._value is None:
            self.is_none = True
            self._value = self.getClearValue()
        else:
            self.is_none = False
        self.notifyModification()
    """

    def setValue_Memo(self, v):
        if v is None:
            self.is_none = True
            self._value = self.getClearValue()
        else:
            if isinstance(v, str):
                self._value = v.decode("latin1")
            else:
                self._value = v
            self.is_none = False
        self.notifyModification()

    def setValue_Integer(self, v):
        if self._value is None:
            self.is_none = True
            self._value = self.getClearValue()
        else:
            try:
                self._value = int(v)
                self.is_none = False
            except ValueError:
                v = str(v).strip()
                if not v:
                    self.setValue(0)
                else:
                    try:
                        self._value = int(v)
                        self.is_none = False
                    except ValueError:
                        pass
            except TypeError, e:
                if v is None:
                    self._value = 0
                    self.is_none = True
        self.notifyModification()

    def setValue_Value(self, v):
        self._value = v
        if self._value is None:
            self.is_none = True
            self._value = self.getClearValue()
        else:
            if isinstance(v, basestring):
                if not v:
                    self._value = 0.0
                else:
                    self._value = float(v)
            self.is_none = False
        self.notifyModification()

    def setValue_Date(self, v):
        if isinstance(v, date):
            self._value = v
        elif isinstance(v, datetime):
            self._value = v.date()
        elif isinstance(v, basestring):
            try:
                if "-" in v:
                    datetuple = v.split("-")
                    year = int(datetuple[0])
                    if year < 100:
                        year += 2000
                    if year < 1900:
                        raise ValueError
                    month = int(datetuple[1])
                    day = int(datetuple[2])
                elif "/" in v:
                    datetuple = v.split("/")
                    year = int(datetuple[2])
                    if year < 100:
                        year += 2000
                    if year < 1900:
                        raise ValueError
                    month = int(datetuple[1])
                    day = int(datetuple[0])
                maxmonthday = calendar.monthrange(year, month)[1]
                if day > maxmonthday:
                    day = maxmonthday
                self._value = date(year, month, day)
            except:
                pass
        if self._value is None:
            self.is_none = True
            self._value = self.getClearValue()
        else:
            self.is_none = False
        self.notifyModification()

    def setValue_Time(self, v):
        if isinstance(v, datetime):
            self._value = v.time()
        elif isinstance(v, time):
            self._value = v
        elif isinstance(v, basestring):
            if ":" in v:
                timetuple = v.split(":")
            elif "." in v:
                timetuple = v.split(".")
            else:
                return
            seconds = 0
            if len(timetuple) >= 3:
                seconds = int(timetuple[2])
            self._value = time(int(timetuple[0]), int(timetuple[1]), seconds)
        if self._value is None:
            self.is_none = True
            self._value = self.getClearValue()
        else:
            self.is_none = False
        self.notifyModification()

    def setValue_Boolean(self, v):
        if v is None:
            self.is_none = True
            self._value = self.getClearValue()
        else:
            self._value = bool(v)
            self.is_none = False
        self.notifyModification()

    def setValue_Detail(self, v):
        self._value = v
        if self._value is None:
            self.is_none = True
            self._value = self.getClearValue()
        else:
            self.is_none = False
        self.notifyModification()

    def isPersistent(self):
        return self.fielddef.persistent

    def getType(self):
        return self.fielddef.type

    def notifyModification(self):
        name = self.name()
        if isinstance(self, Embedded_DetailField):
            name = self.fielddef.name
        self._record.fieldModified(name, self._value)
        #~ self._record._modified = True
        master_record = self._record.getMasterRecord()
        if master_record:
            master_record._modified = True

    def getRecordName(self):
        return self.fielddef.recordname

    Setters = {"internalid": "setValue_Integer", "masterid": "setValue_Integer", "integer": "setValue_Integer", "string": "setValue_String", "blob": "setValue_String", "memo": "setValue_Memo", "value":  "setValue_Value", "internalId":  "setValue_Integer", "date":  "setValue_Date", "time":  "setValue_Time", "boolean":  "setValue_Boolean", "set":  "setValue_String", "detail":  "setValue_Detail"}


class Embedded_DetailField(Embedded_Field):

    def getClearValue(self):
        return RecordList(self)

    def __len__(self):
        return len(self._value)

    def __getitem__(self, idx):
        return self._value.__getitem__(idx)

    def removedRecordsCount(self):
        return self._value.removedRecordsCount()

    def getRemovedRecord(self, idx):
        return self._value.getRemovedRecord(idx)

    def clearRemovedRecords(self):
        return self._value.clearRemovedRecords()

    def appendRemovedRecord(self, r):
        return self._value.appendRemovedRecord(r)

    def count(self):
        return len(self)

    def setMasterId(self, mid):
        self._value.masterId = mid
        for r in self._value:
            r.masterId = mid
        self.notifyModification()

    def append(self, row):
        return self._value.append(row)

    def remove(self, idx):
        row.setMasterRecord(None)
        return self._value.remove(idx)

    def fieldNames(self):
        from globalfunctions import NewRecord
        return NewRecord(self.getRecordName()).fieldNames()

    def fieldType(self,fn):
        from globalfunctions import NewRecord
        return NewRecord(self.getRecordName()).fields(fn).getType()


