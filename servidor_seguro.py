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

@app.route('/buscar_seguro')
def buscar_seguro():
    nombre = request.args.get('nombre', '')
    
    # --- SEGURO: CONSULTA PARAMETRIZADA ---
    # El motor SQL trata el parámetro como texto literal, no como código
    query = "SELECT nombre, admin FROM usuarios WHERE nombre = ?"
    
    cursor = db.cursor()
    cursor.execute(query, (nombre,))
    resultados = cursor.fetchall()
    
    return jsonify({"query_ejecutada": "SELECT nombre, admin FROM usuarios WHERE nombre = ?", "resultados": resultados})

if __name__ == '__main__':
    print("🚀 Servidor SEGURO iniciado en puerto 5002")
    app.run(port=5002)
