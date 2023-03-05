import sqlite3 as sql


class SQLiteDBManager:
    """A simple & clean SQLite Database Context Manager which makes it possible to 
    import the class & outer function execute() into another module (for example main.py) 
    with the import statement "import sql_mgr as sql" and then you'll be able to write 
    sql.execute(query), where "query" is the actual SQL query.
    """

    def __init__(self, db_file_path:str):
        self.db_file = db_file_path
        
    def __enter__(self):
        self.connection = sql.connect(self.db_file)
        self.cursor = self.connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = True;") # enabling FOREIGN KEYS for SQLite 3
        return self
    
    def __exit__(self, exc_class, exc, traceback):
        try:
            self.connection.commit()
        except AttributeError: # isn't closable
            return True # exception handled successfully
        finally:
            self.cursor.close()
            self.connection.close()
     
    def execute_query(self, query:str):
        self.cursor.execute(query)
        return self.cursor.fetchall()  # cursor.fetchall object -> if SELECT (viewing data), None object if INSERT/UPDATE/DELETE (editing data)


def execute(filename:str, query:str):

    with SQLiteDBManager(filename) as sql:
        return(sql.execute_query(query))