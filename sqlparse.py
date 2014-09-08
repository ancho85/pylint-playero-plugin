def parseSQL(txt):
    import re
    table_pattern = re.compile("([^\\\])\[([^\]]*?)\]")
    field_pattern = re.compile("\{([^\}]*?)\}")
    value_pattern = re.compile("[svdt]\|([^\|]*?)\|")
    integer_value_pattern = re.compile("i\|([^\|]*?)\|")
    boolean_value_pattern = re.compile("b\|([^\|]*?)\|")
    where_and_pattern = re.compile("(WHERE\?AND)")
    schemas_pattern = re.compile("\[([^\]]*?)\]")

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
        return "%s" % mo.group(1).replace("[","\\[").replace("{", "\\{")
    def boolean_value_replacer(mo):
        return {"true": "1", "1": "1", "false": "0", "0": "0"}[mo.group(1).replace("[","\\[").replace("{", "\\{").lower()]
    txt = value_pattern.sub(value_replacer, txt)
    txt = boolean_value_pattern.sub(boolean_value_replacer, txt)
    txt = integer_value_pattern.sub(integer_value_replacer, txt)
    txt = table_pattern.sub("\g<1>`\g<2>`", txt)
    txt = field_pattern.sub("`\g<1>`", txt)
    txt = where_and_pattern.sub(where_and_replacer, txt)
    txt = txt.replace("\\[", "[").replace("\\{", "{")
    if not txt.find(";") > -1:
        txt += ";"
    return txt

def validateSQL(txt):
    import os
    configLocation = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config", "mysql.cfg")
    if not os.path.exists(configLocation): return True
    f = open(configLocation, "r")
    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.readfp(f) #the configuration file can change, so it must be opened every time
    f.close()
    if not int(config.get("mysql", "connect")): return True
    dbstring = config.get('mysql', 'host')
    dbstring += ":" + config.get('mysql', 'user')
    dbstring += ":" + config.get('mysql', 'pass')
    dbstring += ":" + config.get('mysql', 'dbname')
    dbstring += ":" + config.get('mysql', 'port')
    from mysqlparser.pylib import db
    dbh = db.Connect(dbstring)
    from mysqlparser.pylib import schema
    db = schema.Schema(dbh)
    txt = parseSQL(txt)
    from mysqlparser.parser_lib import validator
    val = validator.Validator(db_schema=db)
    res = val.ValidateString(txt)
    return True

if __name__ == "__main__":
    sql = "SELECT {Code} FROM [User]\n"
    sql += "WHERE internalId > 0\n"
    sql += "AND internalId < 10\n"
    sql += "AND internalId != 5\n"
    validateSQL(sql)
