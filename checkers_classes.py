from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker
from tools import logHere, escapeAnyToString

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
        logHere(self.cache.getStatistics(), filename='stats.log')
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

    queryTxt = {} # instanceName : parsedSQLtext
    funcParams = {} # functionName : argumentName : argumentValue

    def setUpFuncParams(self, node):
        """define the funcParams dict based directly on the function"""
        if not isinstance(node, Function): return
        funcname = node.name
        try:
            if funcname not in self.funcParams:
                self.funcParams[funcname] = {}
            for funcarg in node.args.args:
                argname = funcarg.name
                if argname in ("self", "classobj", "cls"): continue
                argvalue = self.getNameValue(funcarg)
                self.funcParams[funcname][argname] = self.getAssignedTxt(argvalue)
        except Exception, e:
            logHere("setUpFuncParamsError", e, filename="%s.log" % filenameFromPath(node.root().file))

    def setUpCallFuncParams(self, node):
        """ define the funcParams dict based of a function call"""
        if not isinstance(node, CallFunc): return
        if isinstance(node.func, Getattr):
            funcname = node.func.attrname
        elif isinstance(node.func, Name):
            funcname = node.func.name
        try:
            if funcname not in self.funcParams:
                self.funcParams[funcname] = {}
            index = 0
            for nodearg in node.args:
                index += 1
                if isinstance(nodearg, Keyword):
                    self.funcParams[funcname][nodearg.arg] = self.getAssignedTxt(nodearg.value)
                else:
                    self.funcParams[funcname][index] = self.getAssignedTxt(nodearg)
        except Exception, e:
            logHere("setUpCallFuncParamsError", e, filename="%s.log" % filenameFromPath(node.root().file))

    def getFuncParams(self, node):
        fparam = ""
        nodescope = node.scope()
        try:
            if isinstance(nodescope, Function):
                if hasattr(node, "name") and node.name in nodescope.argnames():
                    funcname = nodescope.name
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
        except Exception, e:
            logHere("getFuncParamsError", e, filename="%s.log" % filenameFromPath(node.root().file))
        return fparam

    def getAssNameValue(self, nodeValue, nodeName=""):
        anvalue = ""
        try:
            if isinstance(nodeValue, Assign):
                if isinstance(nodeValue.targets[0], AssName):
                    if nodeName and nodeName == nodeValue.targets[0].name:
                        anvalue = self.getAssignedTxt(nodeValue.value)
            elif isinstance(nodeValue, AugAssign):
                if isinstance(nodeValue.target, AssName):
                    if nodeName and nodeName == nodeValue.target.name:
                        anvalue = self.getAssignedTxt(nodeValue.value)
            elif isinstance(nodeValue, If):
                if nodeValue.test.as_string().find(nodeName) > -1:
                    lookBody = True
                    if isinstance(nodeValue.test, Compare):
                        if nodeName not in nodeValue.parent.scope().keys():
                            leftval = self.getAssignedTxt(nodeValue.test.left)
                            op = nodeValue.test.ops[0] #a list with 1 tuple
                            rightval = self.getAssignedTxt(op[1])
                            evaluation = '"""%s""" %s """%s"""' % (leftval, op[0], rightval)
                            try:
                                lookBody = eval(evaluation)
                            except Exception, e:
                                logHere("EvaluationError getAssNameValue", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
                        else:
                            anvalue = self.getFuncParams(nodeValue.parent)
                            if anvalue: lookBody = False
                    if lookBody:
                        anvalue = self.getIfValues(nodeValue, nodeName)
                    if not anvalue: anvalue = nodeName
                else:
                    anvalue = self.getIfValues(nodeValue, nodeName)
        except Exception, e:
            logHere("getAssNameValueError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return anvalue

    def getIfValues(self, nodeValue, nodeName=""):
        ivalue = ""
        try:
            for elm in nodeValue.body:
                assValue = self.getAssNameValue(elm, nodeName)
                ivalue += self.getAssignedTxt(assValue)
            if not ivalue:
                for elm2 in nodeValue.orelse:
                    assValue = self.getAssNameValue(elm2, nodeName)
                    ivalue += self.getAssignedTxt(assValue)
        except Exception, e:
            logHere("getIfValuesError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return ivalue

    def getNameValue(self, nodeValue):
        nvalue = ""
        try:
            if isinstance(nodeValue.statement(), Return):
                for elm in nodeValue.parent.scope().body:
                    if nodeValue.statement() == elm: continue #Returns are ignored
                    assValue = self.getAssNameValue(elm, nodeName=nodeValue.name)
                    nvalue += self.getAssignedTxt(assValue)
            else:
                nvalue = self.getFuncParams(nodeValue)
                if not nvalue:

                    try:
                        inferedValue = nodeValue.infered()
                    except InferenceError:
                        pass
                    else:
                        for inferedValue in inferedValue:
                            if inferedValue is not YES:
                                nvalue = self.getAssignedTxt(inferedValue)
                                if nvalue: break
                    if not nvalue:
                        if nodeValue.name in nodeValue.scope().keys():
                            for elm in nodeValue.scope().body:
                                if elm.lineno > nodeValue.lineno: break #finding values if element's line is previous to node's line
                                assValue = self.getAssNameValue(elm, nodeName=nodeValue.name)
                                nvalue = self.getAssignedTxt(assValue)
                                if nvalue: break
        except Exception, e:
            logHere("getNameValueError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return nvalue

    def getCallFuncValue(self, nodeValue):
        self.setUpCallFuncParams(nodeValue)
        cfvalue = ""
        try:
            lastchild = nodeValue.func.infered()[0].last_child()
        except Exception, e:
            if isinstance(nodeValue.func, Getattr):
                if nodeValue.func.attrname == "name":
                    if isinstance(nodeValue.func.expr, Name):
                        parent = nodeValue.func.scope().parent
                        if isinstance(parent, Class):
                            cfvalue = parent.name
            elif isinstance(nodeValue.func, Name):
                if nodeValue.func.name == "date":
                    cfvalue = "2000-01-01"
                elif nodeValue.func.name == "time":
                    cfvalue = "00:00:00"
        else:
            if isinstance(lastchild, Return):
                cfvalue = self.getAssignedTxt(lastchild.value)
        return cfvalue

    def getBinOpValue(self, nodeValue):
        try:
            qvalue = self.getAssignedTxt(nodeValue.left)
            if nodeValue.op == "%":
                newleft = '"%s "' % escapeAnyToString(qvalue)
                newright = '("%s")' % ('","' * (newleft.count("%s") - 1))
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
                elif isinstance(nodeValue.right, Const):
                    newright = self.getAssignedTxt(nodeValue.right)
                else:
                    newright = '("%s")' % self.getAssignedTxt(nodeValue.right)
                toeval = str("%s %% %s" % (newleft, newright)).replace("\n", "NEWLINE")
                qvalue = eval(toeval)
                qvalue = qvalue.replace("NEWLINE", "\n")
            else:
                qvalue += self.getAssignedTxt(nodeValue.right)
        except Exception, e:
            logHere("getBinOpValueError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return qvalue

    def getTupleValues(self, nodeValue):
        tvalues = []
        try:
            for elts in nodeValue.itered():
                if isinstance(elts, Name):
                    elts = self.getNameValue(elts)
                tvalues.append(self.getAssignedTxt(elts))
        except Exception, e:
            logHere("getTupleValuesError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return '("""%s""")' % '""","""'.join(tvalues)

    def getGetattrValue(self, nodeValue):
        try:
            gvalue = nodeValue.attrname
            inferedValue = nodeValue.expr.infered()[0]
            res = ""
            if isinstance(inferedValue, Instance) :
                if isinstance(inferedValue.infered()[0], Class):
                    if inferedValue.pytype() == "Query.Query" and nodeValue.expr.name in self.queryTxt:
                        res = self.queryTxt[nodeValue.expr.name]
                    else:
                        res = self.getClassAttr(inferedValue.infered()[0], gvalue)
        except Exception, e:
            logHere("getGetattrValueError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return {True:res, False:nodeValue.attrname}[bool(res)]

    def getClassAttr(self, nodeValue, attrSeek=""):
        cvalue = ""
        try:
            if "__init__" in nodeValue:
                for attr in nodeValue["__init__"].body:
                    if isinstance(attr, Assign):
                        if isinstance(attr.targets[0], AssAttr):
                            if attr.targets[0].attrname == attrSeek or attrSeek == "returnFirst":
                                cvalue = self.getAssignedTxt(attr.value)
                                if cvalue and attrSeek == "returnFirst": break
            if not cvalue:
                if "bring" in nodeValue.locals:
                    cvalue = self.getClassAttr(nodeValue.locals["bring"][0], attrSeek)
        except Exception, e:
            logHere("getClassAttrError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return cvalue

    def getAssignedTxt(self, nodeValue):
        fname = self.getNodeFileName(nodeValue)
        if type(nodeValue) in (type(None), int, str, float):
            return str(nodeValue)
        qvalue = ""
        try:
            if isinstance(nodeValue, Const):
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
                qvalue = self.getClassAttr(nodeValue, "returnFirst")
            else:
                inferedValue = nodeValue.infered()
                if isinstance(inferedValue, Iterable) and nodeValue != inferedValue[0]:
                    if not inferedValue[0] is YES:
                        qvalue = self.getAssignedTxt(inferedValue[0])
                else:
                    self.add_message("W6602", line=nodeValue.fromlineno, node=nodeValue.scope(), args=nodeValue)
        except InferenceError, e:
            logHere("getAssignedTxtInferenceError", e, filename="%s.log" % fname)
        except Exception, e:
            logHere("getAssignedTxtError", e, nodeValue.as_string()[:100], filename="%s.log" % fname)
        return qvalue

    def setUpQueryTxt(self, nodeTarget, value, isnew=False):

        def addUpQuery(instanceName, value):
            if isnew or instanceName not in self.queryTxt:
                self.queryTxt[instanceName] = ""
            self.queryTxt[instanceName] += str(value)

        try:
            if nodeTarget.expr.infered()[0].pytype() == "Query.Query":
                nodeGrandParent = nodeTarget.parent.parent #First parent is Assign or AugAssign
                instanceName = nodeTarget.expr.name
                if not isinstance(nodeGrandParent, If):
                    addUpQuery(instanceName, value)
                elif nodeTarget.parent not in nodeGrandParent.orelse: #Only first part of If... ElIf and Else will not be included
                    addUpQuery(instanceName, value)
        except InferenceError, e:
            logHere("setUpQueryTxtInferenceError", e, filename="%s.log" % filenameFromPath(nodeTarget.root().file))

    def isSqlAssAttr(self, node):
        return isinstance(node, AssAttr) and node.attrname == "sql"

    def getNodeFileName(self, node):
        parsedFileName = None
        if hasattr(node, "root"):
            parsedFileName = filenameFromPath(node.root().file)
            if not parsedFileName or parsedFileName == "<?>":
                parsedFileName = "notFound"
        return parsedFileName


    ####### pylint's redefinitions #######

    def visit_assign(self, node):
        if self.isSqlAssAttr(node.targets[0]):
            self.setUpFuncParams(node.scope())
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
                inferedNode = node.infered()
            except InferenceError, e:
                pass
            else:
                for x in inferedNode:
                    xrootvalues = x.root().values()
                    if xrootvalues is YES: continue
                    try:
                        main = xrootvalues[0].frame()
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
