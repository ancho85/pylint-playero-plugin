import os
import sys
import ConfigParser

if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(HERE, "..")) #pylint_playero_plugin path added to environment

    configLocation = os.path.join(HERE, "..", "config", "playero.cfg")
    config = ConfigParser.ConfigParser()
    config.readfp(open(configLocation))
    config.set("paths", "posix", os.path.join(HERE, "..", "Playero/"))
    config.set("plugin_paths", "posix", os.path.join(HERE, ".."))
    config.write(open(configLocation, "wb"))

    config.readfp(open(configLocation))
    print config.get("paths", "posix")
