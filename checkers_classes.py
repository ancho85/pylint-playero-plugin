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
from sqlparse import validateSQL
from collections import Iterable
from funcs import inspectModule

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

    def getNameValue(self, nodeValue):
        nvalue = nodeValue.infered()[0]
        if nvalue is YES:
            nvalue = " "
            if isinstance(nodeValue.parent, Return):
                for elm in nodeValue.parent.scope().body:
                    if isinstance(elm, Assign) and elm.targets[0].name == nodeValue.name:
                        nvalue += str(elm.accept(self))
                    elif isinstance(elm, AugAssign) and elm.target.name == nodeValue.name:
                        nvalue += str(elm.accept(self))
            if not len(nvalue.strip()): nvalue = "1"
        return nvalue

    def getGetattrValue(self, nodeValue):
        gvalue = ""
        return gvalue

    def getCallFuncValue(self, nodeValue):
        cfvalue = ""
        lastchild = nodeValue.func.infered()[0].last_child()
        if isinstance(lastchild, Return):
            cfvalue = self.getAssignedTxt(lastchild.value)
        return cfvalue

    def getBinOpValue(self, nodeValue):
        qvalue = self.getAssignedTxt(nodeValue.left)
        newleft = '"%s "' % qvalue.replace("%i","%s").replace("%d", "%s")
        newright = "(\'0%s\')" % ("','" * (qvalue.count("%s") - 1))
        if isinstance(nodeValue.right, Tuple):
            newright = self.getTupleValues(nodeValue.right)
        elif isinstance(nodeValue.right, CallFunc):
            callfuncval = self.getCallFuncValue(nodeValue.right)
            if callfuncval:
                newright = "(\"%s\")" % callfuncval
        toeval = str("%s %% %s" % (newleft, newright)).replace("\n"," ")
        try:
            qvalue = eval(toeval)
        except Exception, e:
            logHere("EvaluationError getBinOpValue", toeval, e, filename="errors.log")
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
                qvalue = self.getGetattrValue(nodeValue)
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
            logHere("InferenceError getAssignedTxt", e, filename="errors.log")
        except Exception, e:
            logHere("Exception getAssignedTxt", e, filename="errors.log")
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
            logHere("InferenceError setUpQueryTxt", e, filename="errors.log")

    def visit_assign(self, node):
        if isinstance(node.targets[0], AssAttr):
            qvalue = self.getAssignedTxt(node.value)
            self.setUpQueryTxt(node.targets[0], qvalue, isnew=True)
        elif isinstance(node.targets[0], AssName):
            nvalue = self.getAssignedTxt(node.value)
            return nvalue

    def visit_augassign(self, node):
        if isinstance(node.target, AssAttr):
            qvalue = self.getAssignedTxt(node.value)
            self.setUpQueryTxt(node.target, qvalue)
        elif isinstance(node.target, AssName):
            nvalue = self.getAssignedTxt(node.value)
            return nvalue

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
                                    self.add_message("E6601", line=node.lineno, node=node, args="%s near: %s" % (name, res))
                            else:
                                self.add_message("W6602", line=node.lineno, node=node, args=name)
                    except TypeError, e:
                        logHere("TypeError visit_callfunc", e, filename="errors.log")
            except InferenceError, e:
                logHere("InferenceError visit_callfunc", e, filename="errors.log")
