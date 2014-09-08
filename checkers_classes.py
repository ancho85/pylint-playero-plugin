from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker
from tools import logHere

class CacheStatisticWriter(BaseChecker):
    """write the cache statistics after plugin usage"""

    __implements__ = IRawChecker

    name = 'cache_statistics_writer'
    msgs = {'C6666': ('cache statistics writed at log directory',
                      ('cache statistics writed at log directory'),
                      ('cache statistics writed at log directory')),
            }
    options = ()
    priority = -666
    cache = None

    def __init__(self, linter=None, cacheobj=None):
        super(CacheStatisticWriter, self).__init__(linter)
        self.cache = cacheobj

    def process_module(self, node):
        """write the cache statistics after plugin usage"""
        logHere(self.cache.getStatistics(), 'stats.log')
        lastline = sum(1 for line in node.file_stream)
        self.add_message('C6666', lastline)


from astroid.node_classes import Getattr, AssAttr, Const
from pylint.interfaces import IAstroidChecker
from pylint.checkers.utils import check_messages
from sqlparse import parseSQL, validateSQL

class QueryChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = 'playero-query-checker'
    msgs = {
            'E6601': ("query syntax error (%s)",
                                'query-syntax-error',
                                "Query sentence have a syntax error"),
        }
    options = ()

    queryTxt = {}

    @staticmethod
    def getAssignedTxt(node):
        qvalue = ""
        if isinstance(node.value, Const):
            qvalue = node.value.value
        elif isinstance(node.value.infered()[0], Const):
            qvalue = node.value.infered()[0].value
        return qvalue

    def setUpQueryTxt(self, nodeTarget, value):
        if nodeTarget.expr.infered()[0].pytype() == "Query.Query":
            instanceName = nodeTarget.expr.name
            if instanceName not in self.queryTxt:
                self.queryTxt[instanceName] = ""
            self.queryTxt[instanceName] += value

    def visit_assign(self, node):
        if isinstance(node.targets[0], AssAttr):
            qvalue = self.getAssignedTxt(node)
            self.setUpQueryTxt(node.targets[0], qvalue)

    def visit_augassign(self, node):
        if isinstance(node.target, AssAttr):
            qvalue = self.getAssignedTxt(node)
            self.setUpQueryTxt(node.target, qvalue)

    @check_messages('query-syntax-error')
    def visit_callfunc(self, node):
        if isinstance(node.func, Getattr) and node.func.attrname == "open":
            for x in node.infered():
                main = x.root().values()[0].frame()
                if main.name == "Query":
                    name = node.func.expr.name
                    parsed = parseSQL(self.queryTxt[name])
                    from sqlparse import validateSQL
                    res = validateSQL(self.queryTxt[name])
                    self.add_message("E6601", line=node.lineno, node=node, args="QuerySyntaxError")
