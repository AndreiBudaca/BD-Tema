import tkinter as tk
from tkinter import ttk, font
import backend
import datetime

mainWindow = None
currPanel = None

dsn = ""
user = ""
password = ""


def connectAction(window):
    global dsn, user, password
    dsn = window.children.get("dsn").get()
    user = window.children.get("user").get()
    password = window.children.get("password").get()
    window.destroy()


def connectWindow():
    connWin = tk.Tk(className="Connect")
    connWin.geometry("210x300")
    ttk.Label(connWin, text="\tEnter connection info").grid(row=1, sticky="EW", pady=25)

    # dns
    ttk.Label(connWin, text="DSN").grid(row=2)
    e1 = ttk.Entry(connWin, name="dsn", width=32)
    e1.insert(0, "localhost/xe")
    e1.grid(row=3, padx=5)

    # user
    ttk.Label(connWin, text="USER").grid(row=4)
    e2 = ttk.Entry(connWin, name="user", width=32)
    e2.insert(0, "guiuser")
    e2.grid(row=5, padx=5)

    # user
    ttk.Label(connWin, text="PASSWORD").grid(row=6)
    e3 = ttk.Entry(connWin, name="password", width=32, show="*")
    e3.insert(0, "gui")
    e3.grid(row=7, padx=5)

    ttk.Button(connWin, text="Ok", command=lambda: connectAction(connWin)).grid(row=8)

    connWin.eval('tk::PlaceWindow . center')
    connWin.resizable(False, False)
    connWin.mainloop()


def errorWindow(text="An error has occurred. Check error log"):
    errorWin = tk.Tk(className="Error")
    errorWin.geometry("210x50")
    ttk.Label(errorWin, text=text).grid(row=1, sticky="EW")
    ttk.Button(errorWin, text="Ok", command=errorWin.destroy).grid(row=2)
    errorWin.eval('tk::PlaceWindow . center')
    errorWin.resizable(False, False)
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
    global currPanel, mainWindow

    if currPanel is not None:
        currPanel.destroy()

    currPanel = ttk.Frame(mainWindow)
    helloLabel = ttk.Label(currPanel, text="\n\n\n\n  Welcome to GUI Database Manager", font=font.Font(size=34))
    helloLabel.grid(row=1)
    infoLabel = ttk.Label(currPanel, text="\nSelect an action from the menubar", font=font.Font(size=14))
    infoLabel.grid(row=2, pady=15)

    currPanel.grid()


def deleteAction(tableName: str, pkVal):
    backend.deleteFromTable(tableName, pkVal)
    setTableScreen(tableName)


def addFkAction():
    pass


def modifyAction(popUpWindow, fieldsMaster, ddMenuOption: dict, tableName: str, pkVal, notInsertOrModify: bool,
                 savepoint: str, switchTable: bool, master, widgetToUpdate: tk.OptionMenu, widgetVar: tk.Variable):

    pkName = backend.getPkColumnName(tableName)
    tableNr = backend.getTableNumber(tableName)
    insertData = []
    # Get values for each column
    for colInfo in backend.tableInfo[tableNr][backend.COLUMNS]:
        # If value is not pk insert the value
        if colInfo[0] != pkName:

            # Get the value form corresponding widget
            infoWidget = fieldsMaster.children.get(colInfo[0].lower())
            # In case of dd menus you cannot set names
            if infoWidget is None:
                infoWidget = ddMenuOption.get(colInfo[0].lower())
                if infoWidget is not None:
                    rawVal = infoWidget.get().split(" ")[0]
                else:
                    rawVal = None

            else:
                rawVal = infoWidget.get()

        else:
            rawVal = pkVal if notInsertOrModify else None

        if rawVal == "NULL" or rawVal == "Select":
            rawVal = None

        # Convert rawVal to expected type
        if colInfo[1] == "VARCHAR" or colInfo[1] == "VARCHAR2" and rawVal is not None:
            insertData.append(rawVal)

        if colInfo[1] == "NUMBER" and rawVal is not None:
            try:
                insertData.append(float(rawVal))
            except:
                infoWidget.delete(0, tk.END)
                infoWidget.insert(0, "INSERT A NUMBER!")
                errorWindow("Numeric value expected!")
                return

        if colInfo[1] == "DATE" and rawVal is not None:
            dates = rawVal.split("-")
            if len(dates) != 3:
                print(infoWidget.get())
                infoWidget.delete(0, tk.END)
                infoWidget.insert(0, "INSERT A DATE!")
                errorWindow("Date value expected!")
                return
            try:
                insertData.append(datetime.datetime(year=int(dates[0]), month=int(dates[1]), day=int(dates[2])))
            except:
                infoWidget.delete(0, tk.END)
                infoWidget.insert(0, "INSERT A DATE!")
                errorWindow("Date value expected!")
                return

        if rawVal is None:
            insertData.append(None)

    # Insert/Modify value
    if notInsertOrModify:
        backend.modifyValueFromTable(tableName, pkVal, tuple(insertData))
    else:
        backend.insertIntoTable(tableName, tuple(insertData))

    # Update widget if needed (in case of fk inserts -> widget will always be OptionMenu)
    if widgetToUpdate is not None:
        # Get insert data
        optList = []
        # Get values from referenced table
        referencedVals = backend.getTableData(tableName)

        for valTuple in referencedVals:
            # Concat vals (first val will always be PK)
            refNr = backend.getTableNumber(tableName)
            if len(backend.tableInfo[refNr][backend.PK]) > 0:
                pkNr = backend.tableInfo[refNr][backend.PK][0]
            else:
                pkNr = -1

            tupleString = convertToPrintableString(valTuple[pkNr - 1]) + " "
            tupleNr = 0
            for val in valTuple:
                if tupleNr != pkNr - 1:
                    tupleString += convertToPrintableString(val) + " "
                tupleNr += 1

            optList.append(tupleString)

        # Add null option
        optList.append("NULL")

        widgetToUpdate['menu'].delete(0, 'end')
        for opt in optList:
            widgetToUpdate['menu'].add_command(label=opt, command=tk._setit(widgetVar, opt))

    try:
        if master is not None:
            master.deiconify()
        popUpWindow.destroy()
    except:
        pass

    backend.deteleSavepoint(savepoint)

    if switchTable:
        setTableScreen(tableName)


def modifyPopUp(tableName: str, pkVal, notInsertOrModify: bool, switchTable=True, master=None, menu=None, manuVar=None):
    # Get table info to create GUI
    tableNr = backend.getTableNumber(tableName)
    table = backend.tableInfo[tableNr]
    fkNewVals = {}
    modifyWindow = tk.Tk(className="modify" if notInsertOrModify else "insert")
    modifyWindow.geometry("500x400")
    modifyWindow.eval('tk::PlaceWindow . center')
    modifyWindow.resizable(False, False)

    # Create savepoint for transactions
    savepoint = backend.createSavepoint(tableName)

    # Hide master (if any)
    if master is not None:
        master.withdraw()

    # Create close function
    def closePopup():
        # Rollback
        backend.rollbackTo(savepoint)
        # Delete the savepoint
        backend.deteleSavepoint(savepoint)
        # Display master
        if master is not None:
            master.deiconify()
        # Close the window
        modifyWindow.destroy()

    # Bind function to X button
    modifyWindow.protocol('WM_DELETE_WINDOW', closePopup)

    # Modify label
    ttk.Label(modifyWindow, text="Modify values bellow" if notInsertOrModify else "Insert values bellow",
              font=font.Font(size=12, weight='bold')).grid(row=1, column=1, pady=15)

    # Value field
    canvas = tk.Canvas(modifyWindow, width=480, height=290)
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
        if len(table[backend.PK]) > 0 and valRow + 1 != table[backend.PK][0]:
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
                    if len(backend.tableInfo[refNr][backend.PK]) > 0:
                        pkNr = backend.tableInfo[refNr][backend.PK][0]
                    else:
                        pkNr = -1

                    tupleString = convertToPrintableString(valTuple[pkNr - 1]) + " "
                    tupleNr = 0
                    for val in valTuple:
                        if tupleNr != pkNr - 1:
                            tupleString += convertToPrintableString(val) + " "
                        tupleNr += 1

                    if notInsertOrModify and str(valTuple[pkNr - 1]) == str(oldVals[0][valRow]):
                        variable.set(tupleString)
                    optList.append(tupleString)

                # Add null option
                optList.append("NULL")

                # Create drop down menu
                drop = None
                if len(optList) > 0:
                    drop = tk.OptionMenu(valuesGrid, variable, *optList)
                    drop.grid(row=row, column=2)
                else:
                    variable.set("NULL")

                # Add insert new value for FK
                ttk.Button(valuesGrid, text="+", width=1,
                           command=lambda arg1=referencedTable, arg2=modifyWindow, arg3=drop, arg4=variable: modifyPopUp(arg1, None, False, False,
                                    master=arg2, menu=arg3, manuVar=arg4)) \
                    .grid(row=row, column=3)

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
               command=lambda: modifyAction(modifyWindow, valuesGrid,
                                            fkNewVals, tableName, pkVal,
                                            notInsertOrModify, savepoint, switchTable, master, menu, manuVar)) \
        .grid(row=4, column=1, pady=5)


def setTableScreen(tableName: str):
    global currPanel, mainWindow
    tableNr = backend.getTableNumber(tableName)
    pkCol = backend.tableInfo[tableNr][backend.PK][0] if len(backend.tableInfo[tableNr][backend.PK]) else -1
    nrCols = len(backend.tableInfo[tableNr][backend.COLUMNS])

    if currPanel is not None:
        # App closing error fix
        try:
            currPanel.destroy()
        except:
            backend.closeConnection()
            exit(0)

    currPanel = ttk.Frame(mainWindow)

    # Add table name
    tableLabel = ttk.Label(currPanel, text=tableName, font=font.Font(size=14, weight='bold'))
    tableLabel.grid(row=1, column=2, pady=30)

    # Create scrollable canvas
    canvas = tk.Canvas(currPanel, width=750, height=350)
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
                    command=lambda arg1=tableName, arg2=x: deleteAction(arg1, arg2)
                ).grid(column=nrCols + 2, row=i, padx=15)

                # Create modify button
                ttk.Button(
                    tableGrid, text="Modify",
                    command=lambda arg1=tableName, arg2=x: modifyPopUp(arg1, arg2, True)
                ).grid(column=nrCols + 1, row=i, padx=15)

            col += 1
        i += 1

    canvas.grid(row=2, column=2, padx=5)
    scrollbar1.grid(row=2, column=3, sticky="NS")
    scrollbar2.grid(row=3, column=2, sticky="EW")

    ttk.Button(
        currPanel, text="Insert new value",
        command=lambda arg=tableName: modifyPopUp(arg, None, False)
    ).grid(column=2, row=4, pady=30)

    currPanel.grid()


def clearLogAction():
    backend.clearLog()
    setErrorLogScreen()


def setErrorLogScreen():
    global currPanel, mainWindow

    if currPanel is not None:
        currPanel.grid_forget()

    currPanel = ttk.Frame(mainWindow)
    # Create scrollable canvas
    canvas = tk.Canvas(currPanel, width=770, height=530)
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

    ttk.Button(currPanel, text="Clear log", command=clearLogAction).grid(row=4, column=2, pady=10)

    currPanel.grid()


def savepointAction(popWindow):
    backend.createSavepoint(popWindow.children.get("savepointName").get())
    popWindow.destroy()


def savepointPopUp():
    savepointWindow = tk.Tk(className="Savepoint")
    savepointWindow.geometry("210x100")
    savepointWindow.eval('tk::PlaceWindow . center')
    savepointWindow.resizable(False, False)

    ttk.Entry(savepointWindow, name="savepointName", width=32).grid(row=2, pady=5, padx=5)
    ttk.Label(savepointWindow, text="\tInsert savepoint name").grid(row=1, sticky="EW", pady=5, padx=5)
    ttk.Button(savepointWindow, text="Create savepoint", command=lambda: savepointAction(savepointWindow)) \
        .grid(row=3, pady=5, padx=5)

    savepointWindow.mainloop()


def rollbackAction(window, var):
    backend.rollbackTo(var.get())
    setHomeScreen()
    window.destroy()


def rollbackPopUp():
    saveList = backend.savepointList
    if len(saveList) > 0:
        rollbackWindow = tk.Tk(className="Savepoint")
        rollbackWindow.geometry("210x110")
        rollbackWindow.eval('tk::PlaceWindow . center')
        rollbackWindow.resizable(False, False)

        var = tk.StringVar(rollbackWindow, value="Choose savepoint")

        tk.OptionMenu(rollbackWindow, var, saveList[0], *(saveList[1:])).grid(row=2, pady=5, padx=5)
        ttk.Label(rollbackWindow, text="Select desired savepoint").grid(row=1, pady=5, padx=40)
        ttk.Button(rollbackWindow, text="Rollback", command=lambda: rollbackAction(rollbackWindow, var)) \
            .grid(row=3, pady=5, padx=5)

        rollbackWindow.mainloop()


def executeAction(textWidget, canvas):
    canvas.delete("all")
    tableGrid = ttk.Frame(canvas)
    tableGrid.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    canvas.create_window((0, 0), window=tableGrid, anchor="nw")

    query = textWidget.get(1.0, tk.END)
    values = backend.executeQuery(query)

    i = 1
    for val in values:
        col = 1
        for x in val:
            ttk.Label(tableGrid, text=convertToPrintableString(x), font=font.Font(size=9)) \
                .grid(row=i, column=col, sticky="W", padx=15)
            col += 1
        i += 1

    canvas.grid(row=2, column=1)


def setTerminalScreen():
    global currPanel, mainWindow

    if currPanel is not None:
        # App closing error fix
        try:
            currPanel.destroy()
        except:
            backend.closeConnection()
            exit(0)

    currPanel = ttk.Frame(mainWindow)

    # Results label
    ttk.Label(currPanel, text="Results", font=font.Font(size=14, weight='bold')) \
        .grid(row=1, column=1, pady=20)

    # Create scrollable canvas
    canvas = tk.Canvas(currPanel, width=750, height=350)
    scrollbar1 = ttk.Scrollbar(currPanel, orient="vertical", command=canvas.yview)
    scrollbar2 = ttk.Scrollbar(currPanel, orient="horizontal", command=canvas.xview)

    canvas.configure(yscrollcommand=scrollbar1.set, xscrollcommand=scrollbar2.set)

    canvas.grid(row=2, column=1)
    scrollbar1.grid(row=2, column=2, sticky="NS")
    scrollbar2.grid(row=3, column=1, sticky="EW")

    # Add text widget
    text = tk.Text(currPanel, width=85, height=8)
    text.grid(row=4, column=1)

    # Add Execute button
    ttk.Button(currPanel, text="Execute", command=lambda: executeAction(text, canvas)).grid(row=5, column=1, pady=5)

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
            command=lambda e=table[backend.TABLE_NAME]: setTableScreen(e)
        )
    menubar.add_cascade(
        label="Tables",
        menu=tableMenu
    )

    # Create terminal option
    menubar.add_command(
        label="SQL Terminal",
        command=setTerminalScreen
    )

    # Add commit and rollback
    sessionMenu = tk.Menu(menubar, tearoff=0)
    sessionMenu.add_command(
        label="Rollback",
        command=rollbackPopUp
    )
    sessionMenu.add_command(
        label="Savepoint",
        command=savepointPopUp
    )
    sessionMenu.add_command(
        label="Commit",
        command=lambda: backend.executeQuery("COMMIT")
    )
    menubar.add_cascade(
        label="Session",
        menu=sessionMenu
    )

    # Add error log
    menubar.add_command(label="Error log", command=setErrorLogScreen)

    # Set panel
    setHomeScreen()


def runGui():
    if mainWindow is not None:
        mainWindow.mainloop()
