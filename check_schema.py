import sqlite3

def check_schema(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("PRAGMA table_info(usuario)")
    columns = c.fetchall()
    for col in columns:
        print(col)
    conn.close()

check_schema("/root/database.db")
