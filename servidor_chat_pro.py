# -*- coding: utf-8 -*-
"""
Servidor Chat Pro - Version con Gemini Integrado
Compatible con Windows 7/8/10/11

EJECUTAR:
    set GEMINI_API_KEY=tu_clave_aqui
    python servidor_chat_pro.py
"""

from flask import Flask, request, jsonify
from batalla import BatallaSistema
import sqlite3
import datetime
import random
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configuración de Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

app = Flask(__name__)

# ... (resto de las importaciones y configuraciones)
try:
    from archivos_server import registrar_rutas_archivos
    registrar_rutas_archivos(app)
    print("[OK] Modulo de archivos cargado")
except Exception as e:
    print("[WARN] Modulo archivos no disponible: " + str(e))

try:
    from agente_pc import registrar_rutas_pc
    registrar_rutas_pc(app)
    print("[OK] Modulo agente PC cargado")
except Exception as e:
    print("[WARN] Modulo agente PC no disponible: " + str(e))

batalla = None
# ===========================================================
# CONFIGURACION - Cambia estos valores facil
# ===========================================================
DB_FILE    = "chat.db"
PUERTO     = 5003
HOST       = "0.0.0.0"
SALDO_INIT = 100
RECOMPENSA = 1
MAX_CHARS  = 500
MAX_HIST   = 10
DEBUG      = True

# ... (resto del código igual hasta procesar_comando) ...
def conectar():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = conectar()
    c = conn.cursor()
    # (Tablas omitidas por brevedad, asumiendo que ya existen como en el original)
    conn.commit()
    conn.close()
    print("[DB] Base de datos lista: " + DB_FILE)

def crear_usuario_si_no_existe(conn, nombre):
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT OR IGNORE INTO usuarios(nombre, saldo, mensajes, creado, ultimo) VALUES(?,?,0,?,?)",
        (nombre, SALDO_INIT, ahora, ahora)
    )

def obtener_usuario(conn, nombre):
    row = conn.execute("SELECT * FROM usuarios WHERE nombre=?", (nombre,)).fetchone()
    if row:
        return dict(row)
    return None

def registrar_movimiento(conn, de_user, para_user, cantidad, tipo="transferencia"):
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO movimientos(de_user, para_user, cantidad, tipo, fecha) VALUES(?,?,?,?,?)",
        (de_user, para_user, cantidad, tipo, ahora)
    )

# ===========================================================
# PROCESADOR DE COMANDOS
# ===========================================================
def procesar_comando(msg, usuario, conn):
    # ... (Comandos existentes igual) ...
    # (Para no saturar, asumo que mantienes todos los if msg == ... del código original)
    # [Insertar aquí todos los if/elif de comandos del código original]
    
    # Si llega aquí, es un mensaje de chat normal, usar Gemini:
    if model:
        try:
            response = model.generate_content(msg)
            return response.text
        except Exception as e:
            return "Error con Gemini: " + str(e)
    
    return "Gemini no está configurado (falta API KEY)."

# ... (Resto de rutas de la API igual) ...

if __name__ == "__main__":
    print("Iniciando servidor en puerto 5003 con Gemini...")
    init_db()
    batalla = BatallaSistema(DB_FILE)
    app.run(host=HOST, port=PUERTO, debug=DEBUG)
