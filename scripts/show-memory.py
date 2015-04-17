import os
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
logPath = os.path.join(HERE, "logs")

def printFile(fn):
    print fn, open(os.path.join(logPath, fn), "r").read(), "\n"

if __name__ == "__main__":
    (lambda: [printFile(fn) for fn in os.listdir(logPath) if fn.startswith("memory-")])()
