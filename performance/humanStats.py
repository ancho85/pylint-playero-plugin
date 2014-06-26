import sys

def printToFile():
    import pstats
    filename = sys.argv[1].split(".")[0]
    stream = open("%s.txt" % filename, 'w')
    stats = pstats.Stats(sys.argv[1], stream=stream)
    #stats.add('otherfile.stats')
    #stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "USAGE: python humanStats.py filename.ext"
    else:
        printToFile()
