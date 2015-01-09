from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker
from tools import logHere, escapeAnyToString, isNumber

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
                                    Keyword, Compare, Subscript, For, \
                                    Dict, List, Index, Slice, Comprehension, \
                                    Discard
from astroid.scoped_nodes import Function, Class, ListComp
from astroid.bases import YES, Instance
from astroid.exceptions import InferenceError
from pylint.interfaces import IAstroidChecker
from pylint.checkers.utils import check_messages
from tools import filenameFromPath
from sqlparse import validateSQL
from collections import Iterable
import ast

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

    def concatOrReplace(self, node, nodeName, previousValue, newValue):
        res = previousValue
        newVal = self.getAssignedTxt(newValue)
        if isinstance(node, AugAssign):
            if isinstance(node.target, AssName):
                if nodeName == node.target.name:
                    res = previousValue+newVal
        elif isinstance(node, Assign):
            if isinstance(node.targets[0], AssName):
                if nodeName == node.targets[0].name:
                    res = newVal
                    if not isNumber(newVal) and isNumber(previousValue):
                        res = previousValue
        elif isinstance(node, If):
            for elm, atr in [(elm, atr) for atr in ("body", "orelse") for elm in getattr(node, atr)]:
                if res == newVal: continue
                elif previousValue and atr == "orelse": continue
                res = self.concatOrReplace(elm, nodeName, res, newVal)
        elif isinstance(node, (For, Discard)):
            res = newVal
        return res

    def getAssNameValue(self, nodeValue, nodeName="", tolineno=999999):
        anvalue = ""
        anfound = False

        def searchBody(node, attrs):
            bvalue, bfound = None, False
            getBVal = lambda x: "" if x is None else x
            for elm, atr in [(elm, atr) for atr in attrs for elm in getattr(node, atr) if elm.lineno < tolineno]:
                if not (bvalue and atr == "orelse"): #no need to search in 'orelse' if the 'body' returns a value
                    (assValue, afound) = self.getAssNameValue(elm, nodeName=nodeName, tolineno=tolineno)
                    if afound and assValue != bvalue:
                        bvalue = self.concatOrReplace(elm, nodeName, getBVal(bvalue), assValue)
                        bfound = afound
            return (getBVal(bvalue), bfound)

        try:
            if nodeValue.lineno > tolineno: return (anvalue, anfound)
            if isinstance(nodeValue, Assign):
                if isinstance(nodeValue.targets[0], AssName):
                    if nodeName and nodeName == nodeValue.targets[0].name:
                        anvalue = self.getAssignedTxt(nodeValue.value)
                        anfound = True
            elif isinstance(nodeValue, AugAssign):
                if isinstance(nodeValue.target, AssName):
                    if nodeName and nodeName == nodeValue.target.name:
                        anvalue = self.getAssignedTxt(nodeValue.value)
                        anfound = True
            elif isinstance(nodeValue, For):
                if isinstance(nodeValue.target, AssName):
                    if nodeName and nodeName == nodeValue.target.name:
                        anvalue = self.getAssignedTxt(nodeValue.iter)
                        anfound = True
                        anvalue = ast.literal_eval(anvalue)[0]
                if not anfound:
                    anvalue, anfound = searchBody(nodeValue, attrs=["body", "orelse"])
            elif isinstance(nodeValue, If):
                lookBody = self.doCompareValue(nodeValue, nodeName)
                if lookBody:
                    anvalue, anfound = searchBody(nodeValue, attrs=["body"])
                else:
                    anvalue, anfound = searchBody(nodeValue, attrs=["orelse"])
            elif isinstance(nodeValue, Discard):
                if isinstance(nodeValue.value, CallFunc):
                    nvf = nodeValue.value.func
                    if isinstance(nvf, Getattr) and isinstance(nvf.expr, Name):
                        if nodeName == nvf.expr.name:
                            if nvf.attrname in ("append", "extend"):
                                anvalue = self.getAssignedTxt(nodeValue.value.args[0])
                                anfound = True
        except Exception, e:
            logHere("getAssNameValueError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return (anvalue, anfound)

    def doCompareValue(self, nodeValue, nodeName):
        evalResult = True
        if isinstance(nodeValue.test, Compare):
            leftval = self.getAssignedTxt(nodeValue.test.left)
            op = nodeValue.test.ops[0] #a list with 1 tuple
            rightval = self.getAssignedTxt(op[1])
            if op[0] != "in": rightval = '"""%s"""' % rightval
            evaluation = '"""%s""" %s %s' % (leftval, op[0], rightval)
            try:
                evalResult = eval(evaluation)
            except Exception, e:
                logHere("EvaluationError doCompareValue %s" % evaluation, e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
            anvalue = self.getFuncParams(nodeValue.parent)
            if anvalue: evalResult = False
        return evalResult

    def getNameValue(self, nodeValue):
        nvalue = ""
        try:
            nvalue = self.getFuncParams(nodeValue)
            if not nvalue:
                tryinference = True
                for elm in nodeValue.scope().body:
                    if elm.lineno >= nodeValue.lineno: break #finding values if element's line is previous to node's line
                    (assValue, assFound) = self.getAssNameValue(elm, nodeName=nodeValue.name, tolineno=nodeValue.parent.lineno)
                    if assFound:
                        nvalue = self.concatOrReplace(elm, nodeValue.name, nvalue, assValue)
                        tryinference = False
                if not nvalue and tryinference:
                    try:
                        inferedValue = nodeValue.infered()
                    except InferenceError:
                        pass
                    else:
                        for inferedValue in inferedValue:
                            if inferedValue is not YES:
                                nvalue = self.getAssignedTxt(inferedValue)
                                if nvalue: break
        except Exception, e:
            logHere("getNameValueError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return nvalue

    def getCallFuncValue(self, nodeValue):
        self.setUpCallFuncParams(nodeValue)
        cfvalue = ""
        returns  = []
        try:
            returns = [x for x in nodeValue.func.infered()[0].nodes_of_class(Return)]
        except InferenceError, e:
            pass
        for retNode in returns:
            if isinstance(retNode.parent, If):
                try:
                    if self.doCompareValue(retNode.parent, nodeName=""):
                        cfvalue = self.getAssignedTxt(retNode.value)
                        break
                except Exception:
                    pass
            else:
                cfvalue = self.getAssignedTxt(retNode.value)
                break
        if not cfvalue:
            if isinstance(nodeValue.func, Name):
                if nodeValue.func.name == "date":
                    cfvalue = "2000-01-01"
                elif nodeValue.func.name == "time":
                    cfvalue = "00:00:00"
                elif nodeValue.func.name == "len":
                    cfvalue = len(self.getAssignedTxt(nodeValue.args[0]))
            elif isinstance(nodeValue.func, Getattr):
                if nodeValue.func.attrname == "name":
                    if isinstance(nodeValue.func.expr, Name):
                        parent = nodeValue.func.scope().parent
                        if isinstance(parent, Class):
                            cfvalue = parent.name
                elif nodeValue.func.attrname == "keys":
                    cfvalue = "['']"
                elif nodeValue.func.attrname == "join":
                    expr = self.getAssignedTxt(nodeValue.func.expr)
                    args = self.getAssignedTxt(nodeValue.args[0])
                    cfvalue = eval("'%s'.join(%s)" % (expr, args))
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
                elif isinstance(nodeValue.right, Dict):
                    tupleDictator = lambda (x, y): "'%s':'%s'" % (self.getAssignedTxt(x), self.getAssignedTxt(y))
                    newright = '{%s}' % ",".join(map(tupleDictator, nodeValue.right.items))
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
                tvalues.append(self.getAssignedTxt(elts))
        except Exception, e:
            logHere("getTupleValuesError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return '("""%s""")' % '""","""'.join(tvalues)

    def getGetattrValue(self, nodeValue):
        res = ""
        try:
            gvalue = nodeValue.attrname
            inferedValue = nodeValue.expr.infered()[0]
            if isinstance(inferedValue, Instance) :
                if isinstance(inferedValue.infered()[0], Class):
                    if inferedValue.pytype() == "Query.Query" and nodeValue.expr.name in self.queryTxt:
                        res = self.queryTxt[nodeValue.expr.name]
                    else:
                        res = self.getClassAttr(inferedValue.infered()[0], gvalue)
            elif isinstance(nodeValue.expr, Subscript):
                res = self.getSubscriptValue(nodeValue.expr)
        except InferenceError:
            pass #missing parameters?
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

    def getSubscriptValue(self, nodeValue):
        svalue = ""
        if isinstance(nodeValue.parent, Getattr) and nodeValue.parent.attrname == "sql":
            if isinstance(nodeValue.value, Name):
                instanceName = nodeValue.value.name
                if instanceName in self.queryTxt:
                    svalue = self.queryTxt[instanceName]
        else:
            if isinstance(nodeValue.value, Name):
                if nodeValue.value.name in nodeValue.parent.scope().keys():
                    nvalue = self.getNameValue(nodeValue.value)
                    idx = ""
                    if isinstance(nodeValue.slice, Index):
                        idx = self.getAssignedTxt(nodeValue.slice.value)
                    elif isinstance(nodeValue.slice, Slice):
                        low = self.getAssignedTxt(nodeValue.slice.lower)
                        up = self.getAssignedTxt(nodeValue.slice.upper)
                        if not low or low == "None": low = 0
                        if not up or up == "None": up = ""
                        idx = "%s:%s" % (low, up)
                    if nvalue and idx:
                        try:
                            svalue = eval("'%s'[%s]" % (nvalue, idx))
                        except Exception, e:
                            logHere("getSubscriptValueError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        return svalue

    def getListValue(self, nodeValue):
        return [self.getAssignedTxt(x) for x in nodeValue.elts]

    def getListCompValue(self, nodeValue):
        lvalue = "['']"
        targets = []
        fgen = nodeValue.generators[0]
        if isinstance(fgen, Comprehension):
            if isinstance(fgen.iter, CallFunc):
                evaluation = "'%s'.%s('%s')" % (self.getAssignedTxt(fgen.iter.func.expr), fgen.iter.func.attrname, self.getAssignedTxt(fgen.iter.args[0]))
                try:
                    targets = eval(evaluation)
                except Exception, e:
                    logHere("getListCompValueError", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
            else:
                targets = self.getAssignedTxt(fgen.iter)
        elements = []
        if isinstance(nodeValue.elt, CallFunc):
            if isinstance(nodeValue.elt.func, Getattr):
                try:
                    elements = [eval("'%s'.%s()" % (x, nodeValue.elt.func.attrname)) for x in targets]
                except Exception, e:
                    logHere("getListCompValueEval1Error", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        elif isinstance(nodeValue.elt, BinOp):
            try:
                elements = [eval("'%s' %s '%s'" % (self.getAssignedTxt(nodeValue.elt.left), nodeValue.elt.op, x)) for x in targets]
            except Exception, e:
                logHere("getListCompValueEval2Error", e, filename="%s.log" % filenameFromPath(nodeValue.root().file))
        else:
            elements = [self.getAssignedTxt(nodeValue.elt)]
        if elements:
            lvalue = str(elements)
        elif targets:
            lvalue = str(targets)
        return lvalue

    def getAssignedTxt(self, nodeValue):
        if type(nodeValue) in (type(None), int, str, float, list):
            return str(nodeValue)
        fname = self.getNodeFileName(nodeValue)
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
            elif isinstance(nodeValue, Subscript):
                qvalue = self.getSubscriptValue(nodeValue)
            elif isinstance(nodeValue, Class):
                qvalue = self.getClassAttr(nodeValue, "returnFirst")
            elif isinstance(nodeValue, List):
                qvalue = self.getListValue(nodeValue)
            elif isinstance(nodeValue, ListComp):
                qvalue = self.getListCompValue(nodeValue)
            else:
                inferedValue = nodeValue.infered()
                if isinstance(inferedValue, Iterable) and nodeValue != inferedValue[0]:
                    if not inferedValue[0] is YES:
                        qvalue = self.getAssignedTxt(inferedValue[0])
                else:
                    self.add_message("W6602", line=nodeValue.fromlineno, node=nodeValue.scope(), args=nodeValue)
        except InferenceError, e:
            logHere("getAssignedTxtInferenceError", e, nodeValue, nodeValue.as_string(), filename="%s.log" % fname)
        except Exception, e:
            logHere("getAssignedTxtError", e, nodeValue.as_string()[:100], filename="%s.log" % fname)
        return qvalue

    def setUpQueryTxt(self, nodeTarget, value, isnew=False):
        try:
            instanceName = None
            inferedValue = nodeTarget.expr.infered()[0]
            if inferedValue is YES:
                if isinstance(nodeTarget, AssAttr) and isinstance(nodeTarget.expr, Subscript) and nodeTarget.attrname == "sql":
                    if isinstance(nodeTarget.expr.value, Name):
                        instanceName = nodeTarget.expr.value.name
            if inferedValue.pytype() == "Query.Query" or instanceName:
                nodeGrandParent = nodeTarget.parent.parent #First parent is Assign or AugAssign
                instanceName = instanceName or nodeTarget.expr.name
                if not isinstance(nodeGrandParent, If):
                    self.appendQuery(instanceName, value, isnew)
                else:
                    self.preprocessQueryIfs(nodeTarget, instanceName, value, isnew)
        except InferenceError, e:
            logHere("setUpQueryTxtInferenceError", e, filename="%s.log" % filenameFromPath(nodeTarget.root().file))

    def appendQuery(self, instanceName, value, isnew):
        if isnew or instanceName not in self.queryTxt:
            self.queryTxt[instanceName] = ""
        self.queryTxt[instanceName] += str(value)

    def preprocessQueryIfs(self, nodeTarget, instanceName, value, isnew):
        nodeGrandParent = nodeTarget.parent.parent
        if nodeTarget.parent not in nodeGrandParent.orelse: #Only first part of If... Else will not be included
            if not isinstance(nodeGrandParent.parent, If): #ElIf will not be included
                self.appendQuery(instanceName, value, isnew)
            else:
                self.preprocessQueryIfs(nodeTarget.parent, instanceName, value, isnew)

    def isSqlAssAttr(self, node):
        return isinstance(node, AssAttr) and node.attrname == "sql"

    def getNodeFileName(self, node):
        parsedFileName = None
        if hasattr(node, "root") and hasattr(node.root(), "file"):
            filepath = node.root().file
            if filepath:
                parsedFileName = filenameFromPath(filepath)
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
                                res = validateSQL(self.queryTxt[name], filename="%sQUERY.log" % filenameFromPath(node.root().file))
                                if res:
                                    self.add_message("E6601", line=node.lineno, node=node, args="%s: %s" % (name, res))
                            else:
                                self.add_message("W6602", line=node.lineno, node=node, args=name)
                    except TypeError, e:
                        logHere("TypeError visit_callfunc", e, filename="%s.log" % filenameFromPath(node.root().file))
