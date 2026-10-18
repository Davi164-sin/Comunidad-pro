import sqlite3
import os

DB_PATH = "database.db"

def register_user(username, password, email):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO usuario (nombre,email,password,puntos,nivel) VALUES (?,?,?,0,'Iniciado')", (username,email,password))
        conn.commit()
        conn.close()
        print("Registration successful")
    except sqlite3.IntegrityError:
        print("User already exists")
    except Exception as e:
        print(f"Error: {e}")

register_user("testuser", "testpass", "test@example.com")

# Check if user exists
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT * FROM usuario WHERE nombre='testuser'")
user = c.fetchone()
print(f"User found: {user}")
conn.close()
