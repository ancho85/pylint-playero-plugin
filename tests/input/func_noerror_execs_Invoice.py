# pylint:disable=C6666,R0201,W0122

def doWorld():
    return "World!"

class helloWorld(object):
    exec("res = 'hello'")
    exec("res2 = doWorld()")
    print res, res2

    exec("from %s import Field as MyField" % "Field")
    f = MyField()

    test = True
    exec("res3 = %s" % test)
    print res3
