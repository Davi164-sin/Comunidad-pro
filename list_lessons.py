import sqlite3
import os

DB_PATH = "asistente_project/database.db"

def list_lessons():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM lecciones")
    lessons = c.fetchall()
    for l in lessons:
        print(f"ID: {l['id']}, Modulo: {l['modulo']}, Titulo: {l['titulo']}, Premium: {l['es_premium']}")
    conn.close()

if __name__ == "__main__":
    list_lessons()
