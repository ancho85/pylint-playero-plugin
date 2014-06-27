from tools import logHere

class cache:
    storage = {}

    debug = False
    skipDebug = []

    collectStats = False
    statistics = {}


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
                cls.storage[fid][args_id] = f(*args, **kwargs)

                if cls.debug and fname not in cls.skipDebug:
                    logHere("CACHE MISS: %s (%d) (args: %s) (kwargs: %s)"%(fname, fid, str(args), str(kwargs)))
                if cls.collectStats:
                    cls.setStatistics("miss", fname, *args, **kwargs)
            else:
                if cls.debug and fname not in cls.skipDebug:
                    logHere("CACHE HIT: %s (%d) (args: %s) (kwargs: %s)"%(fname, fid, str(args), str(kwargs)))
                if cls.collectStats:
                    cls.setStatistics("hit", fname, *args, **kwargs)
            return cls.storage[fid][args_id]
        return new_f

    @classmethod
    def flush(cls, f):
        cls.storage.pop(id(f))

    @classmethod
    def setStatistics(cls, statsType, fname, *args, **kwargs):
        args_id = tuple( args + tuple(kwargs.items()))
        if fname not in cls.statistics:
            cls.statistics[fname] = {"miss": {}, "hit": {}}
        if args_id not in cls.statistics[fname]["miss"]:
            cls.statistics[fname]["miss"][args_id] = 0
            cls.statistics[fname]["hit"][args_id] = 0
        cls.statistics[fname][statsType][args_id] += 1


    @classmethod
    def getStatistics(cls, detailed = True):
        res = []
        for fname in sorted(cls.statistics):
            for arg in sorted(cls.statistics[fname]["hit"]):
                hits = cls.statistics[fname]["hit"][arg]
                misses = cls.statistics[fname]["miss"][arg]
                res.append("Total %s(%s) Hits: %i -- Miss: %i" % (fname, arg, hits, misses))
                #if hits+misses > 0: res.append("Total %%Hits: %%%.2f\n" % (float(hits) / hits+misses * 100))
        return '\n'.join(res)
