from flask import Flask, request, jsonify
import sqlite3
import bcrypt

app = Flask(__name__)

DB_FILE = "integrado_database.db"

# Configuración BD
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (nombre TEXT, hash_password TEXT)")
    conn.commit()
    return conn

db = get_db()

@app.route('/registrar', methods=['POST'])
def registrar():
    data = request.json
    nombre = data.get('nombre')
    password = data.get('password').encode('utf-8')
    
    # Hashing (Seguridad en almacenamiento)
    hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
    
    cursor = db.cursor()
    cursor.execute("INSERT INTO usuarios VALUES (?, ?)", (nombre, hash_password))
    db.commit()
    return jsonify({"mensaje": "Usuario registrado de forma segura"})

@app.route('/buscar')
def buscar():
    nombre = request.args.get('nombre', '')
    # Consulta parametrizada (Seguridad contra SQLi)
    cursor = db.cursor()
    cursor.execute("SELECT nombre FROM usuarios WHERE nombre = ?", (nombre,))
    resultados = cursor.fetchall()
    return jsonify({"resultados": resultados})

if __name__ == '__main__':
    print("🚀 Servidor INTEGRADO iniciado en puerto 5000")
    app.run(port=5000)
