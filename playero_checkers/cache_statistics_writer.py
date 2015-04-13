from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker
from libs.tools import logHere

class CacheStatisticWriter(BaseChecker):
    """write the cache statistics after plugin usage"""

    __implements__ = IRawChecker

    name = 'cache_statistics_writer'
    msgs = {'I6666': ('cache statistics writed at log directory',
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
        if self.cache.collectStats: #pragma: no cover
            logHere(self.cache.getStatistics(), filename='stats.log')
            lastline = len(node.file_stream.readlines())
            self.add_message('I6666', lastline)

    def close(self):
        self.cache.collectStats = False
