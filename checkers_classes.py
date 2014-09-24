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


from astroid.node_classes import Getattr, AssAttr, Const, \
                                    If, BinOp, CallFunc, Name, Tuple, \
                                    Return, Assign, AugAssign, AssName
from astroid.bases import YES
from astroid.exceptions import InferenceError
from pylint.interfaces import IAstroidChecker
from pylint.checkers.utils import check_messages
from tools import filenameFromPath
from sqlparse import validateSQL
from collections import Iterable

class QueryChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = 'playero-query-checker'
    msgs = {
            'W6602': ("query inference could not be resolved (%s)",
                                'query-inference',
                                "Query could not be resolved"),
            'E6601': ("query syntax error (%s)",
                                'query-syntax-error',
                                "Query sentence has a syntax error"),
        }
    options = ()

    queryTxt = {}

    def getAssNameValue(self, nodeValue, nodeName=""):
        anvalue = ""
        if isinstance(nodeValue, Assign):
            if isinstance(nodeValue.targets[0], AssName):
                if nodeName and nodeName == nodeValue.targets[0].name:
                    anvalue = self.getAssignedTxt(nodeValue.value)
        elif isinstance(nodeValue, AugAssign):
            if isinstance(nodeValue.target, AssName):
                if nodeName and nodeName == nodeValue.target.name:
                    anvalue = self.getAssignedTxt(nodeValue.value)
        elif isinstance(nodeValue, If):
            for elm in nodeValue.body:
                assValue = self.getAssNameValue(elm, nodeName)
                anvalue += self.getAssignedTxt(assValue)
        return anvalue

    def getNameValue(self, nodeValue):
        nvalue = ""
        if isinstance(nodeValue.statement(), Return):
            for elm in nodeValue.parent.scope().body:
                assValue = self.getAssNameValue(elm, nodeName=nodeValue.name)
                nvalue += self.getAssignedTxt(assValue)
        else:
            inferedValue = nodeValue.infered()[0]
            if inferedValue is not YES:
                nvalue = self.getAssignedTxt(inferedValue)
        if not nvalue: nvalue = "1"
        return nvalue

    def getCallFuncValue(self, nodeValue):
        cfvalue = ""
        lastchild = nodeValue.func.infered()[0].last_child()
        if isinstance(lastchild, Return):
            cfvalue = self.getAssignedTxt(lastchild.value)
        return cfvalue

    def getBinOpValue(self, nodeValue):
        qvalue = self.getAssignedTxt(nodeValue.left)
        if nodeValue.op == "%":
            newleft = '"%s "' % qvalue.replace("%i","%s").replace("%d", "%s")
            newright = "(\'%s\')" % ("','" * (qvalue.count("%s") - 1))
            if isinstance(nodeValue.right, Tuple):
                newright = self.getTupleValues(nodeValue.right)
            elif isinstance(nodeValue.right, CallFunc):
                callfuncval = self.getCallFuncValue(nodeValue.right)
                if callfuncval: newright = "(\"%s\")" % callfuncval
            elif isinstance(nodeValue.right, Name):
                newright = "(\"%s\")" % self.getNameValue(nodeValue.right)
            toeval = str("%s %% %s" % (newleft, newright)).replace("\n","NEWLINE")
            try:
                qvalue = eval(toeval)
                qvalue = qvalue.replace("NEWLINE","\n")
            except Exception, e:
                logHere("EvaluationError getBinOpValue", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        else:
            qvalue += self.getAssignedTxt(nodeValue.right)
        return qvalue

    def getTupleValues(self, nodeValue):
        tvalues = []
        for elts in nodeValue.itered():
            if isinstance(elts, Name):
                elts = self.getNameValue(elts)
            tvalues.append(self.getAssignedTxt(elts))
        return "(\'%s\')" % "','".join(tvalues)

    def getAssignedTxt(self, nodeValue):
        qvalue = ""
        try:
            if type(nodeValue) == str:
                qvalue = nodeValue
            elif isinstance(nodeValue, Const):
                qvalue = nodeValue.value
            elif isinstance(nodeValue, BinOp):
                qvalue = self.getBinOpValue(nodeValue)
            elif isinstance(nodeValue, Tuple):
                qvalue = self.getTupleValues(nodeValue)
            elif isinstance(nodeValue, CallFunc):
                qvalue = self.getCallFuncValue(nodeValue)
            elif isinstance(nodeValue, Getattr):
                qvalue = nodeValue.attrname
            elif isinstance(nodeValue, Name):
                qvalue = self.getNameValue(nodeValue)
            else:
                inferedValue = nodeValue.infered()
                if inferedValue is YES:
                    raise InferenceError("YES reached")
                elif isinstance(inferedValue, Iterable) and isinstance(inferedValue[0], Const):
                    qvalue = inferedValue[0].value
                else:
                    self.add_message("W6602", line=nodeValue.fromlineno, node=nodeValue.scope(), args=nodeValue)
        except InferenceError, e:
            logHere("InferenceError getAssignedTxt", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        except Exception, e:
            logHere("Exception getAssignedTxt", e, nodeValue.as_string()[:60], filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return qvalue

    def setUpQueryTxt(self, nodeTarget, value, isnew=False):
        try:
            if nodeTarget.expr.infered()[0].pytype() == "Query.Query":
                instanceName = nodeTarget.expr.name
                if isnew or instanceName not in self.queryTxt:
                    self.queryTxt[instanceName] = ""
                if not isinstance(nodeTarget.parent.parent, If):
                    self.queryTxt[instanceName] += str(value)
                else:
                    if not isinstance(nodeTarget.parent.parent.parent, If): #First if in if-Elif-Else
                        self.queryTxt[instanceName] += str(value)
        except InferenceError, e:
            logHere("InferenceError setUpQueryTxt", e, filename="%s.log" % filenameFromPath(nodeTarget.root().file))

    def isSqlAssAttr(self, node):
        res = False
        if isinstance(node, AssAttr) and node.attrname == "sql":
            res = True
        return res

    def visit_assign(self, node):
        if self.isSqlAssAttr(node.targets[0]):
            qvalue = self.getAssignedTxt(node.value)
            self.setUpQueryTxt(node.targets[0], qvalue, isnew=True)

    def visit_augassign(self, node):
        if self.isSqlAssAttr(node.target):
            qvalue = self.getAssignedTxt(node.value)
            self.setUpQueryTxt(node.target, qvalue)

    @check_messages('query-syntax-error', 'query-inference')
    def visit_callfunc(self, node):
        if isinstance(node.func, Getattr) and node.func.attrname in ("open", "execute"):
            try:
                for x in node.infered():
                    try:
                        main = x.root().values()[0].frame()
                        if main.name == "Query":
                            name = node.func.expr.name
                            if name in self.queryTxt:
                                res = validateSQL(self.queryTxt[name])
                                if res:
                                    self.add_message("E6601", line=node.lineno, node=node, args="%s: %s" % (name, res))
                            else:
                                self.add_message("W6602", line=node.lineno, node=node, args=name)
                    except TypeError, e:
                        logHere("TypeError visit_callfunc", e, filename="%s.log" % filenameFromPath(node.root().file))
            except InferenceError, e:
                logHere("InferenceError visit_callfunc", e, filename="%s.log" % filenameFromPath(node.root().file))
