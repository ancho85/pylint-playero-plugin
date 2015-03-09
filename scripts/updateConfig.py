import os.path as ospath
import sys
import ConfigParser

if __name__ == "__main__":
    HERE = ospath.join(ospath.dirname(ospath.abspath(__file__)), "..")
    sys.path.append(HERE) #pylint_playero_plugin path added to environment

    configLocation = ospath.join(HERE, "config", "playero.cfg")
    config = ConfigParser.ConfigParser()
    config.readfp(open(configLocation))
    config.set("paths", "posix", ospath.join(HERE, "Playero/"))
    config.set("plugin_paths", "posix", HERE)
    config.set("mysql", "connect", "1")
    config.set("mysql", "dbname", "playero")
    config.set("mysql", "host", "127.0.0.1")
    config.set("mysql", "user", "root")
    config.set("mysql", "pass", "")
    config.write(open(configLocation, "wb"))

