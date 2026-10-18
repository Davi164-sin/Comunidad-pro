import sqlite3

DB_PATH = "/root/asistente_project/database.db"

def enable_wal():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.close()
        print("✅ Modo WAL habilitado correctamente.")
    except Exception as e:
        print(f"❌ Error al habilitar WAL: {e}")

if __name__ == "__main__":
    enable_wal()
