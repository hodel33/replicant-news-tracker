import sqlite3 as sql

class SQLiteDBManager:
    """A streamlined SQLite Database Context Manager that makes it easy to run SQL queries. The module includes an outer execute() function, allowing SQL commands to be run from other 
    modules via "import sql_mgr as sql". In practice, you can use sql.execute(db, query), where 'db' specifies the database and 'query' holds the SQL query string. Have fun! /hodel33 & dyaland
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
        # Returns the result of a SELECT query, or None if the query was an INSERT/UPDATE/DELETE command
        return self.cursor.fetchall()

def execute(filename:str, query:str):
    with SQLiteDBManager(filename) as sql:
        return(sql.execute_query(query))