from pylint.checkers import BaseChecker
from astroid.node_classes import Getattr, AssAttr, Const, \
                                    If, BinOp, CallFunc, Name, Tuple, \
                                    Return, Assign, AugAssign, AssName, \
                                    Keyword, Compare, Subscript, For, \
                                    Dict, List, Slice, Comprehension, \
                                    Discard, Index
from astroid.scoped_nodes import Function, Class, ListComp
from astroid.bases import YES, Instance
from astroid.exceptions import InferenceError
from pylint.interfaces import IAstroidChecker
from pylint.checkers.utils import check_messages
from libs.tools import logHere, filenameFromPath, escapeAnyToString, isNumber, ifElse
from libs.sqlparse import validateSQL
from collections import Iterable
import ast
import re

def queryEnabled():
    from libs.funcs import getConfig
    return int(getConfig().get("mysql", "connect"))

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
    funcParams = {} # functionName : argumentIndex : argumentValue

    def setFuncParams(self, node):
        """ define the funcParams dict based of a function call"""
        if not isinstance(node, CallFunc): return
        if isinstance(node.func, Getattr):
            funcname = node.func.attrname
        elif isinstance(node.func, Name):
            funcname = node.func.name
        try:
            self.funcParams[funcname] = {}
            for idx, nodearg in enumerate(node.args):
                if isinstance(nodearg, Keyword):
                    idx, nodearg = nodearg.arg, nodearg.value #redefining index and value
                self.funcParams[funcname][idx] = self.getAssignedTxt(nodearg)
        except Exception, e:
            self.logError("setFuncParams", node, e)

    def getFuncParams(self, node, forceSearch=True):
        fparam = ""
        nodescope = node.scope()
        try:
            if isinstance(nodescope, Function):
                if hasattr(node, "name") and node.name in nodescope.argnames():
                    funcname = nodescope.name
                    if funcname in self.funcParams:
                        fp = self.funcParams[funcname]
                        funcargs = [x for x in nodescope.args.args if x.name not in ("self", "classobj", "cls")]
                        for idx, funcarg in enumerate(funcargs):
                            if node.name == funcarg.name:
                                fparam = fp.get(funcarg.name, fp.get(idx, "")) #get by name and then, by index
                    elif forceSearch: #funcname wasn't created
                        self.searchNode(nodescope.root(), funcname)
                        fparam = self.getFuncParams(node, forceSearch=False) #forceSearch=False to prevent infinite loop
        except Exception, e:
            self.logError("getFuncParamsError", node, e)
        return fparam

    def concatOrReplace(self, node, nodeName, previousValue, newValue):
        res = previousValue
        try:
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
            elif isinstance(node, For):
                if isinstance(node.target, AssName) and nodeName == node.target.name:
                    res = newVal
                else:
                    for elm, atr in [(elm, atr) for atr in ("body", "orelse") for elm in getattr(node, atr)]:
                        if res == newVal: continue
                        elif previousValue and atr == "orelse": continue
                        res = self.concatOrReplace(elm, nodeName, res, newVal)
            elif isinstance(node, Discard):
                if isinstance(node.value, CallFunc):
                    if hasattr(node.value.func, "expr") and isinstance(node.value.func.expr, Name):
                        if nodeName == node.value.func.expr.name:
                            res = newVal
        except Exception, e:
            self.logError("concatOrReplaceError", node, e)
        return res

    def getAssNameValue(self, nodeValue, nodeName="", tolineno=999999):
        if not tolineno: tolineno = 999999
        anvalue = ""
        anfound = False

        def searchBody(attrs):
            bvalue, bfound = None, False
            getBVal = lambda x: "" if x is None else x
            for elm, atr in [(elm, atr) for atr in attrs for elm in getattr(nodeValue, atr) if elm.lineno < tolineno]:
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
                        if not anvalue.startswith("["): anvalue = "['%s']" % anvalue
                        anfound = True
                        try:
                            anvalue = ast.literal_eval(anvalue)[0]
                        except Exception, e:
                            self.logError("getAssNameValueError literal_eval", nodeValue, e)
                if not anfound:
                    anvalue, anfound = searchBody(["body", "orelse"])
            elif isinstance(nodeValue, If):
                lookBody = self.doCompareValue(nodeValue)
                if lookBody:
                    anvalue, anfound = searchBody(["body"])
                else:
                    anvalue, anfound = searchBody(["orelse"])
            elif isinstance(nodeValue, Discard):
                if isinstance(nodeValue.value, CallFunc):
                    nvf = nodeValue.value.func
                    if isinstance(nvf, Getattr) and isinstance(nvf.expr, Name):
                        if nodeName == nvf.expr.name:
                            anvalue = self.getCallFuncValue(nodeValue.value)
                            anfound = True
        except Exception, e:
            self.logError("getAssNameValueError", nodeValue, e)
        return (anvalue, anfound)

    def doCompareValue(self, nodeValue):
        evalResult = True
        if isinstance(nodeValue.test, Compare):
            leftval = self.getAssignedTxt(nodeValue.test.left)
            op = nodeValue.test.ops[0] #a list with 1 tuple
            rightval = self.getAssignedTxt(op[1])
            if op[0] != "in": rightval = '"""%s"""' % rightval
            elif not rightval: rightval = "[0, 0]"
            evaluation = '"""%s""" %s %s' % (leftval, op[0], rightval)
            try:
                evalResult = eval(evaluation)
            except Exception, e:
                self.logError("EvaluationError doCompareValue %s" % evaluation, nodeValue, e)
            anvalue = self.getFuncParams(nodeValue.parent)
            if anvalue: evalResult = False
        return evalResult

    def getNameValue(self, nodeValue):
        nvalue = ""
        try:
            nvalue = self.getFuncParams(nodeValue)
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
                except InferenceError: # pragma: no cover
                    pass
                else:
                    for inferedValue in inferedValue:
                        if inferedValue is not YES:
                            nvalue = self.getAssignedTxt(inferedValue)
                            if nvalue: break
        except Exception, e:
            self.logError("getNameValueError", nodeValue, e)
        return nvalue

    def getFunctionReturnValue(self, funcNode):
        retVal = ""
        returns = [x for x in funcNode.nodes_of_class(Return)]
        for retNode in returns:
            if isinstance(retNode.parent, If):
                try:
                    if self.doCompareValue(retNode.parent):
                        retVal = self.getAssignedTxt(retNode.value)
                        break
                except Exception:
                    pass
            else:
                retVal = self.getAssignedTxt(retNode.value)
                break
        return retVal

    def getCallFuncValue(self, nodeValue):
        self.setFuncParams(nodeValue)
        cfvalue = ""
        nodefn = nodeValue.func
        try:
            inferedFunc = nodefn.infered()[0]
            cfvalue = self.getFunctionReturnValue(inferedFunc)
        except (InferenceError, TypeError) as e:
            pass #cannot be infered | cannot be itered. _Yes object?
        if not cfvalue:
            if isinstance(nodefn, Name):
                funcname = nodefn.name
                if funcname == "date":
                    cfvalue = "2000-01-01"
                elif funcname == "time":
                    cfvalue = "00:00:00"
                elif funcname == "len":
                    cfvalue = len(self.getAssignedTxt(nodeValue.args[0]))
                elif funcname == "map":
                    mapto = nodeValue.args[0]
                    target = self.getAssignedTxt(nodeValue.args[1])
                    if target in ("", "0"): target = "['0','0']"
                    evaluation = "map(%s, %s)" % (mapto.as_string(), target)
                    try:
                        cfvalue = str(eval(evaluation))
                    except Exception, e:
                        self.logError("getCallFuncValueMapEvalError", nodeValue, e)
                elif funcname == "filter":
                    pass
                else: #method may be locally defined
                    cfvalue = self.getCallUserDefinedName(nodeValue)
            elif isinstance(nodefn, Getattr):
                attrname = nodefn.attrname
                if attrname == "name":
                    if isinstance(nodefn.expr, Name):
                        parent = nodefn.scope().parent
                        if isinstance(parent, Class):
                            cfvalue = parent.name
                elif attrname == "keys":
                    cfvalue = "['0','0']"
                elif attrname == "join":
                    expr = self.getAssignedTxt(nodefn.expr)
                    args = self.getAssignedTxt(nodeValue.args[0])
                    if args:
                        if not args.startswith(("[", "'")): args = "'%s'" % args
                        cfvalue = "%s" % expr.join(["%s" % x for x in ast.literal_eval(args)])
                        if not cfvalue: cfvalue = "%s" % expr.join(['666'])
                elif attrname in ("append", "extend"):
                    cfvalue = self.getAssignedTxt(nodeValue.args[0])
                elif attrname == "split":
                    expr = self.getAssignedTxt(nodefn.expr)
                    args = self.getAssignedTxt(nodeValue.args[0])
                    cfvalue = "[%s]" % args.join(["'%s'" % str(x) for x in expr.split(args)])
                elif attrname == "replace":
                    arg1 = self.getAssignedTxt(nodeValue.args[0])
                    arg2 = self.getAssignedTxt(nodeValue.args[1])
                    cfvalue = self.getNameValue(nodefn.expr).replace(arg1, arg2)
                else:
                    # if reachs here, then the inference did not work
                    cfvalue = self.getCallGetattr(nodeValue)
        return cfvalue

    def getCallGetattr(self, node):
        cgattr = ""
        nodefn = node.func
        attrname = nodefn.attrname
        if isinstance(nodefn.expr, Getattr):
            if isinstance(nodefn.expr.expr, Name) and nodefn.expr.expr.name == "self":
                instAttrName = nodefn.expr.attrname
                prevSi = node.previous_sibling()
                while prevSi is not None:
                    if isinstance(prevSi, Assign):
                        target = prevSi.targets[0]
                        if isinstance(target, AssAttr):
                            if target.expr.name == "self" and target.attrname == instAttrName:
                                if isinstance(prevSi.value, CallFunc):
                                    inst = prevSi.value.infered()[0]
                                    if isinstance(inst, Instance):
                                        if attrname in inst.locals:
                                            cgattr = self.getFunctionReturnValue(inst.locals[attrname][0])
                                            break
                    prevSi = prevSi.previous_sibling()
        return cgattr

    def getCallUserDefinedName(self, node):
        cudnvalue = ""
        nodefn = node.func
        funcname = nodefn.name
        nodeScope = node.scope()
        if funcname in nodeScope.locals:
            methodParent = nodeScope.locals[funcname][0].parent
            if isinstance(methodParent, Assign):
                if isinstance(methodParent.value, CallFunc) and isinstance(methodParent.value.func, Name):
                    if methodParent.value.func.name == "getattr":
                        args = methodParent.value.args
                        if isinstance(args[0], Name) and args[0].name == "self":
                            methodname = self.getAssignedTxt(args[1]).strip() #the for must be analysed here
                            if methodname in nodeScope.parent.locals:
                                realmethod = nodeScope.parent.locals[methodname][0]
                                cudnvalue = self.getFunctionReturnValue(realmethod)
                            else:
                                #backwards name locator
                                try:
                                    sname = [child for child in args[1].get_children() if isinstance(child, Name)][0]
                                    forText1 = args[1].as_string().replace(sname.name, '"""forText"""')
                                    assignText1 = ""
                                    prevSi = node.previous_sibling()
                                    if prevSi is None: prevSi = node.parent
                                    while node.scope() == prevSi.scope(): #cannot go beyond this
                                        if isinstance(prevSi, Assign):
                                            if isinstance(prevSi.targets[0], AssName) and prevSi.targets[0].name == sname.name:
                                                sname = [child for child in prevSi.value.get_children() if isinstance(child, Name)][0]
                                                assignText1 = prevSi.value.as_string().replace(sname.name, '"""assignText1"""')
                                        elif isinstance(prevSi, For):
                                            if isinstance(prevSi.target, AssName) and prevSi.target.name == sname.name:
                                                value = self.getAssignedTxt(prevSi.iter)
                                                for methodname in ast.literal_eval(value):
                                                    from playero_transforms.classes import buildStringModule
                                                    assignText2 = assignText1.replace("assignText1", methodname)
                                                    newnode = buildStringModule(assignText2)
                                                    assignText2 = self.getAssignedTxt(newnode.body[0].value)
                                                    forText2 = forText1.replace("forText", assignText2)
                                                    newnode = buildStringModule(forText2)
                                                    methodname = self.getAssignedTxt(newnode.body[0].value).strip()
                                                    if methodname in nodeScope.parent.locals:
                                                        realmethod = nodeScope.parent.locals[methodname][0]
                                                        cudnvalue = self.getFunctionReturnValue(realmethod)
                                                        break
                                        prevParent = prevSi.parent
                                        prevSi = prevSi.previous_sibling()
                                        if not prevSi: prevSi = prevParent
                                except Exception, e:
                                    self.logError("backwards locator error", node, e)
        return cudnvalue

    def getBinOpValue(self, nodeValue):
        try:
            qvalue = self.getAssignedTxt(nodeValue.left)
            if nodeValue.op == "%":
                newleft = '"""%s """' % escapeAnyToString(qvalue)
                regex = re.compile(r"%(\(.+\))?s") #matches '%s' and '%(text)s'
                strFlagQty = len(regex.findall(newleft))
                if not strFlagQty: return newleft
                newright = '("%s")' % ('","' * (strFlagQty - 1))
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
                elif isinstance(nodeValue.right, Dict):
                    newright = self.getDictValue(nodeValue.right)
                else:
                    newright = '("%s")' % self.getAssignedTxt(nodeValue.right)
                toeval = str("%s %% %s" % (newleft, newright)).replace("\n", "NEWLINE")
                qvalue = eval(toeval)
                qvalue = qvalue.replace("NEWLINE", "\n")
            else:
                qvalue += self.getAssignedTxt(nodeValue.right)
        except Exception, e:
            self.logError("getBinOpValueError", nodeValue, e)
        return qvalue

    def getTupleValues(self, nodeValue):
        tvalues = []
        try:
            for elts in nodeValue.itered():
                tvalues.append(self.getAssignedTxt(elts))
        except Exception, e:
            self.logError("getTupleValuesError", nodeValue, e)
        return '("""%s""")' % '""","""'.join(tvalues)

    def getHeirValue(self, node):
        """locate attribute in inheritance by visiting all assignments"""
        heirVal = ""
        prevSi = node.previous_sibling()
        if isinstance(prevSi, Assign):
            if isinstance(prevSi.targets[0], AssName) and prevSi.targets[0].name == node.expr.name:
                if isinstance(prevSi.value, CallFunc) and isinstance(prevSi.value.func, Getattr):
                    if prevSi.value.func.expr.name == "self":
                        if prevSi.value.func.attrname not in node.scope().parent.locals: #the function called is not present
                            heirClass = node.scope().parent.bases[0].infered()[0]
                            heirCall = heirClass.locals[prevSi.value.func.attrname][0]
                            #Now I'm building self.queryTxt by visiting all Assigns and AugAssigns
                            prevKeys = self.queryTxt.keys()
                            for ass in heirCall.body:
                                if isinstance(ass, Assign):
                                    self.visit_assign(ass)
                                elif isinstance(ass, AugAssign):
                                    self.visit_augassign(ass)
                            newKey = [k for k in self.queryTxt if k not in prevKeys]
                            if newKey:
                                heirVal = self.queryTxt[newKey[0]]
        return heirVal

    def getGetattrValue(self, nodeValue):
        res = ""
        try:
            inferedValue = nodeValue.expr.infered()[0]
            if isinstance(inferedValue, Instance) :
                if isinstance(inferedValue.infered()[0], Class):
                    if inferedValue.pytype() == "Query.Query":
                        if nodeValue.expr.name in self.queryTxt:
                            res = self.queryTxt[nodeValue.expr.name]
                        else:
                            res = self.getHeirValue(nodeValue)
                    if not res:
                        res = self.getClassAttr(inferedValue.infered()[0], nodeValue.attrname)
            elif isinstance(nodeValue.expr, Subscript):
                res = self.getSubscriptValue(nodeValue.expr)
        except InferenceError:
            pass #missing parameters?
        except Exception, e:
            self.logError("getGetattrValueError", nodeValue, e)
        return [nodeValue.attrname, res][bool(res)]

    def getClassAttr(self, nodeValue, attrSeek=None):
        cvalue = ""
        try:
            for ofuncs in nodeValue.get_children():
                if isinstance(ofuncs, Assign):
                    if isinstance(ofuncs.targets[0], AssName):
                        if ofuncs.targets[0].name == attrSeek:
                            cvalue = self.getAssignedTxt(ofuncs.value)
                elif isinstance(ofuncs, Function):
                    for attr in nodeValue[ofuncs.name].body:
                        if isinstance(attr, Assign):
                            if isinstance(attr.targets[0], AssAttr):
                                if attr.targets[0].attrname == attrSeek or attrSeek is None:
                                    cvalue = self.getAssignedTxt(attr.value)
                        if cvalue: break
                if cvalue: break
            if not cvalue:
                if "bring" in nodeValue.locals:
                    cvalue = self.getClassAttr(nodeValue.locals["bring"][0], attrSeek)
        except Exception, e:
            self.logError("getClassAttrError", nodeValue, e)
        return cvalue

    def getSubscriptValue(self, nodeValue):
        svalue = ""
        if isinstance(nodeValue.parent, Getattr) and nodeValue.parent.attrname == "sql":
            if isinstance(nodeValue.value, Name):
                instanceName = nodeValue.value.name
                if instanceName in self.queryTxt:
                    svalue = self.queryTxt[instanceName]
        else:
            nvalue = ""
            if isinstance(nodeValue.value, Name):
                if nodeValue.value.name in nodeValue.parent.scope().keys():
                    nvalue = self.getNameValue(nodeValue.value)
            elif isinstance(nodeValue.value, List):
                nvalue = self.getListValue(nodeValue.value)
            elif isinstance(nodeValue.value, Const):
                nvalue = self.getAssignedTxt(nodeValue.value)
            if not nvalue.startswith(("[", "'", "{")): nvalue = "'%s'" % nvalue
            idx = "0"
            if isinstance(nodeValue.slice, Slice):
                low = self.getAssignedTxt(nodeValue.slice.lower)
                up = self.getAssignedTxt(nodeValue.slice.upper)
                if not low or low == "None": low = 0
                if not up or up == "None": up = ""
                idx = "%s:%s" % (low, up)
            elif isinstance(nodeValue.slice, Index):
                idx = self.getAssignedTxt(nodeValue.slice.value)
                if not idx: idx = "0"
            if len(nvalue)>2:
                evaluation = '%s[%s]' % (nvalue, idx)
                if nvalue.startswith("{"):
                    evaluation = '%s.get("%s", None)' % (nvalue, idx)
                try:
                    svalue = eval(evaluation)
                except IndexError:
                    svalue = eval('%s[0]' % nvalue)
                except Exception, e:
                    self.logError("getSubscriptValueError", nodeValue, e)
        return svalue

    def getListValue(self, nodeValue):
        return "['%s']" % "','".join([self.getAssignedTxt(x) for x in nodeValue.elts])

    def getDictValue(self, nodeValue):
        tupleDictator = lambda (x, y): "'%s':'%s'" % (self.getAssignedTxt(x), self.getAssignedTxt(y))
        return '{%s}' % ",".join(map(tupleDictator, nodeValue.items))

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
                    self.logError("getListCompValueError", nodeValue, e)
            elif isinstance(fgen.iter, Name):
                targets = self.getNameValue(fgen.iter)
            else:
                targets = ast.literal_eval(self.getAssignedTxt(fgen.iter))
        elements = []
        if isinstance(nodeValue.elt, CallFunc):
            if isinstance(nodeValue.elt.func, Getattr):
                try:
                    elements = [eval("'%s'.%s()" % (x, nodeValue.elt.func.attrname)) for x in targets]
                except Exception, e:
                    self.logError("getListCompValueEval1Error", nodeValue, e)
        elif isinstance(nodeValue.elt, BinOp):
            try:
                elements = [eval("'%s' %s '%s'" % (self.getAssignedTxt(nodeValue.elt.left), nodeValue.elt.op, x)) for x in ast.literal_eval(targets)]
            except Exception, e:
                self.logError("getListCompValueEval2Error", nodeValue, e)
        else:
            elements = [self.getAssignedTxt(nodeValue.elt)]
        lvalue = ifElse(str(elements), str(elements), str(targets))
        return lvalue

    def getAssignedTxt(self, nodeValue):
        if type(nodeValue) in (type(None), int, str, float, list, dict):
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
            elif isinstance(nodeValue, Subscript):
                qvalue = self.getSubscriptValue(nodeValue)
            elif isinstance(nodeValue, Class):
                qvalue = self.getClassAttr(nodeValue, attrSeek=None)
            elif isinstance(nodeValue, List):
                qvalue = self.getListValue(nodeValue)
            elif isinstance(nodeValue, ListComp):
                qvalue = self.getListCompValue(nodeValue)
            elif isinstance(nodeValue, Dict):
                qvalue = self.getDictValue(nodeValue)
            else:
                inferedValue = nodeValue.infered()
                if isinstance(inferedValue, Iterable) and nodeValue != inferedValue[0]:
                    if not inferedValue[0] is YES:
                        qvalue = self.getAssignedTxt(inferedValue[0])
                else:
                    self.add_message("W6602", line=nodeValue.fromlineno, node=nodeValue.scope(), args=nodeValue)
                    raise InferenceError
        except InferenceError, e:
            self.logError("getAssignedTxtInferenceError", nodeValue, e)
        except Exception, e:
            self.logError("getAssignedTxtError", nodeValue, e)
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
        except InferenceError, e: # pragma: no cover
            self.logError("setUpQueryTxtInferenceError", nodeTarget, e)

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

    def searchNode(self, node, searchName="", _done=None):
        """ creates the main Func dictionary for the CallFunc's Getattr of 'searchName' in 'node' """

        if _done is None: _done = set()
        if node in _done: return
        if not hasattr(node, '_astroid_fields'): return
        _done.add(node)

        def match():
            if isinstance(node, CallFunc) and isinstance(node.func, Getattr):
                if node.func.attrname == searchName:
                    self.setFuncParams(node)
                    return True
            return False

        for field in node._astroid_fields:
            value = getattr(node, field)
            if isinstance(value, (list, tuple)):
                for child in value:
                    if isinstance(child, (list, tuple)):
                        self.searchNode(child[0], searchName, _done)
                        self.searchNode(child[1], searchName, _done)
                    else:
                        if match(): break
                        self.searchNode(child, searchName, _done)
            else:
                if match(): break
                self.searchNode(value, searchName, _done)

    def logError(self, msg, node, e=""):
        nodeString = ""
        if hasattr(node, "as_string"): nodeString = node.as_string()
        logHere(msg, e, node.lineno, nodeString, filename="%s.log" % self.getNodeFileName(node))

    ####### pylint's redefinitions #######

    def visit_assign(self, node):
        if not queryEnabled(): return
        if self.isSqlAssAttr(node.targets[0]):
            qvalue = self.getAssignedTxt(node.value)
            self.setUpQueryTxt(node.targets[0], qvalue, isnew=True)

    def visit_augassign(self, node):
        if not queryEnabled(): return
        if self.isSqlAssAttr(node.target):
            qvalue = self.getAssignedTxt(node.value)
            self.setUpQueryTxt(node.target, qvalue)

    @check_messages('query-syntax-error', 'query-inference')
    def visit_callfunc(self, node):
        if not queryEnabled(): return
        if isinstance(node.func, Getattr) and node.func.attrname in ("open", "execute"):
            try:
                inferedNode = node.infered()
            except InferenceError, e: # pragma: no cover
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
