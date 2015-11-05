# pylint:disable=W0703,R0912

from pylint.checkers import BaseChecker
from astroid.node_classes import Getattr, AssAttr, Const, \
                                    If, BinOp, CallFunc, Name, Tuple, \
                                    Return, Assign, AugAssign, AssName, \
                                    Keyword, Compare, Subscript, For, \
                                    Dict, List, Slice, Comprehension, \
                                    Discard, Index, UnaryOp, BoolOp
from astroid.scoped_nodes import Function, Class, ListComp, Lambda
from astroid.bases import YES, Instance
from astroid.exceptions import InferenceError
from pylint.interfaces import IAstroidChecker
from pylint.checkers.utils import check_messages
from libs.tools import logHere, filenameFromPath, escapeAnyToString, isNumber
from libs.sqlparse import validateSQL
from libs.cache import cache
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

    def open(self):
        self.queryTxt = {}  # instanceName : parsedSQLtext
        self.funcParams = {}  # functionName : argumentIndex : argumentValue
        self.ifProcessed = set()

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
            QueryChecker.logError("setFuncParams", node, e)

    def getFuncParams(self, node, forceSearch=True):
        fparam = ""
        nodescope = node.scope()
        try:
            if isinstance(nodescope, Function) and hasattr(node, "name") and node.name in nodescope.argnames():
                funcname = nodescope.name
                if funcname in self.funcParams:
                    fparam = self.get_func_params_by_name_or_index(node)
                elif forceSearch: #funcname wasn't created
                    self.searchNode(nodescope.root(), funcname)
                    fparam = self.getFuncParams(node, forceSearch=False) #forceSearch=False to prevent infinite loop
        except Exception, e:
            QueryChecker.logError("getFuncParamsError", node, e)
        return fparam

    def get_func_params_by_name_or_index(self, node):
        fparam = ""
        fp = self.funcParams[node.scope().name]
        funcargs = [x for x in node.scope().args.args if x.name not in ("self", "classobj", "cls")]
        for idx, funcarg in enumerate(funcargs):
            if node.name == funcarg.name:
                fparam = fp.get(funcarg.name, fp.get(idx, "")) #get by name and then, by index
        return fparam

    def concatOrReplace(self, node, nodeName, previousValue, newValue):
        res = previousValue
        try:
            newVal = self.getAssignedTxt(newValue)
            if isinstance(node, AugAssign):
                res = QueryChecker.concat_aug_assign(node, nodeName, previousValue, newVal)
            elif isinstance(node, Assign):
                res = QueryChecker.concat_assign(node, nodeName, previousValue, newVal)
            elif isinstance(node, If):
                res = self.concat_if_for(node, nodeName, previousValue, newVal)
            elif isinstance(node, For) and isinstance(node.target, AssName) and nodeName == node.target.name:
                res = newVal
            elif isinstance(node, For):
                res = self.concat_if_for(node, nodeName, previousValue, newValue)
            elif isinstance(node, Discard) and isinstance(node.value, CallFunc):
                res = QueryChecker.concat_discard(node.value, nodeName, previousValue, newVal)
        except Exception, e:
            QueryChecker.logError("concatOrReplaceError", node, e)
        return res

    @staticmethod
    def concat_aug_assign(node, node_name, prev_value, new_value):
        res = prev_value
        if isinstance(node, AugAssign) and isinstance(node.target, AssName) and node_name == node.target.name:
            res = "%s%s" % (prev_value, new_value)
        return res

    @staticmethod
    def concat_assign(node, node_name, prev_value, new_value):
        res = prev_value
        if isinstance(node.targets[0], AssName) and node_name == node.targets[0].name:
            res = new_value
            if not isNumber(new_value) and isNumber(prev_value):
                res = prev_value
        return res

    def concat_if_for(self, node, node_name, prev_value, new_value):
        res = prev_value
        for atr in "body", "orelse":
            for elm in getattr(node, atr):
                if (res == new_value) or (prev_value and atr == "orelse"):
                    continue
                res = self.concatOrReplace(elm, node_name, res, new_value)
        return res

    @staticmethod
    def concat_discard(node_value, node_name, prev_value, new_value):
        res = prev_value
        if hasattr(node_value.func, "expr") and isinstance(node_value.func.expr, Name) and node_name == node_value.func.expr.name:
            res = new_value
        return res

    def search_assname_body(self, body_or_else, node_value, node_name, to_line_number):
        bvalue, bfound = None, None
        getBVal = lambda x: "" if x is None else x
        for elm, atr in [(elm, atr) for atr in body_or_else for elm in getattr(node_value, atr) if elm.lineno < to_line_number]:
            if not (bvalue and atr == "orelse"): #no need to search in 'orelse' if the 'body' returns a value
                (assValue, afound) = self.getAssNameValue(elm, nodeName=node_name, tolineno=to_line_number)
                if afound and assValue != bvalue:
                    bvalue = self.concatOrReplace(elm, node_name, getBVal(bvalue), assValue)
                    bfound = elm
        return getBVal(bvalue), bfound

    @cache.store
    def getAssNameValue(self, nodeValue, nodeName="", tolineno=999999):
        if not tolineno: tolineno = 999999
        anvalue = ""
        anfound = None
        if nodeValue.lineno > tolineno: return anvalue, anfound
        if isinstance(nodeValue, Assign):
            anvalue, anfound = self.get_assname_target_value(nodeValue.targets[0], nodeValue.value, nodeName)
        elif isinstance(nodeValue, AugAssign):
            anvalue, anfound = self.get_assname_target_value(nodeValue.target, nodeValue.value, nodeName)
        elif isinstance(nodeValue, For):
            anvalue, anfound = self.get_assname_for_value(nodeValue, nodeName, tolineno)
        elif isinstance(nodeValue, If):
            lookBody = "body" if self.doCompareValue(nodeValue) else "orelse"
            anvalue, anfound = self.search_assname_body([lookBody], nodeValue, nodeName, tolineno)
        elif isinstance(nodeValue, Discard) and isinstance(nodeValue.value, CallFunc):
            anvalue, anfound = self.get_assname_func_value(nodeValue, nodeName)
        return anvalue, anfound

    def get_assname_target_value(self, target_node, target_value, node_name):
        anvalue = ""
        anfound = None
        if node_name and isinstance(target_node, AssName) and node_name == target_node.name:
            anvalue = self.getAssignedTxt(target_value)
            anfound = target_node.parent
        return anvalue, anfound

    def get_assname_for_value(self, node_value, node_name, to_line_number):
        anvalue, anfound = self.get_assname_target_value(node_value.target, node_value.iter, node_name)
        if not anvalue.startswith("["): anvalue = "['%s']" % anvalue
        elif anvalue == "[]": anvalue = "['666']"
        try:
            anvalue = ast.literal_eval(anvalue)[0]
        except Exception, e:
            QueryChecker.logError("get_assname_for_value literal_eval", node_value, e)
        if not anfound:
            anvalue, anfound = self.search_assname_body(["body", "orelse"], node_value, node_name, to_line_number)
        return anvalue, anfound

    def get_assname_func_value(self, node_value, node_name):
        anvalue = ""
        anfound = None
        nvf = node_value.value.func
        if isinstance(nvf, Getattr) and isinstance(nvf.expr, Name) and node_name == nvf.expr.name:
            anvalue = self.getCallFuncValue(node_value.value)
            anfound = node_value
        return anvalue, anfound

    def doCompareValue(self, nodeValue):
        evalResult = True
        evaluation = "True"
        if isinstance(nodeValue.test, Compare):
            leftval = self.getAssignedTxt(nodeValue.test.left)
            op = nodeValue.test.ops[0] #a list with 1 tuple
            rightval = self.getAssignedTxt(op[1])
            if op[0] != "in": rightval = '"""%s"""' % rightval
            elif not rightval: rightval = "[0, 0]"
            evaluation = '"""%s""" %s %s' % (leftval, op[0], rightval)
        elif isinstance(nodeValue.test, UnaryOp):
            evaluation = self.getUnaryOpValue(nodeValue.test)
        elif isinstance(nodeValue.test, BoolOp):
            evaluation = self.getBoolOpValue(nodeValue.test)
        elif isinstance(nodeValue.test, Const):
            evaluation = '%s' % self.getAssignedTxt(nodeValue.test)
        if evaluation:
            try:
                evalResult = eval("%s" % str(evaluation), nodeValue.root().globals, nodeValue.root().locals)
            except Exception, e:
                evalResult = False
                QueryChecker.logError("EvaluationError doCompareValue %s" % evaluation, nodeValue, e)
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
                    nvalue = self.concatOrReplace(assFound, nodeValue.name, nvalue, assValue)
                    tryinference = False
            if not nvalue and tryinference:
                nvalue = self.get_name_value_inference(nodeValue)
        except Exception, e:
            QueryChecker.logError("getNameValueError", nodeValue, e)
        return nvalue

    def get_name_value_inference(self, node_value):
        nvalue = ""
        try:
            for inferedValue in [ival for ival in node_value.infered() if ival is not YES]:
                nvalue = self.getAssignedTxt(inferedValue)
                if nvalue: break
        except InferenceError: # pragma: no cover
            pass
        return nvalue

    def getFunctionReturnValue(self, funcNode):
        retVal = ""
        for retNode in [x for x in funcNode.nodes_of_class(Return)]:
            if isinstance(retNode.parent, If) and not self.doCompareValue(retNode.parent):
                continue #if is an If and the result of the comparition is false, try next Return
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
        except (InferenceError, TypeError):
            pass #cannot be infered | cannot be itered. _Yes object?
        if not cfvalue:
            if isinstance(nodefn, Name):
                cfvalue = self.get_callfunc_name_value(nodeValue)
            elif isinstance(nodefn, Getattr):
                cfvalue = self.get_callfunc_getattr_value(nodeValue)
        return cfvalue

    def get_callfunc_name_value(self, node_value):
        cfvalue = ""
        funcname = node_value.func.name
        if funcname == "date":
            cfvalue = "2000-01-01"
        elif funcname == "time":
            cfvalue = "00:00:00"
        elif funcname == "len":
            cfvalue = len(self.getAssignedTxt(node_value.args[0]))
        elif funcname in ("map", "filter"):
            mapto = node_value.args[0]
            target = self.getAssignedTxt(node_value.args[1])
            if target in ("", "0"): target = "['0','0']"
            evaluation = "%s(%s, %s)" % (funcname, mapto.as_string(), target)
            try:
                cfvalue = str(eval(evaluation, node_value.root().globals, node_value.scope().locals))
            except Exception, e:
                QueryChecker.logError("get_callfunc_name_value MapEvalError", node_value, e)
        else: #method may be locally defined
            cfvalue = self.getCallUserDefinedName(node_value)
        return cfvalue

    def get_callfunc_getattr_value(self, node_value):
        cfvalue = ""
        attrname = node_value.func.attrname
        if attrname == "name" and isinstance(node_value.func.expr, Name) and isinstance(node_value.scope().parent, Class):
            cfvalue = node_value.scope().parent.name
        elif attrname == "keys":
            cfvalue = "['0','0']"
        elif attrname == "join":
            cfvalue = self.get_callfunc_getattr_value_from_join(node_value)
        elif attrname in ("append", "extend"):
            cfvalue = self.getAssignedTxt(node_value.args[0])
        elif attrname == "split":
            cfvalue = self.get_callfunc_getattr_value_from_split(node_value)
        elif attrname == "replace":
            cfvalue = self.get_callfunc_getattr_value_from_replace(node_value)
        elif attrname == "date":
            cfvalue = "2000-01-01"
        else:
            cfvalue = self.getCallGetattr(node_value)
        return cfvalue

    def get_callfunc_getattr_value_from_join(self, node):
        cfvalue = ""
        expr = self.getAssignedTxt(node.func.expr)
        args = self.getAssignedTxt(node.args[0])
        if args:
            if not args.startswith(("[", "'")):
                args = "'%s'" % args
            cfvalue = "%s" % expr.join(["%s" % x for x in ast.literal_eval(args)])
            if not cfvalue:
                cfvalue = "%s" % expr.join(['666'])
        return cfvalue

    def get_callfunc_getattr_value_from_split(self, node):
        expr = self.getAssignedTxt(node.func.expr)
        args = self.getAssignedTxt(node.args[0])
        return "[%s]" % args.join(["'%s'" % str(x) for x in expr.split(args)])

    def get_callfunc_getattr_value_from_replace(self, node):
        arg1 = self.getAssignedTxt(node.args[0])
        arg2 = self.getAssignedTxt(node.args[1])
        return self.getNameValue(node.func.expr).replace(arg1, arg2)

    def getCallGetattr(self, node):
        cgattr = ""
        nodefn = node.func
        attrname = nodefn.attrname
        prevSi = node.previous_sibling()
        while prevSi is not None:
            if QueryChecker.sibling_is_valid(node, prevSi):
                cgattr = self.getFunctionReturnValue(prevSi.value.infered()[0].locals[attrname][0])
                break
            prevSi = prevSi.previous_sibling()
        return cgattr

    @staticmethod
    def sibling_is_valid(node, sibling):
        return QueryChecker.is_valid_getattr_name(node) and QueryChecker.is_valid_assign(node, sibling) and QueryChecker.is_valid_instance(node, sibling)

    @staticmethod
    def is_valid_getattr_name(node):
        return isinstance(node.func.expr, Getattr) and isinstance(node.func.expr.expr, Name) and node.func.expr.expr.name == "self"

    @staticmethod
    def is_valid_assign(node, sibling):
        res = False
        if isinstance(sibling, Assign) and isinstance(sibling.targets[0], AssAttr):
            target = sibling.targets[0]
            res = target.expr.name == "self" and target.attrname == node.func.expr.attrname
        return res

    @staticmethod
    def is_valid_instance(node, sibling):
        res = False
        if isinstance(sibling.value, CallFunc):
            infered = sibling.value.infered()[0]
            res = isinstance(infered, Instance) and node.func.attrname in infered.locals
        return res

    def getCallUserDefinedName(self, node):
        cudnvalue = ""
        nodefn = node.func
        funcname = nodefn.name
        nodeScope = node.scope()
        if funcname not in nodeScope.locals: return cudnvalue
        methodParent = nodeScope.locals[funcname][0].parent
        if QueryChecker.is_parent_getattr_named_self(methodParent):
            args = methodParent.value.args[1]
            methodname = self.getAssignedTxt(args).strip() #the for must be analysed here
            if methodname in nodeScope.parent.locals:
                realmethod = nodeScope.parent.locals[methodname][0]
                cudnvalue = self.getFunctionReturnValue(realmethod)
            else:
                #backwards name locator
                cudnvalue = self.get_call_user_defined_name_backward_locator(node, args)
        return cudnvalue

    @staticmethod
    def is_parent_getattr_named_self(node):
        res = False
        if isinstance(node, Assign) and isinstance(node.value, CallFunc) and isinstance(node.value.func, Name) and node.value.func.name == "getattr":
            args = node.value.args[0]
            if isinstance(args, Name) and args.name == "self":
                res = True
        return res

    def get_call_user_defined_name_backward_locator(self, node, args):
        cudnvalue = ""
        sname, forText1 = QueryChecker.backward_locator_name_finder(args)
        assignText1 = ""
        prevSi = node.previous_sibling() or node.parent
        while node.scope() == prevSi.scope(): #cannot go beyond this
            if isinstance(prevSi, Assign) and isinstance(prevSi.targets[0], AssName) and prevSi.targets[0].name == sname.name:
                sname, assignText1 = QueryChecker.backward_locator_assing_finder(prevSi)
            elif isinstance(prevSi, For) and isinstance(prevSi.target, AssName) and prevSi.target.name == sname.name:
                cudnvalue = self.backward_locator_for_finder(node, prevSi, forText1, assignText1)
            prevSi = prevSi.previous_sibling() or prevSi.parent
        return cudnvalue

    @staticmethod
    def backward_locator_name_finder(args):
        sname = [child for child in args.get_children() if isinstance(child, Name)][0]
        forText1 = args.as_string().replace(sname.name, '"""forText"""')
        return sname, forText1

    @staticmethod
    def backward_locator_assing_finder(sibling):
        sname = [child for child in sibling.value.get_children() if isinstance(child, Name)][0]
        return sname, sibling.value.as_string().replace(sname.name, '"""assignText1"""')

    def backward_locator_for_finder(self, node, sibling, for_text1, assign_text1):
        cudnvalue = ""
        from playero_transforms.classes import buildStringModule
        value = self.getAssignedTxt(sibling.iter)
        for methodname in ast.literal_eval(value):
            assignText2 = assign_text1.replace("assignText1", methodname)
            newnode = buildStringModule(assignText2)
            assignText2 = self.getAssignedTxt(newnode.body[0].value)
            forText2 = for_text1.replace("forText", assignText2)
            newnode = buildStringModule(forText2)
            methodname = self.getAssignedTxt(newnode.body[0].value).strip()
            if methodname in node.scope().parent.locals:
                realmethod = node.scope().parent.locals[methodname][0]
                cudnvalue = self.getFunctionReturnValue(realmethod)
                break
        return cudnvalue

    def getBinOpValue(self, nodeValue):
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
            try:
                qvalue = eval(toeval, nodeValue.root().globals, nodeValue.scope().locals)
                qvalue = qvalue.replace("NEWLINE", "\n")
            except Exception, e:
                QueryChecker.logError("getBinOpValueError", nodeValue, e)
        else:
            qvalue += self.getAssignedTxt(nodeValue.right)
        return qvalue

    def getTupleValues(self, nodeValue):
        tvalues = []
        try:
            for elts in nodeValue.itered():
                tvalues.append(self.getAssignedTxt(elts))
        except Exception, e:
            QueryChecker.logError("getTupleValuesError", nodeValue, e)
        return '("""%s""")' % '""","""'.join(tvalues)

    def getHeirValue(self, node):
        """locate attribute in inheritance by visiting all assignments"""
        heirVal = ""
        prevSi = node.previous_sibling()
        if QueryChecker.is_heir_getattr_valid_assign(prevSi, node.expr.name) and QueryChecker.is_heir_getattr_valid_callfunc(prevSi) and QueryChecker.is_attr_in_locals(node, prevSi):
            heirVal = self.build_inheritance(node, prevSi)
        return heirVal

    @staticmethod
    def is_heir_getattr_valid_assign(node, node_expr_name):
        res = False
        if isinstance(node, Assign) and isinstance(node.targets[0], AssName) and node.targets[0].name == node_expr_name:
            res = True
        return res

    @staticmethod
    def is_heir_getattr_valid_callfunc(node):
        res = False
        if isinstance(node.value, CallFunc) and isinstance(node.value.func, Getattr) and node.value.func.expr.name == "self":
            res = True
        return res

    @staticmethod
    def is_attr_in_locals(node, sibling):
        return sibling.value.func.attrname not in node.scope().parent.locals #the function called is not present

    def build_inheritance(self, node, sibling):
        heirVal = ""
        heirClass = node.scope().parent.bases[0].infered()[0]
        heirCall = heirClass.locals[sibling.value.func.attrname][0]
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
            if isinstance(inferedValue, Instance) and isinstance(inferedValue.infered()[0], Class):
                if inferedValue.pytype() == "Query.Query":
                    res = self.queryTxt.get(nodeValue.expr.name, self.getHeirValue(nodeValue))
                if not res:
                    res = self.getClassAttr(inferedValue.infered()[0], nodeValue.attrname)
            elif isinstance(nodeValue.expr, Subscript):
                res = self.getSubscriptValue(nodeValue.expr)
        except InferenceError:
            pass #missing parameters?
        except Exception, e:
            QueryChecker.logError("getGetattrValueError", nodeValue, e)
        return [nodeValue.attrname, res][bool(res)]

    def getClassAttr(self, nodeValue, attrSeek=None):
        cvalue = ""
        try:
            for ofuncs in nodeValue.get_children():
                if isinstance(ofuncs, Assign) and isinstance(ofuncs.targets[0], AssName) and ofuncs.targets[0].name == attrSeek:
                    cvalue = self.getAssignedTxt(ofuncs.value)
                elif isinstance(ofuncs, Function):
                    cvalue = self.get_class_attr_function(nodeValue, ofuncs, attrSeek)
                if cvalue: break
            if not cvalue and "bring" in nodeValue.locals:
                cvalue = self.getClassAttr(nodeValue.locals["bring"][0], attrSeek)
        except Exception, e:
            QueryChecker.logError("getClassAttrError", nodeValue, e)
        return cvalue

    def get_class_attr_function(self, node, ofuncs, attr_seek):
        cvalue = ""
        for attr in [atr for atr in node[ofuncs.name].body if isinstance(atr, Assign)]:
            if isinstance(attr.targets[0], AssAttr) and (attr.targets[0].attrname == attr_seek or attr_seek is None):
                cvalue = self.getAssignedTxt(attr.value)
                if cvalue: break
        return cvalue

    def getSubscriptValue(self, nodeValue):
        svalue = ""
        if isinstance(nodeValue.parent, Getattr) and nodeValue.parent.attrname == "sql" and isinstance(nodeValue.value, Name):
            svalue = self.queryTxt.get(nodeValue.value.name, "")
        else:
            nvalue = self.get_subscript_left_value(nodeValue)
            idx = self.get_subscript_index_value(nodeValue)
            if len(nvalue) > 2:
                evaluation = '%s[%s]' % (nvalue, idx)
                if nvalue.startswith("{"):
                    evaluation = '%s.get("%s", None)' % (nvalue, idx)
                try:
                    svalue = eval(evaluation, nodeValue.root().globals, nodeValue.scope().locals)
                except IndexError:
                    svalue = eval('%s[0]' % nvalue)
                except Exception, e:
                    QueryChecker.logError("getSubscriptValueError", nodeValue, e)
        return svalue

    def get_subscript_left_value(self, node):
        nvalue = ""
        if isinstance(node.value, Name):
            if node.value.name in node.parent.scope().keys():
                nvalue = self.getNameValue(node.value)
        elif isinstance(node.value, List):
            nvalue = self.getListValue(node.value)
        elif isinstance(node.value, Const):
            nvalue = self.getAssignedTxt(node.value)
        if not nvalue.startswith(("[", "'", "{")):
            nvalue = "'%s'" % nvalue
        return nvalue

    def get_subscript_index_value(self, node):
        idx = "0"
        if isinstance(node.slice, Slice):
            low = self.getAssignedTxt(node.slice.lower)
            up = self.getAssignedTxt(node.slice.upper)
            if not low or low == "None":
                low = 0
            if not up or up == "None":
                up = ""
            idx = "%s:%s" % (low, up)
        elif isinstance(node.slice, Index):
            idx = self.getAssignedTxt(node.slice.value) or "0"
        return idx

    def getListValue(self, nodeValue):
        return "['%s']" % "','".join([self.getAssignedTxt(x) for x in nodeValue.elts])

    def getDictValue(self, nodeValue):
        tupleDictator = lambda (x, y): "'%s':'%s'" % (self.getAssignedTxt(x), self.getAssignedTxt(y))
        return '{%s}' % ",".join(map(tupleDictator, nodeValue.items))

    def getListCompValue(self, nodeValue):
        targets = []
        doEval = lambda x: eval(x, nodeValue.root().globals, nodeValue.scope().locals)
        fgen = nodeValue.generators[0]
        if isinstance(fgen, Comprehension):
            if isinstance(fgen.iter, CallFunc):
                evaluation = "'%s'.%s('%s')" % (self.getAssignedTxt(fgen.iter.func.expr), fgen.iter.func.attrname, self.getAssignedTxt(fgen.iter.args[0]))
                try:
                    targets = doEval(evaluation)
                except Exception, e:
                    QueryChecker.logError("getListCompValueError", nodeValue, e)
            elif isinstance(fgen.iter, Name):
                targets = self.getNameValue(fgen.iter)
            else:
                targets = ast.literal_eval(self.getAssignedTxt(fgen.iter))
        elements = []
        if isinstance(nodeValue.elt, CallFunc):
            if isinstance(nodeValue.elt.func, Getattr):
                try:
                    elements = [doEval("'%s'.%s()" % (x, nodeValue.elt.func.attrname)) for x in targets]
                except Exception, e:
                    QueryChecker.logError("getListCompValueEval1Error", nodeValue, e)
        elif isinstance(nodeValue.elt, BinOp):
            try:
                elements = [doEval("'%s' %s '%s'" % (self.getAssignedTxt(nodeValue.elt.left), nodeValue.elt.op, x)) for x in ast.literal_eval(targets)]
            except Exception, e:
                QueryChecker.logError("getListCompValueEval2Error", nodeValue, e)
        else:
            elements = [self.getAssignedTxt(nodeValue.elt)]
        lvalue = str(elements) or str(targets)
        return lvalue

    def getLambdaValue(self, nodeValue):
        lvalue = ""
        if isinstance(nodeValue.parent, CallFunc):
            lambdaArgs = nodeValue.parent.args[1]
            args = self.getAssignedTxt(lambdaArgs)
            if args:
                ite = None
                try:
                    ite = eval(args, nodeValue.root().globals, nodeValue.scope().locals)
                except Exception:
                    pass
                if isinstance(ite, Iterable):
                    lvalue = ite
        return lvalue

    def getUnaryOpValue(self, nodeValue):
        uvalue = "True"
        if not isinstance(nodeValue.operand, UnaryOp):
            uvalue = '"""%s"""' % self.getAssignedTxt(nodeValue.operand)
        return uvalue

    def getBoolOpValue(self, nodeValue):
        bvalue = []
        for val in nodeValue.values:
            if isinstance(val, UnaryOp):
                bvalue.append(self.getUnaryOpValue(val))
            elif isinstance(val, Compare):
                bvalue.append(self.getCompareValue(val))
            else:
                bvalue.append(self.getAssignedTxt(val))
        return str(any(bvalue))

    def getCompareValue(self, nodeValue):
        cvalue = []
        cvalue.append(self.getAssignedTxt(nodeValue.left))
        cvalue.extend([self.getAssignedTxt(v) for v in nodeValue.ops])
        return str(any(cvalue))

    def getAssignedTxt(self, nodeValue):
        if type(nodeValue) in (type(None), int, str, float, list, dict, tuple):
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
            elif isinstance(nodeValue, Lambda):
                qvalue = self.getLambdaValue(nodeValue)
            elif isinstance(nodeValue, BoolOp):
                qvalue = self.getBoolOpValue(nodeValue)
            elif isinstance(nodeValue, Compare):
                qvalue = self.getCompareValue(nodeValue)
                """elif isinstance(nodeValue, UnaryOp):
                    qvalue = self.getUnaryOpValue(nodeValue)"""
            else:
                qvalue = self.get_assigned_text_by_inference(nodeValue)
        except Exception, e:
            QueryChecker.logError("getAssignedTxtError", nodeValue, e)
        return qvalue

    def get_assigned_text_by_inference(self, node):
        qvalue = ""
        try:
            inferedValue = node.infered()
            if isinstance(inferedValue, Iterable) and inferedValue[0] not in (node, YES):
                qvalue = self.getAssignedTxt(inferedValue[0])
            else:
                self.add_message("W6602", line=node.fromlineno, node=node.scope(), args=node)
                raise InferenceError
        except InferenceError, e:
            QueryChecker.logError("getAssignedTxtInferenceError", node, e)
        return qvalue

    def setUpQueryTxt(self, nodeTarget, value, isnew=False):
        try:
            instanceName = None
            inferedValue = nodeTarget.expr.infered()[0]
            if inferedValue is YES and QueryChecker.is_sql_attr_and_name_subscript(nodeTarget):
                instanceName = nodeTarget.expr.value.name
            if inferedValue.pytype() == "Query.Query" or instanceName:
                nodeGrandParent = nodeTarget.parent.parent #First parent is Assign or AugAssign
                instanceName = instanceName or nodeTarget.expr.name
                if not isinstance(nodeGrandParent, If):
                    self.appendQuery(instanceName, value, isnew)
                else:
                    self.preprocessQueryIfs(nodeTarget, instanceName, value, isnew)
        except InferenceError, e: # pragma: no cover
            QueryChecker.logError("setUpQueryTxtInferenceError", nodeTarget, e)

    @staticmethod
    def is_sql_attr_and_name_subscript(node):
        return isinstance(node, AssAttr) and isinstance(node.expr, Subscript) and isinstance(node.expr.value, Name) and node.attrname == "sql"

    def appendQuery(self, instanceName, value, isnew):
        if isnew or instanceName not in self.queryTxt:
            self.queryTxt[instanceName] = ""
        self.queryTxt[instanceName] += str(value)

    def preprocessQueryIfs(self, nodeTarget, instanceName, value, isnew):
        nodeGrandParent = nodeTarget.parent.parent
        if nodeTarget.parent not in nodeGrandParent.orelse: #Only first part of If...
            if not isinstance(nodeGrandParent.parent, If): #ElIf will not be included
                if self.doCompareValue(nodeGrandParent):
                    self.appendQuery(instanceName, value, isnew)
                    self.ifProcessed.add(nodeGrandParent.lineno)
            else:
                self.ifProcessed.add(nodeGrandParent.lineno)
                self.preprocessQueryIfs(nodeTarget.parent, instanceName, value, isnew)
        else: #Else included if his parent was not processed
            if nodeGrandParent.lineno not in self.ifProcessed:
                self.appendQuery(instanceName, value, isnew)

    @staticmethod
    def is_sql_assattr(node):
        return isinstance(node, AssAttr) and node.attrname == "sql"

    @staticmethod
    def is_open_or_execute_getattr(node):
        return isinstance(node.func, Getattr) and node.func.attrname in ("open", "execute")

    @staticmethod
    def get_node_filename(node):
        parsedFileName = "notFound"
        if hasattr(node, "root") and hasattr(node.root(), "file") and node.root().file:
            parsedFileName = filenameFromPath(node.root().file)
        return parsedFileName

    def searchNode(self, node, searchName="", _done=None):
        """ creates the main Func dictionary for the CallFunc's Getattr of 'searchName' in 'node' """

        _done = _done or set()
        if not hasattr(node, '_astroid_fields') or node in _done: return
        _done.add(node)

        for field in node._astroid_fields:
            value = getattr(node, field)
            if isinstance(value, (list, tuple)):
                self.search_node_in_childs(node, value, searchName, _done)
            elif self.match_and_set_funcs(node, searchName): break
            self.searchNode(value, searchName, _done)

    def search_node_in_childs(self, node, value, searchName, _done):
        for child in value:
            if isinstance(child, (list, tuple)):
                self.searchNode(child[0], searchName, _done)
                self.searchNode(child[1], searchName, _done)
            elif self.match_and_set_funcs(node, searchName): break
            self.searchNode(child, searchName, _done)

    def match_and_set_funcs(self, node, search_name):
        if isinstance(node, CallFunc) and isinstance(node.func, Getattr) and node.func.attrname == search_name:
            self.setFuncParams(node)
            return True
        return False

    @staticmethod
    def logError(msg, node, e=""):
        nodeString = ""
        if hasattr(node, "as_string"): nodeString = node.as_string()
        logHere(msg, e, node.lineno, nodeString, filename="%s.log" % QueryChecker.get_node_filename(node))

    ####### pylint's redefinitions #######

    def visit_assign(self, node):
        if not queryEnabled(): return
        if QueryChecker.is_sql_assattr(node.targets[0]):
            qvalue = self.getAssignedTxt(node.value)
            self.setUpQueryTxt(node.targets[0], qvalue, isnew=True)

    def visit_augassign(self, node):
        if not queryEnabled(): return
        if QueryChecker.is_sql_assattr(node.target):
            qvalue = self.getAssignedTxt(node.value)
            self.setUpQueryTxt(node.target, qvalue)

    @check_messages('query-syntax-error', 'query-inference')
    def visit_callfunc(self, node):
        if not (queryEnabled() and QueryChecker.is_open_or_execute_getattr(node)):
            return
        try:
            inferedNode = node.infered()
        except InferenceError: # pragma: no cover
            return
        for name in QueryChecker.get_query_expr_names(node, inferedNode):
            if name in self.queryTxt:
                res = validateSQL(self.queryTxt[name], filename="%sQUERY.log" % filenameFromPath(node.root().file))
                if res:
                    self.add_message("E6601", line=node.lineno, node=node, args="%s: %s" % (name, res))
            else:
                self.add_message("W6602", line=node.lineno, node=node, args=name)

    @staticmethod
    def get_query_expr_names(node, infered_node):
        for x in infered_node:
            xrootvalues = x.root().values()
            if xrootvalues is YES:
                continue
            try:
                main = xrootvalues[0].frame()
                if main.name == "Query":
                    yield node.func.expr.name
            except TypeError, e:
                logHere("TypeError visit_callfunc", e, filename="%s.log" % filenameFromPath(node.root().file))
