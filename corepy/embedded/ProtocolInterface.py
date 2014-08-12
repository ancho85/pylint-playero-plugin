import cPickle
from datetime import datetime
import socket

class Session(object):

    def __init__(self):
        self.user = None
        self.is_logued = False
        self._uptime = datetime.now()

    def getUptime(self):
        return self._uptime

    def getUser(self):
        return self.user

    def isLogued(self):
        return self.is_logued

class ConnectionClosed(Exception): pass

class ProtocolInterface(object):
    TIMEOUT = 5
    CLOSE_TIMEOUTS = 0 #cantidad de timeouts para cerrar la conexion

    dumb_connection = False

    def send(self, s):
        pass


    def sendObject(self, obj):
        self.send(cPickle.dumps(obj))

    def receive(self):
        return ""

    def receiveObject(self):
        recstr = self.receive()
        res = cPickle.loads(recstr)
        return res

    def sendCommand(self, cmd_code, *params):
        response = self.receiveObject()
        return response

    def receiveCommand(self):
        cmd_code, params = self.receiveObject()
        return cmd_code, params

    def responseToCommand(self, response):
        self.sendObject(response)

    def handleCommand(self, cmd=None, params=None):
        pass
    def _shouldKeepWaiting(self):
        return True

class ClientProtocolInterface(ProtocolInterface):
    TIMEOUT = 0.5
    CLOSE_TIMEOUTS = 0 #cantidad de timeouts para cerrar la conexion

    def __init__(self, host=None, port=None):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.rfile = self.socket.makefile('rb', -1)
        self.wfile = self.socket.makefile('wb', 0)
        self._keep_waiting = True

    def _shouldKeepWaiting(self):
        return self._keep_waiting

    def close(self):
        self._keep_waiting = False
        self.socket.close()

    def __del__(self):
        self.close()

    def sendInitialCommand(self, cmd_code, *params):
        return self.sendCommand(cmd_code, *params)


    def login(self, user, password):
        return self.sendInitialCommand("login", user, password)

    def getCurrentCompany(self):
        return self.sendInitialCommand("getCurrentCompany")

    def getCurrentUser(self):
        return self.sendInitialCommand("getCurrentUser")

    def restartServer(self):
        return self.sendInitialCommand("restartServer")

    def popEvent(self):
        return self.sendInitialCommand("popEvent")

    def postEvent(self, event):
        return self.sendInitialCommand("postEvent", event)

    def saveRecordAndCommit(self, record):
        res, srv_record = self.sendInitialCommand("saveRecordAndCommit", record)
        return res

    def getLoguedUsers(self):
        users = self.sendInitialCommand("getLoguedUsers")
        return users

    def runRoutine(self, routinename, spec):
        res = self.sendInitialCommand("runRoutine", routinename, spec)
        return res

    def getInfo(self):
        res = self.sendInitialCommand("getInfo")
        return res

    def displaymessage(self, msg, icon):
        return msg

    def askYesNo(self, msg):
        return msg

    def getSelection(self, msg, options, default=0):
        return msg

    def getString(self, msg, default=""):
        return msg

    def postMessage(self, msg):
        return msg

    def runOnClient(self, *args):
        fn_class, fn_name, fn_self = args[:3]
        if fn_self:
            return getattr(fn_class, fn_name)(fn_self, *args[3:])
        return getattr(fn_class, fn_name)(*args[3:])

class ServerProtocolInterface(ProtocolInterface):
    TIMEOUT = 5
    CLOSE_TIMEOUTS = 0 / TIMEOUT #cantidad de timeouts para cerrar la conexion

    def __init__(self):
        print "connection received"
        self.session = Session()

    def _shouldKeepWaiting(self):
        return False

    def login(self, user, password):
        self.session.user = None
        self.session.is_logued = True
        if self.session.is_logued:
            self.session.user = user
        return self.session.is_logued

    def getCurrentCompany(self):
        return ""

    def getCurrentUser(self):
        return ""

    def saveRecordAndCommit(self, record):
        return True

    def getLoguedUsers(self):
        return []

    def runRoutine(self, routinename, spec):
        return True

    def displaymessage(self, msg, icon):
        return self.receiveObject()

    def askYesNo(self, msg):
        return self.receiveObject()

    def getSelection(self, msg, options, default=0):
        return self.receiveObject()

    def getString(self, msg, default=""):
        return self.receiveObject()

    def postMessage(self, msg):
        return self.receiveObject()

    def restartServer(self):
        return True

    def runOnClient(self, fn_class, fn_name, fn_self, *args):
        return self.receiveObject()

    def postEvent(self, event):
        return event.dispatch()

    def popEvent(self):
        return None

    def getInfo(self):
        return {}

class WebServerTimeout(Exception):
    pass

class WebServerProtocolInterface(ServerProtocolInterface):

    dumb_connection = True

    def __init__(self, twisted_protocol):
        ServerProtocolInterface.__init__()
        self.twisted_protocol = twisted_protocol
        self.queue = []
        self.queue_items = {}

    def sendObject(self, obj):
        return

    def flush(self):
        pass

    def receiveObject(self):
        self.flush()

        msg = self.twisted_protocol.current_message
        return cPickle.loads(msg)

    def openWindow(self, window):
        return self.receiveObject()

    def openReport(self, report, openw):
        return self.receiveObject()

    def openURL(self, url):
        return self.receiveObject()

    def setImage(self, image):
        return self.receiveObject()

    def getOpenFileName(self, msg):
        return self.receiveObject()

    def notifyMessages(self, qty):
        return self.receiveObject()

    def heartbeat(self):
        return self.receiveObject()

    def rawAction(self, *args, **kwargs):
        return self.receiveObject()

    def _webclientSendId(self, idc):
        pass

    def saveFile(self, content, DefaultFileName, mode):
        return self.receiveObject()
