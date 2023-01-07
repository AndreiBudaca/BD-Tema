import datetime
import frontend

import cx_Oracle as cx

TABLE_NAME = 0
COLUMNS = 1
PK = 2
FOREIGN_KEYS = 3

con = None
tableInfo = []
savepointList = []


def writeError(errMessage: str):
    file = open("errorLog.txt", "a")
    file.write(str(datetime.datetime.now()) + ": " + errMessage + "\n")
    file.close()
    frontend.errorWindow()


def clearLog():
    file = open("errorLog.txt", "w")
    file.write("")
    file.close()


def getPkColumnName(tableName: str) -> str:
    global tableInfo

    for tables in tableInfo:
        if tables[TABLE_NAME] == tableName:
            return tables[COLUMNS][tables[PK][0] - 1][0]

    return ""


def getTableNumber(tableName):
    global tableInfo

    i = 0
    for tables in tableInfo:
        if tables[TABLE_NAME] == tableName:
            return i
        i += 1

    return i


def convertToSqlString(val):
    # Check for None value
    if val is None:
        return "NULL, "

    # Check for numeric value
    if type(val) == int or type(val) == float:
        return str(val) + ", "

    # Check for date value
    if type(val) == datetime.datetime:
        return "to_date(\'" + str(val.date()) + "\', \'RRRR-MM-DD\'), "

    # Check for str value
    if type(val) == str:
        # Check for subquery
        if val.__contains__("SELECT"):
            return "(" + val + "), "
        else:
            return "\'" + val + "\', "

    return ", "


def getFkReferencedTable(tableName: str, colName: str) -> str:
    tableNr = getTableNumber(tableName)

    for fkInfo in tableInfo[tableNr][FOREIGN_KEYS]:
        if colName == fkInfo[0]:
            return fkInfo[1]

    return ""


def executeQuery(query: str):

    res = []
    try:
        cursor = con.cursor()
        cursor.execute(query)
    except Exception as e:
        writeError(str(e))
    finally:
        # Check for result
        try:
            for x in cursor:
                res.append(x)
            cursor.close()
        finally:
            return res


def initSession(dsn: str, user: str, password: str):

    # Creating a connection
    global con, tableInfo
    try:
        con = cx.connect(user=user, password=password, dsn=dsn)
    except Exception as e:
        writeError(": Failed to connect to database: " + str(e))
        exit(-1)

    # print("Connection established")

    # Get table names
    tableInfo = []
    qResult = executeQuery("SELECT table_name FROM user_tables")

    for x in qResult:
        tableInfo.append((x[0], [], [], []))

    # Get table columns
    for infoTuple in tableInfo:
        qResult = executeQuery("SELECT column_name, data_type FROM user_tab_cols WHERE table_name = \'"
                               + infoTuple[TABLE_NAME] + "\' ORDER BY column_id")
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


def createSavepoint(savePointName: str):

    # Check for valid savepoint name
    nextVal = 1
    found = False
    if savePointName is None or savePointName == "":

        savePointName = "Savepoint1"
        nextVal = 2

    while not found:
        if savePointName not in savepointList:
            found = True
        else:

            if savePointName.endswith(str(nextVal - 1)):
                savePointName = savePointName[:len(savePointName) - len(str(nextVal - 1))] + str(nextVal)
            else:
                savePointName += str(nextVal)
            nextVal += 1

    # Add the savepoint to savepoint list
    savepointList.append(savePointName)
    # Execute query
    executeQuery("SAVEPOINT " + savePointName)

    return savePointName


def deteleSavepoint(savePointName: str):
    try:
        savepointList.remove(savePointName)
    except:
        pass


def rollbackTo(savePointName: str):
    global savepointList
    if savePointName in savepointList:
        index = savepointList.index(savePointName)
        if index == 0:
            savepointList = savepointList[:1]
        else:
            savepointList = savepointList[:index + 1]

        executeQuery("ROLLBACK TO " + savePointName)


def getTableData(tableName: str) -> list:
    res = []

    if con is not None:
        qResult = executeQuery("SELECT * FROM " + tableName)

        for x in qResult:
            res.append(x)

    return res


def getTableDataByPk(tableName: str, pkVal) -> list:
    res = []
    pkCol = getPkColumnName(tableName)
    pkStr = convertToSqlString(pkVal)
    pkStr = pkStr[:len(pkStr) - 2]

    if con is not None:
        qResult = executeQuery("SELECT * FROM " + tableName + " WHERE " + pkCol + " = " + pkStr)

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


def deleteFromTable(tableName: str, pkVal):
    valStr = convertToSqlString(pkVal)
    valStr = valStr[:len(valStr) - 2]
    executeQuery("DELETE FROM " + tableName + " WHERE " + getPkColumnName(tableName) + " = " + valStr)


def modifyValueFromTable(tableName, pkVal, newVals: tuple):
    global tableInfo

    setString = ""

    tableNr = getTableNumber(tableName)
    pkName = getPkColumnName(tableName)
    pkValStr = convertToSqlString(pkVal)
    pkValStr = pkValStr[:len(pkValStr) - 2]

    i = 0
    for val in newVals:
        # Add column name and new val
        setString += tableInfo[tableNr][COLUMNS][i][0] + " = " + convertToSqlString(val)
        i += 1
    # Remove last ", "
    setString = setString[:len(setString) - 2]
    executeQuery("UPDATE " + tableName + " SET " + setString + " WHERE " + pkName + " = " + pkValStr)


def closeConnection():
    try:
        con.close()
    except:
        pass
