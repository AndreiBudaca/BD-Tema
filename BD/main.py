import datetime
import tkinter as tk

import backend

if __name__ == "__main__":

    tableInfo = backend.initSesion("bd-dc.cs.tuiasi.ro", 1539, "orcl", "bd018", "bd018")
    # table = tableInfo[0][backend.TABLE_NAME]
    # backend.insertIntoTable(table, (20, "Test"))
    #
    # info = backend.getTableData('CLIENTI')
    # for x in info:
    #    print(x)
    #
    # print("_" * 20)
    #
    # pkCol = backend.getPkColumnName(tableInfo, tableName=table)
    # print(pkCol)
    # pkVal = 20
    # backend.deleteFromTable(table, pkCol, pkVal)
    #
    #
    #
    # info2 = backend.getTableData(table)
    # for x in info2:
    #     print(x)

    for x in tableInfo:
        print(x)

