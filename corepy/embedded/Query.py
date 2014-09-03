class Query(object):

    def __init__(self):
        self.sql = ""
        self.result = []

    def __len__(self):
        return len(self.result)

    def __getitem__(self, idx):
        return self.result[idx]

    def open(self):
        self.result = []
        return True

    def execute(self):
        self.sql = ""
        return True

    def setLimit(self, qty, offset=-1):
        pass

    def count(self):
        return len(self.result)

    def getSQL(self):
        return self.sql

    def setSQL(self, sql):
        self.sql = sql

    def addSQL(self, sql):
        self.sql += sql

    def parseSQL(self):
        import re
        table_pattern = re.compile("([^\\\])\[([^\]]*?)\]")
        field_pattern = re.compile("\{([^\}]*?)\}")
        value_pattern = re.compile("[svdt]\|([^\|]*?)\|")
        integer_value_pattern = re.compile("i\|([^\|]*?)\|")
        boolean_value_pattern = re.compile("b\|([^\|]*?)\|")
        where_and_pattern = re.compile("(WHERE\?AND)")
        schemas_pattern = re.compile("\[([^\]]*?)\]")

        global k
        k = 0
        def where_and_replacer(mo):
            global k
            k += 1
            if k == 1: return "WHERE"
            return "AND"
        def value_replacer(mo):
            return "'%s'" % mo.group(1).replace("[","\\[").replace("{", "\\{")
        def integer_value_replacer(mo):
            return "%s" % mo.group(1).replace("[","\\[").replace("{", "\\{")
        def boolean_value_replacer(mo):
            return {"true": "1", "1": "1", "false": "0", "0": "0"}[mo.group(1).replace("[","\\[").replace("{", "\\{").lower()]
        self.sql = value_pattern.sub(value_replacer, self.sql)
        self.sql = boolean_value_pattern.sub(boolean_value_replacer, self.sql)
        self.sql = integer_value_pattern.sub(integer_value_replacer, self.sql)
        self.sql = table_pattern.sub("\g<1>`\g<2>`", self.sql)
        self.sql = field_pattern.sub("`\g<1>`", self.sql)
        self.sql = where_and_pattern.sub(where_and_replacer, self.sql)
        self.sql = self.sql.replace("\\[", "[").replace("\\{", "{")
