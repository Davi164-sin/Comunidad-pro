import os, sqlite3
from dotenv import load_dotenv

load_dotenv()

# Ruta absoluta en PythonAnywhere
DB_PATH = "/home/Achip/mysite/database.db"
# Cargar contraseña desde entorno
ADMIN_PASSWORD = os.environ.get('ADMIN_DEFAULT_PASSWORD', 'default_password_change_me')

def fix_user():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Base de datos no encontrada en {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Asegurarnos de que el usuario existe y poner contraseña conocida
        c.execute("UPDATE usuario SET password=?, es_admin=1 WHERE nombre='david_achipiz'", (ADMIN_PASSWORD,))
        
        if c.rowcount == 0:
            print("⚠️ Usuario 'david_achipiz' no encontrado, creándolo...")
            c.execute("INSERT INTO usuario (nombre, email, password, es_admin) VALUES (?, ?, ?, ?)", 
                      ('david_achipiz', 'admin@genesis.com', ADMIN_PASSWORD, 1))
        
        conn.commit()
        conn.close()
        print(f"✅ Usuario 'david_achipiz' configurado con privilegios de admin.")
    except Exception as e:
        print(f"❌ Error al configurar usuario: {e}")

if __name__ == "__main__":
    fix_user()
