def getMySQLConfig():
    import os
    configLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config", "mysql.cfg")
    if not os.path.exists(configLocation): return None
    f = open(configLocation, "r")
    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.readfp(f) #the configuration file can change, so it must be opened every time
    f.close()
    return config

def validateSQL(txt):
    config = getMySQLConfig()
    if not config: return ""
    if not int(config.get("mysql", "connect")): return ""
    txt = "%s%s%s" % ("START TRANSACTION;\n", parseSQL(txt), ";\nROLLBACK;\n")
    if int(config.get("mysql", "useapi")):
        res = apiValidateSQL(txt, config)
    else:
        res = cmdValidateSQL(txt, config)
    return res

def parseSQL(txt):
    import re
    table_pattern = re.compile("([^\\\])\[([^\]]*?)\]")
    field_pattern = re.compile(r"\{([^\}]*?)\}")
    value_pattern = re.compile(r"[svdt]\|([^\|]*?)\|")
    integer_value_pattern = re.compile(r"i\|([^\|]*?)\|")
    boolean_value_pattern = re.compile(r"b\|([^\|]*?)\|")
    where_and_pattern = re.compile(r"(WHERE\?AND)", re.I)
    #schemas_pattern = re.compile(r"\[([^\]]*?)\]")
    limit_pattern = re.compile(r"(LIMIT [0-9]*[,\s]*[0-9]*|OFFSET [0-9]+)", re.I)
    unionall_pattern = re.compile(r'UNION ALL', re.I)
    insert_pattern = re.compile(r'INSERT [INTO]+', re.I)

    global k
    k = 0
    def where_and_replacer(mo):
        global k
        k += 1
        if k == 1: return "WHERE"
        return "AND"
    def value_replacer(mo):
        return "'%s'" % mo.group(1).replace("[","\\[").replace("{", "\\{")
    def integer_value_replacer(mo):
        return "%s0" % mo.group(1).replace("[","\\[").replace("{", "\\{")
    def boolean_value_replacer(mo):
        return {"true": "1", "1": "1", "false": "0", "0": "0"}[mo.group(1).replace("[","\\[").replace("{", "\\{").lower()]
    txt = value_pattern.sub(value_replacer, txt)
    txt = boolean_value_pattern.sub(boolean_value_replacer, txt)
    txt = integer_value_pattern.sub(integer_value_replacer, txt)
    txt = table_pattern.sub(r"\g<1>`\g<2>`", txt)
    txt = field_pattern.sub(r"`\g<1>`", txt)
    txt = where_and_pattern.sub(where_and_replacer, txt)
    txt = txt.replace(";", " ")
    txt = limit_pattern.sub(" ", txt) #removes the limit part
    txt = unionall_pattern.sub("LIMIT 0\nUNION ALL", txt) #if are multiple selects with union all, adds the limit 0
    txt = txt.replace("\\[", "[").replace("\\{", "{")
    insertmatch = insert_pattern.search(txt)
    if insertmatch:
        txt = limit_pattern.sub(" ", txt) #removes the limit part again. Insert doesn't support LIMIT
    else:
        txt += " LIMIT 0"
    return txt

def apiValidateSQL(txt, config):
    """validates sql string using google-mysql-tools api"""
    dbstring = config.get('mysql', 'host')
    dbstring += ":" + config.get('mysql', 'user')
    dbstring += ":" + config.get('mysql', 'pass')
    dbstring += ":" + config.get('mysql', 'dbname')
    dbstring += ":" + config.get('mysql', 'port')
    from mysqlparser.pylib import db
    dbh = db.Connect(dbstring)
    from mysqlparser.pylib import schema
    db = schema.Schema(dbh)
    from mysqlparser.parser_lib import validator
    val = validator.Validator(db_schema=db)
    res = val.ValidateString(txt)
    res = ""
    return res

def cmdValidateSQL(txt, config):
    """validates sql string using command line"""
    res = ""
    import subprocess
    mysqlcmd = ["%s/mysql.exe" % config.get("mysql", "path")]
    mysqlcmd.append("-u%s" % config.get('mysql', 'user'))
    mysqlcmd.append("-p%s" % config.get('mysql', 'pass'))
    mysqlcmd.append("-h%s" % config.get('mysql', 'host'))
    mysqlcmd.append("-P%s" % config.get('mysql', 'port'))
    mysqlcmd.append("-D%s" % config.get('mysql', 'dbname'))
    mysqlcmd.append("--batch")
    mysqlcmd.append("-e")
    mysqlcmd.append("%s" % txt)
    process = subprocess.Popen(
        mysqlcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    import re

    m = re.search('ERROR ([0-9]*).*', process.stderr.read())
    if m:
        found = int(m.group(1))
        if found == 1064: #Query syntax
            m2 = re.search('right syntax to use near (.*).*', m.group(0))
            if m2:
                res = m2.group(1)
        elif found == 1146: #Table doesn't exists
            m2 = re.search('Table (.*).*', m.group(0))
            if m2:
                res = m2.group(1)
        elif found == 1054: #Unknown column
            pass
    return res


if __name__ == "__main__":
    sql = "SELECT {Code}, FROM [User];"
    print validateSQL(sql)
