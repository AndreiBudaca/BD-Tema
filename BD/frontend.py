import tkinter as tk
from tkinter import ttk, font
import backend
import datetime
from functools import partial

mainWindow = None
currPanel = None


def errorWindow(text="An error has occurred. Check error log"):
    errorWin = tk.Tk(className="Error")
    errorWin.geometry("210x50")
    ttk.Label(errorWin, text=text).grid(row=1, sticky="EW")
    ttk.Button(errorWin, text="Ok", command=errorWin.destroy).grid(row=2)
    errorWin.eval('tk::PlaceWindow . center')
    errorWin.mainloop()


def convertToPrintableString(val) -> str:
    # Check for None value
    if val is None:
        return "NULL"

    # Check for numeric value
    if type(val) == int or type(val) == float:
        return str(val)

    # Check for date value
    if type(val) == datetime.datetime:
        return str(val.date())

    # Check for str value
    if type(val) == str:
        return val

    return "Unknown"


def setHomeScreen():
    global currPanel

    if currPanel is not None:
        currPanel.grid_forget()

    currPanel = ttk.Frame(mainWindow)
    helloLabel = ttk.Label(currPanel, text="\n\n\n\n  Welcome to GUI Database Manager", font=font.Font(size=34))
    helloLabel.grid(row=1)
    infoLabel = ttk.Label(currPanel, text="\nSelect an action from the menubar", font=font.Font(size=14))
    infoLabel.grid(row=2)
    currPanel.grid()


def deleteAction(tableName: str, pkVal):
    backend.deleteFromTable(tableName, pkVal)
    setTableScreen(tableName)


def modifyAction(popUpWindow, filedsMaster, ddMenuOption: dict, tableName: str, pkVal, notInsertOrModify):

    pkName = backend.getPkColumnName(tableName)
    tableNr = backend.getTableNumber(tableName)
    insertData = []
    # Get values for each column
    for colInfo in backend.tableInfo[tableNr][backend.COLUMNS]:
        # If value is not pk insert the value
        if colInfo[0] != pkName:
            infoWidget = filedsMaster.children.get(colInfo[0].lower())
            if infoWidget is None:
                infoWidget = ddMenuOption.get(colInfo[0].lower())
                try:
                    rawVal = infoWidget.get().split(" ")[0]
                except:
                    backend.closeConnection()
                    exit(0)
            else:
                try:
                    rawVal = infoWidget.get()
                except:
                    backend.closeConnection()
                    exit(0)
        else:
            rawVal = pkVal if notInsertOrModify else None

        # Convert rawVal to expected type
        if colInfo[1] == "VARCHAR" or colInfo[1] == "VARCHAR2" and rawVal is not None:
            insertData.append(rawVal)
        if colInfo[1] == "NUMBER" and rawVal is not None:
            try:
                insertData.append(float(rawVal))
            except:
                errorWindow("Numeric value expected!")
        if colInfo[1] == "DATE" and rawVal is not None:
            dates = rawVal.split("-")
            if len(dates) != 3:
                errorWindow("Date value expected!")
                return
            try:
                insertData.append(datetime.datetime(year=int(dates[0]), month=int(dates[1]), day=int(dates[2])))
            except:
                errorWindow("Date value expected!")
                return
        if rawVal is None:
            insertData.append(None)

    if notInsertOrModify:
        backend.modifyValueFromTable(tableName, pkVal, tuple(insertData))
    else:
        backend.insertIntoTable(tableName, tuple(insertData))

    try:
        popUpWindow.destroy()
    except:
        backend.closeConnection()
        exit(0)
    setTableScreen(tableName)



def modifyPopUp(tableName: str, pkVal, notInsertOrModify: bool):

    tableNr = backend.getTableNumber(tableName)
    table = backend.tableInfo[tableNr]
    fkNewVals = {}
    modifyWindow = tk.Tk(className="Modify" if notInsertOrModify else "Insert")
    modifyWindow.geometry("400x400")
    modifyWindow.eval('tk::PlaceWindow . center')

    # Modify label
    ttk.Label(modifyWindow, text="Modify values bellow" if notInsertOrModify else "Insert values bellow",
              font=font.Font(size=12, weight='bold')).grid(row=1, column=1, pady=15,)

    # Value field
    canvas = tk.Canvas(modifyWindow, width=370, height=300)
    scrollbar1 = ttk.Scrollbar(modifyWindow, orient="vertical", command=canvas.yview)
    scrollbar2 = ttk.Scrollbar(modifyWindow, orient="horizontal", command=canvas.xview)
    valuesGrid = ttk.Frame(canvas)
    valuesGrid.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=valuesGrid, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar1.set, xscrollcommand=scrollbar2.set)

    # Get old values
    oldVals = []
    if notInsertOrModify:
        oldVals = backend.getTableDataByPk(tableName, pkVal)

    row = 1
    valRow = 0

    for columnInfo in table[backend.COLUMNS]:
        if notInsertOrModify:
            val = oldVals[0][valRow]
        else:
            val = 0
        # If value is not pk
        if valRow + 1 != table[backend.PK][0]:
            # Add column name
            ttk.Label(valuesGrid, text=columnInfo[0]).grid(row=row, column=1, pady=15, padx=15)

            # Add entry widget
            referencedTable = backend.getFkReferencedTable(tableName, columnInfo[0])
            if referencedTable != "":
                # Dropdown entry if FK
                variable = tk.StringVar(valuesGrid, name=columnInfo[0].lower())
                fkNewVals[columnInfo[0].lower()] = variable
                if not notInsertOrModify:
                    variable.set("Select an item")
                optList = []
                # Get values from referenced table
                referencedVals = backend.getTableData(referencedTable)

                for valTuple in referencedVals:
                    # Concat vals (first val will always be PK)
                    refNr = backend.getTableNumber(referencedTable)
                    pkNr = backend.tableInfo[refNr][backend.PK][0]

                    tupleString = convertToPrintableString(valTuple[pkNr - 1]) + " "
                    tupleNr = 0
                    for val in valTuple:
                        if tupleNr != pkNr - 1:
                            tupleString += convertToPrintableString(val) + " "
                        tupleNr += 1

                    if notInsertOrModify and str(valTuple[pkNr - 1]) == str(oldVals[0][valRow]):
                        variable.set(tupleString)
                    optList.append(tupleString)

                # Create drop down menu
                tk.OptionMenu(valuesGrid, variable, optList[0], *(optList[1:])).grid(row=row, column=2)

            else:
                # Normal entry if not FK
                aux = ttk.Entry(valuesGrid, name=columnInfo[0].lower(), width=35)
                if notInsertOrModify:
                    aux.insert(0, convertToPrintableString(val))
                aux.grid(row=row, column=2)

            row = row + 1
        valRow = valRow + 1

    canvas.grid(row=2, column=1)
    scrollbar1.grid(row=2, column=2, sticky="NS")
    scrollbar2.grid(row=3, column=1, sticky="EW")

    # Modify button
    ttk.Button(modifyWindow, text="Modify" if notInsertOrModify else "Insert",
               command=partial(modifyAction, modifyWindow, valuesGrid, fkNewVals, tableName, pkVal, notInsertOrModify))\
        .grid(row=4, column=1)


def setTableScreen(tableName: str):
    global currPanel, mainWindow
    tableNr = backend.getTableNumber(tableName)
    pkCol = backend.tableInfo[tableNr][backend.PK][0]
    nrCols = len(backend.tableInfo[tableNr][backend.COLUMNS])

    if currPanel is not None:
        try:
            currPanel.destroy()
        except:
            backend.closeConnection()
            exit(0)

    currPanel = ttk.Frame(mainWindow)

    # Add table name
    tableLabel = ttk.Label(currPanel, text=tableName, font=font.Font(size=14, weight='bold'))
    tableLabel.grid(row=1, column=2, pady=30)

    # Create scrolable canvas
    canvas = tk.Canvas(currPanel, width=750, height=300)
    scrollbar1 = ttk.Scrollbar(currPanel, orient="vertical", command=canvas.yview)
    scrollbar2 = ttk.Scrollbar(currPanel, orient="horizontal", command=canvas.xview)
    tableGrid = ttk.Frame(canvas)
    tableGrid.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=tableGrid, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar1.set, xscrollcommand=scrollbar2.set)

    # Add table columns
    colString = "\n\n"
    col = 1
    for column in backend.tableInfo[tableNr][backend.COLUMNS]:
        ttk.Label(tableGrid, text=column[0], font=font.Font(size=10, weight='bold')) \
            .grid(row=1, column=col, sticky='W', padx=15, pady=10)

        col += 1

    # Add table values
    i = 2
    values = backend.getTableData(tableName)
    for val in values:
        col = 1
        for x in val:
            ttk.Label(tableGrid, text=convertToPrintableString(x), font=font.Font(size=9)) \
                .grid(row=i, column=col, sticky="W", padx=15)

            # If the value is PK value
            if col == pkCol:
                # Create delete button
                ttk.Button(
                    tableGrid, text="Delete",
                    command=partial(deleteAction, tableName, x)
                ).grid(column=nrCols + 2, row=i, padx=15)

                # Create modify button
                ttk.Button(
                    tableGrid, text="Modify",
                    command=partial(modifyPopUp, tableName, x, True)
                ).grid(column=nrCols + 1, row=i, padx=15)

            col += 1
        i += 1

    canvas.grid(row=2, column=2)
    scrollbar1.grid(row=2, column=3, sticky="NS")
    scrollbar2.grid(row=3, column=2, sticky="EW")

    ttk.Button(
        currPanel, text="Insert new value",
        command=partial(modifyPopUp, tableName, None, False)
    ).grid(column=2, row=4, pady=30)

    currPanel.grid()


def setErrorLogScreen():
    global currPanel, mainWindow

    if currPanel is not None:
        try:
            currPanel.destroy()
        except:
            backend.closeConnection()
            exit(0)

    currPanel = ttk.Frame(mainWindow)
    # Create scrolable canvas
    canvas = tk.Canvas(currPanel, width=770, height=550)
    scrollbar1 = ttk.Scrollbar(currPanel, orient="vertical", command=canvas.yview)
    scrollbar2 = ttk.Scrollbar(currPanel, orient="horizontal", command=canvas.xview)
    logGrid = ttk.Frame(canvas)
    logGrid.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=logGrid, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar1.set, xscrollcommand=scrollbar2.set)

    i = 1
    for line in open("errorLog.txt", "r").readlines():
        tk.Label(logGrid, text=line, font=font.Font(size=9)).grid(row=i)
        i += 1

    canvas.grid(row=2, column=2)
    scrollbar1.grid(row=2, column=3, sticky="NS")
    scrollbar2.grid(row=3, column=2, sticky="EW")

    currPanel.grid()


def initGui():
    global mainWindow

    # Create main window
    mainWindow = tk.Tk(className="DB Gui")
    mainWindow.geometry("800x600")
    mainWindow.resizable(False, False)

    # Create menu bar
    menubar = tk.Menu(mainWindow)
    mainWindow.config(menu=menubar)

    # Create home option
    menubar.add_command(label="Home", command=setHomeScreen)

    # Create table option and sub menus
    tableMenu = tk.Menu(menubar, tearoff=0)
    for table in backend.tableInfo:
        tableMenu.add_command(
            label=table[backend.TABLE_NAME],
            command=partial(setTableScreen, table[backend.TABLE_NAME])
        )
    menubar.add_cascade(
        label="Tables",
        menu=tableMenu
    )

    # Create terminal option
    menubar.add_command(label="SQL Terminal")

    # Add commit and rollback
    sesionMenu = tk.Menu(menubar, tearoff=0)
    sesionMenu.add_command(
        label="Rollback"
    )
    sesionMenu.add_command(
        label="Savepoint"
    )
    sesionMenu.add_command(
        label="Commit",
        command=partial(backend.executeQuery, "COMMIT")
    )
    menubar.add_cascade(
        label="Sesion",
        menu=sesionMenu
    )

    # Add error log
    menubar.add_command(label="Error log", command=setErrorLogScreen)

    # Set panel
    setHomeScreen()


def runGui():
    if mainWindow is not None:
        mainWindow.mainloop()
