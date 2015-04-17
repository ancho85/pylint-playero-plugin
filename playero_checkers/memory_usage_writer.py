from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages
from libs.tools import logHere, filenameFromPath

class MemoryUsageWriter(BaseChecker):
    """write the memory usage after plugin usage"""

    __implements__ = (IRawChecker,)

    name = 'memory_usage_writer'
    msgs = {
        'C6667': ('memory usage was written at log directory',
                  'memory-written',
                  'Used when memory usage are written at log directory'),
            }
    options = ()
    priority = -1000
    tr = None

    def open(self):
        from pympler import tracker
        self.tr = tracker.SummaryTracker()

    @check_messages("memory-written")
    def process_module(self, node):
        """write the cache statistics after plugin usage"""
        if False: #pragma: no cover
            lastline = len(node.file_stream.readlines())
            self.add_message('C6667', lastline)

    def close(self):
        #from pympler import refbrowser
        #ib = refbrowser.InteractiveBrowser(self.priority, maxdepth=1, repeat=False)
        #ib.main(standalone=True)

        #from pympler import summary, muppy
        #sum1 = summary.summarize(muppy.get_objects())
        #for line in summary.format_(sum1, limit=15, sort='size', order='descending'):
        #    logHere(line)

        fname = filenameFromPath(self.linter.base_file)
        from pympler import tracker, summary, muppy
        tr = tracker.SummaryTracker()
        sum2 = summary.summarize(muppy.get_objects())
        diff = tr.diff(summary1=self.tr.s0, summary2=sum2)
        for line in summary.format_(diff, limit=15, sort='size', order='descending'):
            logHere(line, filename="memory-%s.log" % fname)
        from datetime import datetime
        logHere("\n%s\n" % datetime.now(), filename="memory-%s.log" % fname)
