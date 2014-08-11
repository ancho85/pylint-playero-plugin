import threading

def getClientConnection():
    t = threading.currentThread()
    try:
        return t.client_connection
    except AttributeError, e:
        return None
