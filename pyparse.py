import ast
import os

def parseScript(filefullpath):
    f = open(filefullpath, "r")
    lines = f.read().splitlines() #best handling for CR LF and LF
    fixed = "\n".join([line.rstrip() for line in lines]) #force \n for each line
    nodes = ast.parse(fixed)
    f.close()
    parse = PyParse()
    parse.visit(nodes)
    return parse

class PyParse(ast.NodeVisitor):

    def __init__(self):
        ast.NodeVisitor.__init__(self)
        self.attributes = set()
        self.methods = set()
        self.classes = set()
        self.names = set()

    def generic_visit(self, node):
        #print type(node).__name__
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Module(self, node):
        self.generic_visit(node)

    def visit_Name(self, node):
        self.names.add(node.id)
        #print "name level", node.id
        if node.id == "SuperClass":
            self.generic_visit(node)

    def visit_ClassDef(self, node):
        #print "class level", node.name
        self.classes.add(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.methods.add(node.name)
        #print "function level", node.name

    def visit_Assign(self, node):
        self.attributes.add(node.targets[0].id)
        self.generic_visit(node)
        #print "assign level", node.targets[0].id

    """def visit_Str(self, node):
        print "str", node.s

    def visit_Call(self, node):
        for key, value in ast.iter_fields(node):
            if key == 'func':
                print "call FUNCTION", key, "b",    value
                self.visit(value)
            elif value:
                print "call value subnodevisit", value
                self.subnodeVisit(value)

    def subnodeVisit(self, node):
        if isinstance(node, list):
            print "list"
            for item in node:
                print item, "subnodeVisit"
                self.subnodeVisit(item)
        elif isinstance(node, ast.AST):
            self.visit(node)"""


if __name__ == "__main__":
    filepath = "e:/Develop/desarrollo/python/ancho/workspace/Playero/standard/records/Invoice.py"
    if (os.name == "posix"):
        filepath = "/home/ancho/Develop/Playero/standard/records/Invoice.py"
    par = parseScript(filepath)
    print "---attributes---"
    for a in par.attributes:
        print a
    print "---methods---"
    for b in par.methods:
        print b
