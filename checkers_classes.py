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
                                    Return, Assign, AugAssign, AssName, \
                                    Keyword, Compare
from astroid.scoped_nodes import Function, Class
from astroid.bases import YES, Instance
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
    funcParams = {}

    def setUpFuncParams(self, node):
        if isinstance(node.func, Getattr):
            funcname = node.func.attrname
        elif isinstance(node.func, Name):
            funcname = node.func.name
        if funcname not in self.funcParams:
            self.funcParams[funcname] = {}
        index = 0
        for nodearg in node.args:
            index += 1
            if isinstance(nodearg, Keyword):
                self.funcParams[funcname][nodearg.arg] = self.getAssignedTxt(nodearg.value)
            else:
                self.funcParams[funcname][index] = self.getAssignedTxt(nodearg)

    def getFuncParams(self, node):
        fparam = ""
        nodescope = node.scope()
        if isinstance(nodescope, Function):
            if node.name in node.scope().argnames():
                funcname = node.scope().name
                if funcname in self.funcParams:
                    index = 0
                    for funcarg in nodescope.args.args:
                        index += 1
                        if isinstance(funcarg, AssName):
                            if funcarg.name in ("self", "classobj", "cls") and index == 1:
                                index -= 1
                                continue
                            else:
                                if node.name == funcarg.name:
                                    if funcarg.name in self.funcParams[funcname]:
                                        fparam = self.funcParams[funcname][funcarg.name]
                                    elif index in self.funcParams[funcname]:
                                        fparam = self.funcParams[funcname][index]
        return fparam

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
            lookBody = True
            if isinstance(nodeValue.test, Compare):
                leftval = self.getAssignedTxt(nodeValue.test.left)
                op = nodeValue.test.ops[0] #a list with 1 tuple
                rightval = self.getAssignedTxt(op[1])
                evaluation = "'%s' %s '%s'" % (leftval, op[0], rightval)
                lookBody = eval(evaluation)
            if lookBody:
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
            nvalue = self.getFuncParams(nodeValue)
            if not nvalue:
                inferedValue = nodeValue.infered()[0]
                if inferedValue is not YES:
                    nvalue = self.getAssignedTxt(inferedValue)
        return nvalue

    def getCallFuncValue(self, nodeValue):
        self.setUpFuncParams(nodeValue)
        cfvalue = ""
        lastchild = nodeValue.func.infered()[0].last_child()
        if isinstance(lastchild, Return):
            cfvalue = self.getAssignedTxt(lastchild.value)
        return cfvalue

    def getBinOpValue(self, nodeValue):
        qvalue = self.getAssignedTxt(nodeValue.left)
        if nodeValue.op == "%":
            newleft = '"%s "' % qvalue.replace("%i","%s").replace("%d", "%s")
            newright = '("%s")' % ('","' * (qvalue.count("%s") - 1))
            if isinstance(nodeValue.right, Tuple):
                newright = self.getTupleValues(nodeValue.right)
            elif isinstance(nodeValue.right, CallFunc):
                callfuncval = self.getCallFuncValue(nodeValue.right)
                if callfuncval: newright = "(\"%s\")" % callfuncval
            elif isinstance(nodeValue.right, Name):
                newright = "(\"%s\")" % self.getNameValue(nodeValue.right)
            elif isinstance(nodeValue.right, Getattr):
                getattrval = self.getAssignedTxt(nodeValue.right)
                if getattrval: newright = '("%s")' % getattrval
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

    def getGetattrValue(self, nodeValue):
        gvalue = nodeValue.attrname
        inferedValue = nodeValue.expr.infered()[0]
        res = ""
        if isinstance(inferedValue, Instance) and isinstance(inferedValue.infered()[0], Class):
            res = self.getClassAttr(inferedValue.infered()[0], gvalue)
        return {True:res, False:nodeValue.attrname}[bool(res)]

    def getClassAttr(self, nodeValue, attrSeek=""):
        cvalue = ""
        for attr in nodeValue["__init__"].body:
            if isinstance(attr, Assign):
                if isinstance(attr.targets[0], AssAttr):
                    if attr.targets[0].attrname == attrSeek:
                        cvalue = self.getAssignedTxt(attr.value)
        return cvalue

    def getAssignedTxt(self, nodeValue):
        qvalue = ""
        try:
            if type(nodeValue) in (type(None), int, str, float):
                qvalue = str(nodeValue)
            elif isinstance(nodeValue, Const):
                qvalue = str(nodeValue.value)
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
            elif isinstance(nodeValue, Class):
                qvalue = self.getClassAttr(nodeValue)
            else:
                inferedValue = nodeValue.infered()
                if inferedValue is YES:
                    raise InferenceError("YES reached")
                elif isinstance(inferedValue, Iterable) and nodeValue != inferedValue[0]:
                    qvalue = self.getAssignedTxt(inferedValue[0])
                else:
                    self.add_message("W6602", line=nodeValue.fromlineno, node=nodeValue.scope(), args=nodeValue)
        except InferenceError, e:
            logHere("InferenceError getAssignedTxt", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        except Exception, e:
            logHere("Exception getAssignedTxt", e, nodeValue.as_string()[:100], filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return qvalue

    def setUpQueryTxt(self, nodeTarget, value, isnew=False):
        try:
            if nodeTarget.expr.infered()[0].pytype() == "Query.Query":
                nodeGrandParent = nodeTarget.parent.parent #First parent is Assign or AugAssign
                instanceName = nodeTarget.expr.name
                if isnew or instanceName not in self.queryTxt:
                    self.queryTxt[instanceName] = ""
                if not isinstance(nodeGrandParent, If):
                    self.queryTxt[instanceName] += str(value)
                else:
                    if nodeTarget.parent not in nodeGrandParent.orelse: #Only first part of If... ElIf and Else will not be included
                        self.queryTxt[instanceName] += str(value)
        except InferenceError, e:
            logHere("InferenceError setUpQueryTxt", e, filename="%s.log" % filenameFromPath(nodeTarget.root().file))

    def isSqlAssAttr(self, node):
        return isinstance(node, AssAttr) and node.attrname == "sql"

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
