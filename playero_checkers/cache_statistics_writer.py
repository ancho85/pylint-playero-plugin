from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from libs.tools import logHere

class CacheStatisticWriter(BaseChecker):
    """write the cache statistics after plugin usage"""

    __implements__ = (IRawChecker,)

    name = 'cache_statistics_writer'
    msgs = {
        'C6666': ('cache statistics was written at log directory',
                  'cache-written',
                  'Used when cache statistics are written at log directory'),
            }
    options = ()
    priority = -666
    cache = None

    def __init__(self, linter=None, cacheobj=None):
        super(CacheStatisticWriter, self).__init__(linter)
        self.cache = cacheobj

    @check_messages("cache-written")
    def process_module(self, node):
        """write the cache statistics after plugin usage"""
        if self.cache and self.cache.collectStats: #pragma: no cover
            logHere(self.cache.getStatistics(), filename='stats.log')
            lastline = len(node.file_stream.readlines())
            self.add_message('C6666', lastline)

    def close(self):
        if self.cache:
            self.cache.collectStats = False
