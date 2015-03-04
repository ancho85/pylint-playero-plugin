"""
This script tests at once all python scripts in a given directory usign
async multiprocessing. All errors are stored in a separate filename.txt
and finally deletes zero-sized files, leaving only those showing errors
"""

import sys
import os

def silentRemove(fn):
    try:
        os.remove(fn)
    except OSError:
        pass

def doTest():
    import subprocess
    import ConfigParser
    import fnmatch

    try:
        configfile = str(os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "config", "playero.cfg")))
        config = ConfigParser.SafeConfigParser()
        config.read(configfile)
        pluginpath = config.get('plugin_paths', os.name)
        lintpath = config.get('pylint_paths', os.name)
    except ConfigParser.NoSectionError:
        pluginpath = "c:\\Python26\\Lib\\site-packages\\ooPlugin\\sublimetext-playero-plugin"
        lintpath = "c:\\Python26\\Lib\\site-packages\\pylint-1.0.0-py2.6.egg\\pylint\\lint.py"
        if (os.name == "posix"): #TODO put default linux values
            pluginpath = ""
            lintpath = ""


    envi = dict(os.environ)
    pythonpath = envi.get('PYTHONPATH', '')
    preffix = ""
    if len(pythonpath): preffix = ","
    envi['PYTHONPATH'] = pythonpath + "%s%s" % (preffix, pluginpath)

    thisPath = os.path.dirname(os.path.abspath(__file__))
    currRoot = None
    for root, dirnames, filenames in os.walk(sys.argv[1]):
        if not currRoot or root != currRoot:
            currRoot = root
            print root
        for filename in fnmatch.filter(sorted(filenames), '*.py'):
            print "Processing", filename
            pylintcmd = ["python"]
            pylintcmd.append(lintpath)
            pylintcmd.append("--errors-only")
            pylintcmd.append("--reports=n")
            pylintcmd.append("--files-output=y")
            pylintcmd.append("--output-format=text")
            pylintcmd.append("--msg-template={line}:{msg_id}:{msg} ")
            pylintcmd.append("--load-plugins=Playero ")
            pylintcmd.append("--rcfile=%s/config/.pylintrc" % pluginpath)
            #pylintcmd.extend(["--disable=all", "--enable=E6601"]) #use this line to check only a particular error
            pylintcmd.append(os.path.join(root, filename))

            process = subprocess.Popen(
                pylintcmd, stdout=subprocess.PIPE, stderr=file("_stderr%s.txt" % filename, "w"), env=envi
            )
            process.stdout.read() #to keep the process open until is finished and then delete zero size files

            (lambda: [silentRemove(fn) for fn in os.listdir(thisPath) if os.stat(fn).st_size == 0])()

    print "\a" #cross-platform alert on finish

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "USAGE: python generalTest.py PATHTOCHECK"
    else:
        import multiprocessing
        pool = multiprocessing.Pool(processes=None) #cpu_count()
        r = pool.apply_async(func=doTest)
        r.wait()
