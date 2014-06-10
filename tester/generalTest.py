import sys

def doTest():
    import os
    import subprocess
    import ConfigParser

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


    pylintcmd = ["python"]
    pylintcmd.append(lintpath)
    pylintcmd.append("--errors-only")
    pylintcmd.append("--reports=y")
    pylintcmd.append("--files-output=y")
    pylintcmd.append("--output-format=text")
    pylintcmd.append("--msg-template={path}:{line}:{msg_id}:{msg} ")
    pylintcmd.append("--load-plugins=Playero ")
    pylintcmd.append("--rcfile=../config/.pylintrc ")
    #pylintcmd.append("--disable=C0304,C0103,W0512,C0301,W0614,W0401,W0403,C0321,W0511,W0142,W0141,R0913,R0903,W0212,W0312,C0111,C0103,C0303")
    pylintcmd.append(sys.argv[1])

    process = subprocess.Popen(
        pylintcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=envi
    )
    print process.stderr.read()
    print "processing\n", process.stdout.read()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "USAGE: python generalTest.py PATHTOCHECK"
    else:
        doTest()