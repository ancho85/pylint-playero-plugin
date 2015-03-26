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

    def close(self):
        self.sql = ""
        self.result = []

    def execute(self):
        self.sql = ""
        return True

    def rawExecute(self):
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
        pass
