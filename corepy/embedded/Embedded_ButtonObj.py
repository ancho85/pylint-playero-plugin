import os
class Embedded_ButtonObj(object):

    def __init__(self, label, color, image, xb, yb, xe, ye, data):
        pass

    def getAbsolutePos(self):
        return (0, 0)

    def getRelativePos(self):
        return (0, 0)

    def clicked(self):
        pass

    def moved(self):
        return True

    def setMovable(self, boolvalue):
        pass

    def getPos(self):
        return (0, 0)

    def getSize(self):
        return (0, 0)

    def setShortcut(self, sc):
        pass

    def __str__(self):
        x,y = self.getPos()
        w,h = self.getSize()
        return "<button %i,%i,%i,%i>" % (x,y,w,h)

    @classmethod
    def move(classobj, x,y):
        pass

    @classmethod
    def resize(classobj, w,h):
        pass
