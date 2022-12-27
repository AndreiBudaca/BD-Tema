import backend
import frontend
import threading

if __name__ == "__main__":

    # Initialize connection to DB and get table information
    backend.initSesion("localhost/xe", "guiuser", "gui")
    # backend.initSesion("bd-dc.cs.tuiasi.ro:1539/orcl", "bd026", "bd026")

    # Initialize
    frontend.initGui()
    # Run
    frontend.runGui()
    # Close DB conection
    backend.closeConnection()