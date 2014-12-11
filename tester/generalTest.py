import sys

def doTest():
    import os
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
            pylintcmd.append("--reports=y")
            pylintcmd.append("--files-output=y")
            pylintcmd.append("--output-format=text")
            pylintcmd.append("--msg-template={line}:{msg_id}:{msg} ")
            pylintcmd.append("--load-plugins=Playero ")
            pylintcmd.append("--rcfile=%s/config/.pylintrc" % pluginpath)
            #pylintcmd.append("--disable=C0304,C0103,W0512,C0301,W0614,W0401,W0403,C0321,W0511,W0142,W0141,R0913,R0903,W0212,W0312,C0111,C0103,C0303")
            #pylintcmd.extend(["--disable=all", "--enable=E6601"]) #use this line to check only a particular error
            pylintcmd.append(os.path.join(root, filename))

            process = subprocess.Popen(
                pylintcmd, stdout=subprocess.PIPE, stderr=file("_stderr%s.txt" % filename, "w"), env=envi
            )
            process.stdout.read() #to keep the process open until is finished and then delete zero size files
    for zero in [zf for zf in os.listdir(os.path.dirname(os.path.abspath(__file__))) if os.stat(zf).st_size == 0]:
        os.remove(zero)
    print "\a" #cross-platform alert on finish


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "USAGE: python generalTest.py PATHTOCHECK"
    else:
        import multiprocessing
        pool = multiprocessing.Pool(processes=None) #cpu_count()
        r = pool.apply_async(func=doTest)
        r.wait()
        #doTest()
