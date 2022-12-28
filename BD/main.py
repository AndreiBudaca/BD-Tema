import backend
import frontend

if __name__ == "__main__":

    # Initialize connection to DB and get table information
    frontend.connectWindow()

    if frontend.dsn != "" and frontend.user != "" and frontend.password != "":
        backend.initSession(frontend.dsn, frontend.user, frontend.password)
        # backend.initSession("bd-dc.cs.tuiasi.ro:1539/orcl", "bd026", "bd026")

        # Initialize gui
        frontend.initGui()
        # Run
        frontend.runGui()
        # Close DB connection
        backend.closeConnection()
