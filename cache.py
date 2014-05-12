class cache:
    storage = {}

    debug = False
    skipDebug = []

    @classmethod
    def store(cls, f):
        fid = id(f)
        fname = "unknown"
        if hasattr(f, "__name__"):
            fname = f.__name__
        def new_f(*args, **kwargs):
            if fid not in cls.storage:
                cls.storage[fid] = {}
            args_id = tuple( args + tuple(kwargs.items()) )
            if args_id not in cls.storage[fid]:
                if cls.debug and fname not in cls.skipDebug: print "CACHE MISS: %s (%d) (args: %s) (kwargs: %s)"%(fname, fid, str(args), str(kwargs))
                cls.storage[fid][args_id] = f(*args, **kwargs)
            else:
                if cls.debug and fname not in cls.skipDebug: print "CACHE HIT: %s (%d) (args: %s) (kwargs: %s)"%(fname, fid, str(args), str(kwargs))
            return cls.storage[fid][args_id]
        return new_f

    @classmethod
    def flush(cls, f):
        cls.storage.pop(id(f))
