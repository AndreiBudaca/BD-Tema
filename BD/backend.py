import datetime

import cx_Oracle as cx

TABLE_NAME = 0
COLUMNS = 1
PK = 2
FOREIGN_KEYS = 3

con = None


def getPkColumnName(tableInfo, tableName: str) -> str:
    for tables in tableInfo:
        if tables[TABLE_NAME] == tableName:
            return tables[COLUMNS][tables[PK][0] - 1][0]

    return ""


def convertToSqlString(val):
    # Check for None value
    if val is None:
        return "NULL, "

    # Check for numeric value
    if type(val) == int:
        return str(val) + ", "

    # Check for date value
    if type(val) == datetime.datetime:
        return "to_date(" + str(val.date()) + ", RRRR-MM-DD), "

    # Check for str value
    if type(val) == str:
        # Check for subquery
        if val.__contains__("SELECT"):
            return "(" + val + "), "
        else:
            return "\'" + val + "\', "

    return ", "


def executeQuery(query: str):

    res = []
    try:
        cursor = con.cursor()
        cursor.execute(query)
    except Exception as e:
        print(str(e))
        return []

    # Check for result
    try:
        for x in cursor:
            res.append(x)
    finally:

        cursor.execute("COMMIT")
        return res


def initSesion(address: str, port: int, serviceName: str, user: str, password: str) -> list:

    # Creating a connection
    global con
    dns = cx.makedsn(address, port, service_name=serviceName)
    try:
        con = cx.connect(user=user, password=password, dsn=dns)
    except Exception as e:
        file = open("errorLog.txt")
        file.write("Failed to connect to database: " + str(e))
        file.close()
        exit(-1)

    print("Connection established")

    # Get table names
    tableInfo = []
    qResult = executeQuery("SELECT table_name FROM user_tables")

    for x in qResult:
        tableInfo.append((x[0], [], [], []))

    # Get table columns
    for infoTuple in tableInfo:
        # TO DO
        qResult = executeQuery("SELECT column_name, data_type FROM all_tab_cols WHERE table_name = \'" + infoTuple[TABLE_NAME] + "\'")
        for x in qResult:
            infoTuple[COLUMNS].append(x)

    # Get PK column position
    for infoTuple in tableInfo:
        qResult = executeQuery("SELECT cols.position \
                                FROM all_constraints cons, all_cons_columns cols \
                                WHERE cols.table_name = \'" + infoTuple[TABLE_NAME] + "\' \
                                AND cons.constraint_type = \'P\' \
                                AND cons.constraint_name = cols.constraint_name \
                                AND cons.owner = cols.owner \
                                ORDER BY cols.table_name, cols.position")
        for x in qResult:
            infoTuple[PK].append(x[0])

    # Get foreign keys
    for infoTuple in tableInfo:
        qResult = executeQuery("SELECT a.column_name, c_pk.table_name \
                                FROM all_cons_columns a, all_constraints c, all_constraints c_pk \
                                WHERE a.owner = c.owner AND a.constraint_name = c.constraint_name \
                                AND c.r_owner = c_pk.owner AND c.r_constraint_name = c_pk.constraint_name \
                                AND c.constraint_type = 'R' AND a.table_name = \'" + infoTuple[TABLE_NAME] + "\'")

        for x in qResult:
            infoTuple[FOREIGN_KEYS].append((x[0], x[1]))

    return tableInfo


def getTableData(tableName: str) -> list:
    res = []

    if con is not None:
        qResult = executeQuery("SELECT * FROM " + tableName)

        for x in qResult:
            res.append(x)

    return res


def insertIntoTable(tableName: str, values: tuple):

    valuesString = "("
    for val in values:
        valuesString += convertToSqlString(val)

    # Delete last ", " and put ")" instead
    valuesString = valuesString[:len(valuesString) - 2] + ")"

    executeQuery("INSERT INTO " + tableName + " VALUES " + valuesString)
    executeQuery("COMMIT")


def deleteFromTable(tableName: str, pk_column: str, pkVal):
    valStr = convertToSqlString(pkVal)
    valStr = valStr[:len(valStr) - 2]
    executeQuery("DELETE FROM " + tableName + " WHERE " + pk_column + " = " + valStr)
