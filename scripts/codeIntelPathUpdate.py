"""
This script updates all paths in SublimeCodeIntel.sublime-settings related to Playero current location
parsing his settings.xml
"""
import os
import json
import ConfigParser
import re
import imp

HERE = os.path.dirname(os.path.realpath(__file__))


def parse_json(filename):
    """ Parse a JSON file
        First remove comments and then use the json module package
        Comments look like :
            // ...
        or
            /*
            ...
            */
    """
    comment_re = re.compile(
        '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
        re.DOTALL | re.MULTILINE
    )
    with open(filename) as f:
        content = ''.join(f.readlines())
        match = comment_re.search(content)
        while match:
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)
        return json.loads(content)


if __name__ == "__main__":
    if os.name == "nt":
        settingFilePath = os.path.join(os.getenv('APPDATA'), "Sublime Text 2", "Packages", "User", "SublimeCodeIntel.sublime-settings")
        setObj = parse_json(settingFilePath)
        with open(settingFilePath, "w") as jsonFile:

            configfile = str(os.path.normpath(os.path.join(HERE, "..", "config", "playero.cfg")))
            config = ConfigParser.SafeConfigParser()
            config.read(configfile)
            playeropath = config.get('paths', os.name)
            pluginpath = config.get('plugin_paths', os.name)

            newPaths = [os.path.join(pluginpath, "corepy", "embedded")]
            newPaths.append(os.path.join(playeropath, "python", "python24", "Lib"))
            newPaths.append(os.path.join(playeropath, "python", "python24", "Lib", "site-packages", "windows"))
            newPaths.append(os.path.join(playeropath, "python", "python24", "shared-libs", "windows"))
            newPaths.append(os.path.join(playeropath, "core"))


            xmlparse = imp.load_source("xmlparse", os.path.join(HERE, "..", "libs", "xmlparse.py"))

            settingsFile = playeropath + "settings/settings.xml"
            dh = xmlparse.parseSettingsXML(settingsFile)
            res = dh.scriptdirs[:255+1]

            for main, sub in [(m, s) for m in res for s in ("records", "reports", "documents", "routines", "windows", "tools")]:
                newPaths.append(os.path.join(playeropath, main, sub))

            setObj["codeintel_language_settings"]["Python"]["codeintel_scan_extra_dir"] = newPaths

            jsonFile.seek(0)  # rewind
            jsonFile.write(json.dumps(setObj, sort_keys=True, indent=4, separators=(',', ': ')))
            jsonFile.truncate()
