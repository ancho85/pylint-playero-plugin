import os
import re
from libs.tools import logHere

def validateSQL(txt, filename=None):
    from libs.funcs import getConfig
    config = getConfig()
    if config.get("mysql", "dbname") == "databasename": return "MySQL database is not configured. Check playero.cfg file"
    if config.get("mysql", "pass") == "******": return "MySQL password is not configured. Check playero.cfg file"
    txt = parseSQL(txt)
    if int(config.get("mysql", "useapi")):
        res = apiValidateSQL(txt, config)
    else:
        txt = "%s%s%s" % ("START TRANSACTION;\n", txt, ";\nROLLBACK;\n")
        res = cmdValidateSQL(txt, config)
    if res:
        logHere(txt, filename=["queryError.log", filename][bool(filename)])
    return res

def parseSQL(txt):
    table_pattern = re.compile("([^\\\])\[([^\]]*?)\]")
    field_pattern = re.compile(r"\{([^\}]*?)\}")
    value_pattern = re.compile(r"[svdt]\|([^\|]*?)\|")
    integer_value_pattern = re.compile(r"i\|([^\|]*?)\|")
    boolean_value_pattern = re.compile(r"b\|([^\|]*?)\|")
    where_and_pattern = re.compile(r"(WHERE\?AND)", re.I)
    #schemas_pattern = re.compile(r"\[([^\]]*?)\]")
    show_pattern = re.compile(r"^SHOW.*STATUS", re.I) #Commands like SHOW INNODB STATUS or SHOW TABLE STATUS
    from_pattern = re.compile(ur"""(?<=FROM\s)                                  #Start of positive lookbehind assertion FROM
                                  (.*?)                                         #Any character zero to infinite times
                                  (?:                                           #Start of non-capturing group
                                    $|                                          #Anchor to end of line
                                    \s+                                         #One or more spaces before Optional syntax
                                    (?=                                         #Start of positive lookahead assertion
                                        INNER\s+JOIN|
                                        LEFT\s+JOIN|
                                        RIGHT\s+JOIN|
                                        WHERE|
                                        GROUP\s+BY|
                                        HAVING|
                                        ORDER\s+BY|
                                        LIMIT|
                                        PROCEDURE|
                                        INTO\s+OUTFILE|
                                        FOR\s+UPDATE|
                                        LOCK\s+IN\s+SHARE\s+MODE
                                    )                                           #End of lookahead assertion. Optional syntax
                                  )                                             #End of non capturing group
                               """, re.IGNORECASE | re.VERBOSE | re.DOTALL)

    def value_replacer(mo):
        return "'%s'" % mo.group(1).replace("[","\\[").replace("{", "\\{")
    def integer_value_replacer(mo):
        return "%s0" % mo.group(1).replace("[","\\[").replace("{", "\\{")
    def boolean_value_replacer(mo):
        return {"true": "1", "1": "1", "false": "0", "0": "0"}[mo.group(1).replace("[","\\[").replace("{", "\\{").lower()]
    def force_no_rows(mo):
        return "%s INNER JOIN mysql.`host` ON FALSE\n" % mo.group(1) #doing this I make sure never returns any row
    txt = value_pattern.sub(value_replacer, txt)
    txt = boolean_value_pattern.sub(boolean_value_replacer, txt)
    txt = integer_value_pattern.sub(integer_value_replacer, txt)
    txt = table_pattern.sub(r"\g<1>`\g<2>` ", txt)
    txt = field_pattern.sub(r"`\g<1>`", txt)
    mo = where_and_pattern.search(txt)
    if mo:
        txt = "%sWHERE%s" % (txt[:mo.start()], txt[mo.end():])
        txt = where_and_pattern.sub("AND", txt)
    txt = from_pattern.sub(force_no_rows, txt)
    txt = txt.replace(";", " ")
    txt = txt.replace("\\[", "[").replace("\\{", "{")
    if show_pattern.match(txt):
        txt = "SELECT 1" #Forcing a simple query. mysql hangs at cmdValidateSQL
    return txt

def apiValidateSQL(txt, config):
    res = ""
    import MySQLdb
    cnf = lambda x: config.get("mysql", x)
    try:
        db = MySQLdb.connect(cnf("host"), cnf("user"), cnf("pass"), cnf("dbname"), int(cnf("port")), connect_timeout=1)
    except MySQLdb.OperationalError, e:
        res = "ERROR %s %s" % (e.args[0], e.args[1])
    else:
        try:
            c = db.cursor()
            c.execute(txt)
            c.close()
            db.rollback()
        except MySQLdb.MySQLError, e:
            res = "ERROR %s %s" % (e.args[0], e.args[1])
        finally:
            db.close()
    return parseErrorResponses(res)

def cmdValidateSQL(txt, config):
    """validates sql string using command line"""

    import subprocess
    mysqlcmd = ["%s/mysql" % config.get("mysql", "%spath" % os.name)]
    mysqlcmd.append("-u%s" % config.get('mysql', 'user'))
    pwd = config.get('mysql', 'pass')
    if pwd: mysqlcmd.append("-p%s" % pwd)
    mysqlcmd.append("-h%s" % config.get('mysql', 'host'))
    mysqlcmd.append("-P%s" % config.get('mysql', 'port'))
    mysqlcmd.append("-D%s" % config.get('mysql', 'dbname'))
    mysqlcmd.append("--batch")
    mysqlcmd.append("-e")
    mysqlcmd.append("%s" % txt)
    process = subprocess.Popen(
        mysqlcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return parseErrorResponses(process.stderr.read())

def parseErrorResponses(errorTxt):
    res = ""
    m = re.search('ERROR ([0-9]*).*', errorTxt)
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
        elif found == 1049: #Database doesn't exists
            res = m.group(0)
        elif found == 1045: #Wrong password
            res = m.group(0)
        #else: #Other errors
        #    res = m.group(0)
    return res.rstrip("\n").rstrip("\r")


if __name__ == "__main__":
    sql = "SELECT {Code} FROM [User]"
    print validateSQL(sql)
