from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker
from libs.tools import logHere

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

    def process_module(self, node): # TODO: should redefine this method to "close"
        """write the cache statistics after plugin usage"""
        logHere(self.cache.getStatistics(), filename='stats.log')
        lastline = sum(1 for line in node.file_stream)
        self.add_message('C6666', lastline)


