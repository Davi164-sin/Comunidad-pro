import sqlite3

def check_db(db_path):
    print(f"Checking {db_path}:")
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print(f"Tables: {tables}")
        if ('usuario',) in tables:
            c.execute("SELECT * FROM usuario")
            users = c.fetchall()
            print(f"Users: {users}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

check_db("database.db")
check_db("asistente_project/database.db")
