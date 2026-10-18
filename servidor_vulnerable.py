from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Base de datos en memoria para el ejercicio
def get_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre TEXT, admin BOOLEAN)")
    cursor.execute("INSERT INTO usuarios (nombre, admin) VALUES ('david', 0), ('maria', 0), ('admin', 1)")
    conn.commit()
    return conn

db = get_db()

@app.route('/buscar_vulnerable')
def buscar_vulnerable():
    nombre = request.args.get('nombre', '')
    
    # --- VULNERABLE: CONCATENACIÓN DIRECTA ---
    # Un atacante puede cerrar la comilla y añadir comandos SQL
    query = f"SELECT nombre, admin FROM usuarios WHERE nombre = '{nombre}'"
    
    cursor = db.cursor()
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    return jsonify({"query_ejecutada": query, "resultados": resultados})

if __name__ == '__main__':
    print("🚀 Servidor VULNERABLE iniciado en puerto 5001")
    app.run(port=5001)
