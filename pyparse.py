import ast

def parseScript(filefullpath):
    f = file(filefullpath,"r")
    nodes = ast.parse(f.read())
    PyParse().visit(nodes)
    f.close()

class PyParse(ast.NodeVisitor):

    def generic_visit(self, node):
        #print type(node).__name__
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Module(self, node):
        self.names = set()
        self.generic_visit(node)
        print sorted(self.names)

    def visit_Name(self, node):
        self.names.add(node.id)
        #print "name level", node.id

    def visit_ClassDef(self, node):
        print "class level", node.name
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        print "function level", node.name

if __name__ == "__main__":
    filepath = "e:/Develop/desarrollo/python/ancho/workspace/Playero/standard/records/Invoice.py"
    parseScript(filepath)
