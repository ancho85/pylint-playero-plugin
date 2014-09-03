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

from astroid.node_classes import Getattr
from pylint.interfaces import IAstroidChecker
from pylint.checkers.utils import check_messages

class QueryChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = 'playero-query-checker'
    msgs = {
            'E6601': ("query syntax error (%s)",
                                'query-syntax-error',
                                "Query sentence have a syntax error")
        }
    options = ()

    @check_messages('query-syntax-error')
    def visit_callfunc(self, node):
        if isinstance(node.func, Getattr) and node.func.attrname == "open":
            for x in node.infered():
                if x.root().values()[0].frame().name == "Query":
                    import os
                    HERE = os.path.dirname(os.path.abspath(__file__))
                    import imp
                    query = imp.load_source('Query', os.path.join(HERE, "corepy", "embedded", "Query.py"))
                    if not query:
                        self.add_message("E6601", line=node.lineno, node=node, args="QueryError")


