"""
╗██╗   ██╗██╗  ██╗
██╔════╝██║  ██║██╔══██╗╚══██╔══╝    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║   ██║╚██╗██╔╝
██║     ███████║███████║   ██║          ██║   █████╗  ██████╔╝██╔████╔██║██║   ██║ ╚███╔╝
██║     ██╔══██║██╔══██║   ██║          ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║   ██║ ██╔██╗
╚██████╗██║  ██║██║  ██║   ██║          ██║   ███████╗██║  ██║██║ ╚═╝ ██║╚██████╔╝██╔╝ ██╗
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝          ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝

CHAT TERMUX v2.0 — Control Remoto Seguro
=========================================
INSTALAR EN TERMUX:
    pip install requests cryptography

EJECUTAR:
    python chat_termux_v2.py

NUEVAS FUNCIONES:
  - Autenticación con PIN cifrado (PBKDF2 + AES)
  - Sesiones con token firmado (HMAC-SHA256)
  - Control del servidor (reiniciar, apagar, estado)
  - Control de la PC (bloquear, apagar, ejecutar comando)
  - Monitor en tiempo real (CPU, RAM, disco, red)
  - Logs de seguridad con alertas
  - Bloqueo automático tras intentos fallidos
  - Cifrado de mensajes sensibles (Fernet/AES-128)
"""

import requests
import threading
import time
import os
import sys
import datetime
import hashlib
import hmac
import json
import base64
import getpass
import platform
import re
# Nota: La siguiente importación requiere el archivo 'archivos_cliente.py'
# Si no lo tienes, debes comentarla o crear dicho módulo.
try:
    from archivos_cliente import enviar_archivo_interactivo, descargar_archivo, es_mensaje_archivo
except ImportError:
    # Definiciones dummy si no existe el archivo
    def enviar_archivo_interactivo(*args): print("Error: archivos_cliente.py no encontrado")
    def descargar_archivo(*args): print("Error: archivos_cliente.py no encontrado")
    def es_mensaje_archivo(*args): return False

# ---------------------------------------------------------------------------
# DEPENDENCIAS OPCIONALES
# ---------------------------------------------------------------------------
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

# ---------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------
SERVIDOR      = "http://192.168.0.102:5003"
INTERVALO     = 2
VERSION       = "2.0"
MAX_INTENTOS  = 3          # Intentos antes de bloqueo
BLOQUEO_SEG   = 60         # Segundos bloqueado tras fallo
TOKEN_EXPIRA  = 3600       # Segundos de validez del token
CLAVE_HMAC    = b"chat_termux_secret_2024"  # Cambiar en produccion

# Niveles de rol
ROL_USUARIO = 0
ROL_ADMIN   = 1
ROL_ROOT    = 2

ROL_NOMBRES = {ROL_USUARIO: "Usuario", ROL_ADMIN: "Admin", ROL_ROOT: "Root"}

# ---------------------------------------------------------------------------
# ESTADO DE SESION (en memoria, no se guarda en disco)
# ---------------------------------------------------------------------------
sesion = {
    "nombre": None,
    "token": None,
    "token_ts": 0,
    "rol": ROL_USUARIO,
    "intentos_fallidos": 0,
    "bloqueado_hasta": 0,
    "clave_cifrado": None,   # Fernet key para mensajes cifrados
    "mensajes_cifrados": False,
}

# ---------------------------------------------------------------------------
# COLORES
# ---------------------------------------------------------------------------
class C:
    MORADO  = '\033[95m'
    AZUL    = '\033[94m'
    CIAN    = '\033[96m'
    VERDE   = '\033[92m'
    AMARILLO= '\033[93m'
    ROJO    = '\033[91m'
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    DIM     = '\033[2m'
    GRIS    = '\033[90m'
    NARANJA = '\033[38;5;208m'
    SUBRAY  = '\033[4m'

def limpiar():
    os.system("clear")

def separador(car="═", largo=50, color=C.MORADO):
    print(color + car * largo + C.RESET)

def titulo(texto, color=C.MORADO):
    separador()
    print(color + C.BOLD + f"  {texto}" + C.RESET)
    separador()

def ok(msg):    print(C.VERDE   + "  ✔ " + msg + C.RESET)
def err(msg):   print(C.ROJO    + "  ✖ " + msg + C.RESET)
def warn(msg):  print(C.AMARILLO+ "  ⚠ " + msg + C.RESET)
def info(msg):  print(C.CIAN    + "  ℹ " + msg + C.RESET)
def dim(msg):   print(C.GRIS    + "  " + msg + C.RESET)

# ---------------------------------------------------------------------------
# SEGURIDAD — TOKENS Y CIFRADO
# ---------------------------------------------------------------------------

def generar_token(nombre: str, rol: int) -> str:
    """HMAC-SHA256 sobre nombre+rol+timestamp."""
    ts = int(time.time())
    payload = f"{nombre}:{rol}:{ts}"
    firma = hmac.new(CLAVE_HMAC, payload.encode(), hashlib.sha256).hexdigest()
    token_raw = f"{payload}:{firma}"
    return base64.b64encode(token_raw.encode()).decode()

def validar_token(token: str):
    """Devuelve {nombre, rol, ts} si el token es válido y no expiró."""
    try:
        raw = base64.b64decode(token.encode()).decode()
        partes = raw.rsplit(":", 1)
        if len(partes) != 2:
            return None
        payload, firma_recibida = partes
        firma_esperada = hmac.new(CLAVE_HMAC, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(firma_recibida, firma_esperada):
            return None
        nombre, rol_str, ts_str = payload.split(":")
        ts = int(ts_str)
        if time.time() - ts > TOKEN_EXPIRA:
            return None
        return {"nombre": nombre, "rol": int(rol_str), "ts": ts}
    except Exception:
        return None

def hash_pin(pin: str, salt: bytes = None):
    """PBKDF2-HMAC-SHA256 del PIN. Devuelve (hash_hex, salt_hex)."""
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000)
    return dk.hex(), salt.hex()

def verificar_pin(pin: str, hash_guardado: str, salt_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    dk, _ = hash_pin(pin, salt)
    return hmac.compare_digest(dk, hash_guardado)

def derivar_clave_fernet(pin: str, salt: bytes = None):
    """Deriva una clave Fernet desde el PIN (solo si cryptography está instalado)."""
    if not CRYPTO_OK:
        return None, None
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000)
    clave = base64.urlsafe_b64encode(kdf.derive(pin.encode()))
    return Fernet(clave), salt

def cifrar_msg(texto: str) -> str:
    """Cifra un mensaje si hay clave activa, si no lo devuelve tal cual."""
    if sesion["clave_cifrado"] and sesion["mensajes_cifrados"]:
        try:
            token = sesion["clave_cifrado"].encrypt(texto.encode())
            return "🔒" + base64.b64encode(token).decode()
        except Exception:
            pass
    return texto

def descifrar_msg(texto: str) -> str:
    """Intenta descifrar si empieza con 🔒."""
    if texto.startswith("🔒") and sesion["clave_cifrado"]:
        try:
            raw = base64.b64decode(texto[1:].encode())
            return sesion["clave_cifrado"].decrypt(raw).decode()
        except Exception:
            return texto + " [no se pudo descifrar]"
    return texto

def esta_bloqueado() -> bool:
    if sesion["bloqueado_hasta"] > time.time():
        restante = int(sesion["bloqueado_hasta"] - time.time())
        err(f"Cuenta bloqueada. Espera {restante}s.")
        return True
    return False

def registrar_intento_fallido():
    sesion["intentos_fallidos"] += 1
    if sesion["intentos_fallidos"] >= MAX_INTENTOS:
        sesion["bloqueado_hasta"] = time.time() + BLOQUEO_SEG
        err(f"Demasiados intentos. Bloqueado por {BLOQUEO_SEG}s.")
        log_seguridad("BLOQUEO", "Cuenta bloqueada por intentos fallidos")
    else:
        restantes = MAX_INTENTOS - sesion["intentos_fallidos"]
        warn(f"PIN incorrecto. Intentos restantes: {restantes}")

def log_seguridad(evento: str, detalle: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{ts}] [{evento}] {detalle}\n"
    try:
        with open("chat_security.log", "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# RED — Funciones base con token automático
# ---------------------------------------------------------------------------

def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if sesion["token"]:
        h["X-Auth-Token"] = sesion["token"]
    return h

def _get(ruta: str, params: dict = None):
    try:
        r = requests.get(SERVIDOR + ruta, params=params, headers=_headers(), timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def _post(ruta: str, data: dict = None):
    try:
        r = requests.post(SERVIDOR + ruta, json=data or {}, headers=_headers(), timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------------------------
# RED — Chat
# ---------------------------------------------------------------------------

def obtener_mensajes(yo, otro, limite=20):
    data = _get("/leer", {"yo": yo, "otro": otro, "limite": limite})
    msgs = data.get("mensajes", [])
    # Descifrar mensajes entrantes
    for m in msgs:
        m["msg"] = descifrar_msg(m["msg"])
    return msgs if "error" not in data else None

def enviar_mensaje(yo, otro, msg):
    msg_cifrado = cifrar_msg(msg)
    return _post("/enviar", {"de": yo, "para": otro, "msg": msg_cifrado})

def obtener_usuarios():
    return _get("/usuarios").get("usuarios", [])

def obtener_stats():
    return _get("/stats")

# ---------------------------------------------------------------------------
# RED — Control del Servidor (requiere admin en el servidor)
# ---------------------------------------------------------------------------

def servidor_reiniciar():
    return _post("/admin/reiniciar")

def servidor_apagar():
    return _post("/admin/apagar")

def servidor_estado():
    return _get("/admin/estado")

def servidor_logs(lineas=50):
    return _get("/admin/logs", {"lineas": lineas})

def servidor_ban(usuario):
    return _post("/admin/ban", {"usuario": usuario})

def servidor_unban(usuario):
    return _post("/admin/unban", {"usuario": usuario})

def servidor_borrar_mensajes(usuario=None):
    return _post("/admin/borrar_mensajes", {"usuario": usuario})

def servidor_config_get():
    return _get("/admin/config")

def servidor_config_set(clave, valor):
    return _post("/admin/config", {"clave": clave, "valor": valor})

# ---------------------------------------------------------------------------
# RED — Control de la PC (requiere módulo agente en el PC)
# ---------------------------------------------------------------------------

def pc_estado():
    return _get("/pc/estado")

def pc_ejecutar(cmd):
    """Ejecuta comando en el PC. El servidor valida la lista blanca de comandos."""
    return _post("/pc/ejecutar", {"cmd": cmd})

def pc_apagar(delay=60):
    return _post("/pc/apagar", {"delay": delay})

def pc_reiniciar(delay=60):
    return _post("/pc/reiniciar", {"delay": delay})

def pc_bloquear():
    return _post("/pc/bloquear")

def pc_screenshot():
    return _get("/pc/screenshot")

def pc_volumen(nivel):
    return _post("/pc/volumen", {"nivel": nivel})

def pc_abrir_app(app):
    return _post("/pc/abrir", {"app": app})

def pc_procesos():
    return _get("/pc/procesos")

def pc_matar_proceso(pid):
    return _post("/pc/matar", {"pid": pid})

# ---------------------------------------------------------------------------
# AUTENTICACION LOCAL (PIN)
# ---------------------------------------------------------------------------

# Credenciales de demo hardcodeadas (en producción van en servidor cifrado)
# Formato: { nombre: { "hash": ..., "salt": ..., "rol": ... } }
_CREDENCIALES_DEMO = {}

def _crear_usuario_demo(nombre, pin, rol=ROL_USUARIO):
    h, s = hash_pin(pin)
    _CREDENCIALES_DEMO[nombre] = {"hash": h, "salt": s, "rol": rol}

# Usuarios de ejemplo — CAMBIAR EN PRODUCCION
_crear_usuario_demo("admin", "1234", ROL_ADMIN)
_crear_usuario_demo("root",  "0000", ROL_ROOT)

def login_local(nombre: str, pin: str) -> bool:
    """Verifica credenciales locales y crea sesión si son correctas."""
    if esta_bloqueado():
        return False

    cred = _CREDENCIALES_DEMO.get(nombre.lower())
    # Si el usuario no tiene credenciales locales, se permite con ROL_USUARIO (solo chat)
    if cred is None:
        sesion["nombre"] = nombre.lower()
        sesion["rol"]    = ROL_USUARIO
        sesion["token"]  = generar_token(nombre, ROL_USUARIO)
        sesion["token_ts"] = time.time()
        sesion["intentos_fallidos"] = 0
        log_seguridad("LOGIN_OK", f"Usuario sin privilegios: {nombre}")
        return True

    if not verificar_pin(pin, cred["hash"], cred["salt"]):
        registrar_intento_fallido()
        log_seguridad("LOGIN_FAIL", f"PIN incorrecto para: {nombre}")
        return False

    sesion["nombre"] = nombre.lower()
    sesion["rol"]    = cred["rol"]
    sesion["token"]  = generar_token(nombre, cred["rol"])
    sesion["token_ts"] = time.time()
    sesion["intentos_fallidos"] = 0

    # Derivar clave de cifrado desde el PIN
    if CRYPTO_OK:
        fernet, salt = derivar_clave_fernet(pin)
        sesion["clave_cifrado"] = fernet
        info("Clave de cifrado E2E derivada del PIN.")

    log_seguridad("LOGIN_OK", f"Login exitoso: {nombre} rol={ROL_NOMBRES[cred['rol']]}")
    return True

def requiere_rol(rol_minimo: int) -> bool:
    if sesion["rol"] < rol_minimo:
        err(f"Permisos insuficientes. Se necesita: {ROL_NOMBRES[rol_minimo]}")
        return False
    return True

# ---------------------------------------------------------------------------
# PANTALLA DE LOGIN
# ---------------------------------------------------------------------------

def pantalla_login() -> bool:
    limpiar()
    separador("▓", 50, C.MORADO)
    print(C.BOLD + C.MORADO + """
  ██████╗██╗  ██╗ █████╗ ████████╗
  ██╔════╝██║  ██║██╔══██╗╚══██╔══╝
  ██║     ███████║███████║   ██║
  ██║     ██╔══██║██╔══██║   ██║
  ╚██████╗██║  ██║██║  ██║   ██║
   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝""" + C.RESET)
    print(C.GRIS + f"  TERMUX v{VERSION} — Acceso Seguro" + C.RESET)
    separador("▓", 50, C.MORADO)
    print()

    nombre = input(C.BOLD + "  Usuario: " + C.RESET).strip().lower()
    if not nombre:
        err("Nombre vacío.")
        return False

    # Solo pedir PIN si el usuario tiene credenciales locales
    if nombre in _CREDENCIALES_DEMO:
        pin = getpass.getpass(C.BOLD + "  PIN (oculto): " + C.RESET)
    else:
        pin = ""

    print()
    if login_local(nombre, pin):
        ok(f"Bienvenido, {nombre.upper()} [{ROL_NOMBRES[sesion['rol']]}]")
        if not CRYPTO_OK:
            warn("'cryptography' no instalado. Mensajes sin E2E.")
            warn("Ejecuta: pip install cryptography")
        time.sleep(1)
        return True
    else:
        err("Autenticación fallida.")
        time.sleep(2)
        return False

# ---------------------------------------------------------------------------
# MOSTRAR MENSAJES
# ---------------------------------------------------------------------------

def mostrar_mensajes_iniciales(mensajes, yo):
    inicio = max(0, len(mensajes) - 15)
    for m in mensajes[inicio:]:
        _print_msg(m, yo)

def _print_msg(m, yo):
    hora = m.get("fecha", "")[-8:-3] if m.get("fecha") else "--:--"
    lock = "🔒 " if m["msg"].startswith("🔒") else ""
    texto = descifrar_msg(m["msg"])
    if m["de"] == yo:
        print(C.AZUL + C.BOLD + "  Tú" + C.RESET +
              C.GRIS + f" [{hora}]" + C.RESET + ": " + texto)
    elif any(t in m["de"] for t in ["_monitor", "_scanner", "_bot"]):
        print(C.AMARILLO + f"  🤖 [{hora}]: " + texto[:80] + C.RESET)
    else:
        print(C.VERDE + C.BOLD + f"  {m['de']}" + C.RESET +
              C.GRIS + f" [{hora}]" + C.RESET + ": " + lock + texto)

# ---------------------------------------------------------------------------
# MENÚ — CONTROL DEL SERVIDOR
# ---------------------------------------------------------------------------

def menu_servidor():
    while True:
        limpiar()
        titulo("CONTROL DEL SERVIDOR", C.NARANJA)
        print(f"  {C.BOLD}Estado del servidor{C.RESET}")
        print()
        print("  1. Ver estado general")
        print("  2. Ver logs del servidor")
        print("  3. Reiniciar servidor")
        print("  4. Apagar servidor")
        print()
        print(f"  {C.BOLD}Usuarios{C.RESET}")
        print("  5. Banear usuario")
        print("  6. Desbanear usuario")
        print("  7. Borrar mensajes de usuario")
        print()
        print(f"  {C.BOLD}Configuración{C.RESET}")
        print("  8. Ver configuración")
        print("  9. Cambiar valor de config")
        print()
        print("  0. Volver")
        separador()
        op = input("  Opción: ").strip()

        if op == "0":
            break

        elif op == "1":
            limpiar(); titulo("ESTADO DEL SERVIDOR", C.NARANJA)
            data = servidor_estado()
            if "error" in data:
                err(data["error"])
            else:
                for k, v in data.items():
                    print(f"  {C.BOLD}{k:<20}{C.RESET} {v}")

        elif op == "2":
            limpiar(); titulo("LOGS DEL SERVIDOR", C.NARANJA)
            n = input("  Cuántas líneas? [50]: ").strip() or "50"
            data = servidor_logs(int(n))
            logs = data.get("logs", [])
            for l in logs:
                print(C.GRIS + "  " + l + C.RESET)

        elif op == "3":
            if not requiere_rol(ROL_ADMIN): pass
            else:
                conf = input(C.ROJO + "  ¿Reiniciar servidor? (si/no): " + C.RESET)
                if conf.lower() == "si":
                    r = servidor_reiniciar()
                    ok(str(r)) if "error" not in r else err(str(r))
                    log_seguridad("SERVIDOR_REINICIAR", f"Por: {sesion['nombre']}")

        elif op == "4":
            if not requiere_rol(ROL_ADMIN): pass
            else:
                conf = input(C.ROJO + "  ¿APAGAR servidor? (si/no): " + C.RESET)
                if conf.lower() == "si":
                    r = servidor_apagar()
                    ok(str(r)) if "error" not in r else err(str(r))
                    log_seguridad("SERVIDOR_APAGAR", f"Por: {sesion['nombre']}")

        elif op == "5":
            if not requiere_rol(ROL_ADMIN): pass
            else:
                u = input("  Usuario a banear: ").strip()
                r = servidor_ban(u)
                ok(str(r)) if "error" not in r else err(str(r))
                log_seguridad("BAN", f"{u} baneado por {sesion['nombre']}")

        elif op == "6":
            if not requiere_rol(ROL_ADMIN): pass
            else:
                u = input("  Usuario a desbanear: ").strip()
                r = servidor_unban(u)
                ok(str(r)) if "error" not in r else err(str(r))

        elif op == "7":
            if not requiere_rol(ROL_ADMIN): pass
            else:
                u = input("  Usuario (vacío = todos): ").strip() or None
                conf = input(C.ROJO + f"  ¿Borrar mensajes de '{u or 'todos'}'? (si/no): " + C.RESET)
                if conf.lower() == "si":
                    r = servidor_borrar_mensajes(u)
                    ok(str(r)) if "error" not in r else err(str(r))
                    log_seguridad("BORRAR_MSGS", f"Usuario: {u} por {sesion['nombre']}")

        elif op == "8":
            limpiar(); titulo("CONFIGURACIÓN DEL SERVIDOR", C.NARANJA)
            data = servidor_config_get()
            if "error" in data:
                err(data["error"])
            else:
                for k, v in data.items():
                    print(f"  {C.BOLD}{k:<25}{C.RESET} {v}")

        elif op == "9":
            if not requiere_rol(ROL_ADMIN): pass
            else:
                clave = input("  Clave de config: ").strip()
                valor = input("  Nuevo valor: ").strip()
                r = servidor_config_set(clave, valor)
                ok(str(r)) if "error" not in r else err(str(r))

        input("\n  Enter para continuar...")

# ---------------------------------------------------------------------------
# MENÚ — CONTROL DE LA PC
# ---------------------------------------------------------------------------

def menu_pc():
    while True:
        limpiar()
        titulo("CONTROL DE LA PC", C.CIAN)
        print(f"  {C.BOLD}Monitoreo{C.RESET}")
        print("  1. Estado del sistema (CPU/RAM/Disco)")
        print("  2. Lista de procesos")
        print("  3. Captura de pantalla")
        print()
        print(f"  {C.BOLD}Control de energía{C.RESET}")
        print("  4. Apagar PC")
        print("  5. Reiniciar PC")
        print("  6. Bloquear pantalla")
        print()
        print(f"  {C.BOLD}Acciones{C.RESET}")
        print("  7. Ejecutar comando")
        print("  8. Abrir aplicación")
        print("  9. Controlar volumen")
        print(" 10. Matar proceso por PID")
        print()
        print("  0. Volver")
        separador()
        op = input("  Opción: ").strip()

        if op == "0":
            break

        elif op == "1":
            limpiar(); titulo("ESTADO DEL SISTEMA", C.CIAN)
            data = pc_estado()
            if "error" in data:
                err(data["error"])
            else:
                cpu  = data.get("cpu_percent", "?")
                ram  = data.get("ram_percent", "?")
                ram_gb = data.get("ram_usado_gb", "?")
                disco = data.get("disco_percent", "?")
                temp  = data.get("cpu_temp_c", "N/A")
                red_s = data.get("red_enviado_mb", "?")
                red_r = data.get("red_recibido_mb", "?")
                uptime = data.get("uptime_horas", "?")

                def barra(pct, largo=20):
                    try:
                        lleno = int(float(pct) * largo / 100)
                        color = C.VERDE if float(pct) < 70 else (C.AMARILLO if float(pct) < 90 else C.ROJO)
                        return color + "█" * lleno + C.DIM + "░" * (largo - lleno) + C.RESET + f" {pct}%"
                    except:
                        return str(pct)

                print(f"\n  {'CPU':<12} {barra(cpu)}")
                print(f"  {'RAM':<12} {barra(ram)}  ({ram_gb} GB)")
                print(f"  {'Disco':<12} {barra(disco)}")
                print(f"  {'Temperatura':<12} {temp}°C")
                print(f"  {'Red ↑':<12} {red_s} MB")
                print(f"  {'Red ↓':<12} {red_r} MB")
                print(f"  {'Uptime':<12} {uptime} h")

        elif op == "2":
            limpiar(); titulo("PROCESOS ACTIVOS", C.CIAN)
            data = pc_procesos()
            procs = data.get("procesos", [])
            if procs:
                print(f"  {C.BOLD}{'PID':<8} {'NOMBRE':<25} {'CPU%':<8} {'RAM%'}{C.RESET}")
                separador("-", 50, C.GRIS)
                for p in procs[:25]:
                    print(f"  {p.get('pid','?'):<8} {p.get('nombre','?')[:24]:<25} "
                          f"{p.get('cpu','?'):<8} {p.get('ram','?')}")
            else:
                err("No se pudo obtener lista de procesos")

        elif op == "3":
            limpiar(); titulo("CAPTURA DE PANTALLA", C.CIAN)
            if not requiere_rol(ROL_ADMIN): pass
            else:
                data = pc_screenshot()
                if "url" in data:
                    info("Screenshot disponible en: " + data["url"])
                elif "base64" in data:
                    path = "/sdcard/screenshot_pc.jpg"
                    try:
                        with open(path, "wb") as f:
                            f.write(base64.b64decode(data["base64"]))
                        ok(f"Guardado en {path}")
                    except Exception as e:
                        err(str(e))
                else:
                    err(str(data))

        elif op == "4":
            if not requiere_rol(ROL_ROOT): pass
            else:
                delay = input("  Delay en segundos [60]: ").strip() or "60"
                conf  = input(C.ROJO + f"  ¿APAGAR PC en {delay}s? (si/no): " + C.RESET)
                if conf.lower() == "si":
                    r = pc_apagar(int(delay))
                    ok(str(r)) if "error" not in r else err(str(r))
                    log_seguridad("PC_APAGAR", f"Por: {sesion['nombre']} delay={delay}s")

        elif op == "5":
            if not requiere_rol(ROL_ROOT): pass
            else:
                delay = input("  Delay en segundos [60]: ").strip() or "60"
                conf  = input(C.ROJO + f"  ¿REINICIAR PC en {delay}s? (si/no): " + C.RESET)
                if conf.lower() == "si":
                    r = pc_reiniciar(int(delay))
                    ok(str(r)) if "error" not in r else err(str(r))
                    log_seguridad("PC_REINICIAR", f"Por: {sesion['nombre']}")

        elif op == "6":
            if not requiere_rol(ROL_ADMIN): pass
            else:
                r = pc_bloquear()
                ok("Pantalla bloqueada.") if "error" not in r else err(str(r))
                log_seguridad("PC_BLOQUEAR", f"Por: {sesion['nombre']}")

        elif op == "7":
            if not requiere_rol(ROL_ADMIN): pass
            else:
                warn("Solo comandos de la lista blanca del servidor serán ejecutados.")
                cmd = input("  Comando: ").strip()
                if cmd:
                    conf = input(C.ROJO + f"  ¿Ejecutar '{cmd}'? (si/no): " + C.RESET)
                    if conf.lower() == "si":
                        r = pc_ejecutar(cmd)
                        if "salida" in r:
                            print(C.CIAN + r["salida"] + C.RESET)
                        else:
                            err(str(r))
                        log_seguridad("PC_CMD", f"'{cmd}' por {sesion['nombre']}")

        elif op == "8":
            app = input("  Nombre de la app (ej: notepad, chrome): ").strip()
            if app:
                r = pc_abrir_app(app)
                ok(str(r)) if "error" not in r else err(str(r))

        elif op == "9":
            nivel = input("  Nivel de volumen (0-100): ").strip()
            try:
                nivel = max(0, min(100, int(nivel)))
                r = pc_volumen(nivel)
                ok(f"Volumen → {nivel}%") if "error" not in r else err(str(r))
            except ValueError:
                err("Nivel inválido")

        elif op == "10":
            if not requiere_rol(ROL_ADMIN): pass
            else:
                pid = input("  PID del proceso: ").strip()
                conf = input(C.ROJO + f"  ¿Matar proceso {pid}? (si/no): " + C.RESET)
                if conf.lower() == "si":
                    r = pc_matar_proceso(int(pid))
                    ok(str(r)) if "error" not in r else err(str(r))
                    log_seguridad("PC_KILL", f"PID={pid} por {sesion['nombre']}")

        input("\n  Enter para continuar...")

# ---------------------------------------------------------------------------
# MENÚ — SEGURIDAD
# ---------------------------------------------------------------------------

def menu_seguridad():
    while True:
        limpiar()
        titulo("SEGURIDAD Y PRIVACIDAD", C.ROJO)
        cifrado_estado = C.VERDE + "ACTIVO" if sesion["mensajes_cifrados"] else C.GRIS + "INACTIVO"
        print(f"  Cifrado E2E : {cifrado_estado}{C.RESET}")
        print(f"  Tu rol      : {C.BOLD}{ROL_NOMBRES[sesion['rol']]}{C.RESET}")
        print(f"  Token válido: ", end="")
        if sesion["token"]:
            restante = int(TOKEN_EXPIRA - (time.time() - sesion["token_ts"]))
            print(C.VERDE + f"SÍ ({restante}s restantes)" + C.RESET)
        else:
            print(C.ROJO + "NO" + C.RESET)
        print()
        print("  1. Activar/Desactivar cifrado E2E de mensajes")
        print("  2. Renovar token de sesión")
        print("  3. Ver log de seguridad local")
        print("  4. Cerrar sesión")
        print("  5. Información sobre seguridad")
        print()
        print("  0. Volver")
        separador()
        op = input("  Opción: ").strip()

        if op == "0":
            break

        elif op == "1":
            if not CRYPTO_OK:
                err("Instala: pip install cryptography")
            elif not sesion["clave_cifrado"]:
                err("No hay clave de cifrado (inicia sesión con usuario admin).")
            else:
                sesion["mensajes_cifrados"] = not sesion["mensajes_cifrados"]
                estado = "ACTIVADO" if sesion["mensajes_cifrados"] else "DESACTIVADO"
                ok(f"Cifrado E2E {estado}")
                log_seguridad("E2E", estado)

        elif op == "2":
            sesion["token"] = generar_token(sesion["nombre"], sesion["rol"])
            sesion["token_ts"] = time.time()
            ok("Token renovado por 1 hora más.")
            log_seguridad("TOKEN_RENOVADO", f"Por: {sesion['nombre']}")

        elif op == "3":
            limpiar(); titulo("LOG DE SEGURIDAD LOCAL", C.ROJO)
            try:
                with open("chat_security.log", "r", encoding="utf-8") as f:
                    lineas = f.readlines()
                for l in lineas[-30:]:
                    print(C.GRIS + "  " + l.rstrip() + C.RESET)
            except FileNotFoundError:
                info("Sin registros aún.")

        elif op == "4":
            conf = input(C.ROJO + "  ¿Cerrar sesión? (si/no): " + C.RESET)
            if conf.lower() == "si":
                log_seguridad("LOGOUT", f"Usuario: {sesion['nombre']}")
                sesion.update({"nombre": None, "token": None, "rol": ROL_USUARIO,
                               "clave_cifrado": None, "mensajes_cifrados": False})
                ok("Sesión cerrada.")
                time.sleep(1)
                return "logout"

        elif op == "5":
            limpiar(); titulo("INFORMACIÓN DE SEGURIDAD", C.ROJO)
            info("Autenticación : PBKDF2-HMAC-SHA256 (200k iteraciones)")
            info("Tokens        : HMAC-SHA256, expiran en 1h")
            info("Cifrado E2E   : AES-128 Fernet (derivado del PIN)")
            info("Bloqueo       : tras 3 intentos fallidos, 60s")
            info("Logs          : chat_security.log (local)")
            warn("El cifrado E2E solo funciona si ambos usuarios tienen")
            warn("la misma clave (mismo PIN). Para grupos, usar clave compartida.")
            if not CRYPTO_OK:
                err("cryptography no instalado — sin E2E disponible")
                err("Instala con: pip install cryptography")

        input("\n  Enter para continuar...")

# ---------------------------------------------------------------------------
# MONITOR EN TIEMPO REAL
# ---------------------------------------------------------------------------

def monitor_tiempo_real():
    if not requiere_rol(ROL_ADMIN):
        input("  Enter...")
        return

    limpiar()
    titulo("MONITOR EN TIEMPO REAL — Ctrl+C para salir", C.NARANJA)
    try:
        while True:
            data = pc_estado()
            if "error" not in data:
                # Mover cursor al inicio (sin limpiar completamente)
                print("\033[H\033[J", end="")
                titulo("MONITOR EN TIEMPO REAL — Ctrl+C para salir", C.NARANJA)
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"  {C.GRIS}Actualización: {ts}{C.RESET}\n")

                def barra(pct, largo=25):
                    try:
                        v = float(pct)
                        lleno = int(v * largo / 100)
                        color = C.VERDE if v < 60 else (C.AMARILLO if v < 85 else C.ROJO)
                        return color + "█" * lleno + C.GRIS + "░" * (largo-lleno) + C.RESET
                    except:
                        return "?"

                cpu = data.get("cpu_percent", 0)
                ram = data.get("ram_percent", 0)
                dis = data.get("disco_percent", 0)
                print(f"  CPU   [{barra(cpu)}] {cpu}%")
                print(f"  RAM   [{barra(ram)}] {ram}%  ({data.get('ram_usado_gb','?')} GB)")
                print(f"  DISCO [{barra(dis)}] {dis}%")
                print(f"\n  Temp    : {data.get('cpu_temp_c','N/A')}°C")
                print(f"  Red ↑   : {data.get('red_enviado_mb','?')} MB")
                print(f"  Red ↓   : {data.get('red_recibido_mb','?')} MB")
                print(f"  Uptime  : {data.get('uptime_horas','?')} h")
            time.sleep(3)
    except KeyboardInterrupt:
        pass

# ---------------------------------------------------------------------------
# MODO CHAT
# ---------------------------------------------------------------------------

def modo_chat(yo, otro):
    limpiar()
    print(C.VERDE + f"  Cargando chat con {otro}..." + C.RESET)

    mensajes = obtener_mensajes(yo, otro, 50)
    if mensajes is None:
        err("No se pudo conectar al servidor.")
        input("  Enter para volver...")
        return

    ultimo_conteo = [len(mensajes)]
    corriendo      = [True]

    limpiar()
    # Header
    separador("═", 50, C.MORADO)
    cifrado = "🔒 E2E" if sesion["mensajes_cifrados"] else "🔓 Sin cifrar"
    print(C.BOLD + f"  CHAT: {yo.upper()} → {otro.upper()}  {C.GRIS}{cifrado}{C.RESET}")
    print(C.GRIS + f"  Servidor: {SERVIDOR}" + C.RESET)
    separador("═", 50, C.MORADO)

    mostrar_mensajes_iniciales(mensajes, yo)

    if not mensajes:
        dim("Sin mensajes aún. Escribe algo!")

    separador("-", 50, C.GRIS)
    print(C.GRIS + "  'salir' para volver  |  '/cifrar' toggle E2E  |  '/limpiar' para limpiar" + C.RESET)
    separador("-", 50, C.GRIS)

    # Hilo de polling
    def revisar_nuevos():
        while corriendo[0]:
            time.sleep(INTERVALO)
            if not corriendo[0]:
                break
            try:
                msgs = obtener_mensajes(yo, otro, 100)
                if msgs and len(msgs) > ultimo_conteo[0]:
                    for m in msgs[ultimo_conteo[0]:]:
                        if m["de"] != yo:
                            _print_msg(m, yo)
                    ultimo_conteo[0] = len(msgs)
            except Exception:
                pass

    hilo = threading.Thread(target=revisar_nuevos, daemon=True)
    hilo.start()

    while True:
        try:
            msg = input("  Tú: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not msg:
            continue

        # Comandos internos del cliente
        if msg.lower() in ["salir", "exit", "quit", "q"]:
            corriendo[0] = False
            break

        if msg.lower() == "/cifrar":
            if CRYPTO_OK and sesion["clave_cifrado"]:
                sesion["mensajes_cifrados"] = not sesion["mensajes_cifrados"]
                estado = "🔒 ACTIVADO" if sesion["mensajes_cifrados"] else "🔓 DESACTIVADO"
                print(C.AMARILLO + f"  Cifrado E2E {estado}" + C.RESET)
            else:
                warn("Sin clave de cifrado. Inicia como admin.")
            continue

        if msg.lower() == "/limpiar":
            limpiar()
            mostrar_mensajes_iniciales(
                obtener_mensajes(yo, otro, 15) or [], yo)
            continue

        # Mostrar mensaje propio
        hora = datetime.datetime.now().strftime("%H:%M")
        lock = "🔒 " if sesion["mensajes_cifrados"] else ""
        print(C.AZUL + C.BOLD + "  Tú" + C.RESET +
              C.GRIS + f" [{hora}]" + C.RESET + ": " + lock + msg)

        # Enviar en hilo separado
        def _enviar(m=msg):
            data = enviar_mensaje(yo, otro, m)
            if "respuesta" in data:
                print(C.AMARILLO + "  🤖 Bot: " + data["respuesta"] + C.RESET)
            elif "error" in data:
                print(C.ROJO + "  ✖ Error: " + data["error"] + C.RESET)

        threading.Thread(target=_enviar, daemon=True).start()

    corriendo[0] = False
    dim("Saliendo del chat...")

# ---------------------------------------------------------------------------
# MENÚ — CONTROL DEL SERVIDOR
# ---------------------------------------------------------------------------

def menu_principal():
    yo = sesion["nombre"]

    while True:
        limpiar()
        separador("═", 50, C.MORADO)
        rol_str = ROL_NOMBRES[sesion["rol"]]
        print(C.BOLD + C.MORADO + f"  CHAT TERMUX v{VERSION}" + C.RESET)
        print(C.GRIS + f"  Usuario: {yo.upper()}  |  Rol: {rol_str}" + C.RESET)
        print(C.GRIS + f"  Servidor: {SERVIDOR}" + C.RESET)
        separador("═", 50, C.MORADO)
        print()
        print(f"  {C.BOLD}💬 CHAT{C.RESET}")
        print("  1. Chatear con alguien")
        print("  2. Ver usuarios conectados")
        print("  3. Estadísticas del servidor")
        print("  4. Comandos del bot")
        print()

        if sesion["rol"] >= ROL_ADMIN:
            print(f"  {C.BOLD}⚙ ADMINISTRACIÓN{C.RESET}")
            print("  5. Control del servidor")
            print("  6. Control de la PC")
            print("  7. Monitor en tiempo real")
            print()

        print(f"  {C.BOLD}🔐 SEGURIDAD{C.RESET}")
        print("  8. Seguridad y privacidad")
        print()
        print("  0. Salir")
        separador()
        op = input("  Opción: ").strip()

        if op == "0":
            ok("¡Hasta luego!")
            break

        elif op == "1":
            otro = input("  ¿Con quién quieres hablar? ").strip().lower()
            if otro:
                modo_chat(yo, otro)

        elif op == "2":
            limpiar(); titulo("USUARIOS CONECTADOS", C.VERDE)
            usuarios = obtener_usuarios()
            if usuarios:
                print(f"  {C.BOLD}{'NOMBRE':<18} {'SALDO':<10} {'MSGS'}{C.RESET}")
                separador("-", 45, C.GRIS)
                for u in usuarios:
                    print(f"  {C.VERDE}{u['nombre'][:17]:<18}{C.RESET}"
                          f"{u.get('saldo',0):<10} {u.get('mensajes',0)}")
            else:
                err("Sin usuarios o servidor no disponible")
            input("\n  Enter para volver...")

        elif op == "3":
            limpiar(); titulo("ESTADÍSTICAS DEL SERVIDOR", C.CIAN)
            stats = obtener_stats()
            if stats:
                campos = [("Usuarios","usuarios"), ("Mensajes","mensajes"),
                          ("Grupos","grupos"), ("Notas","notas"),
                          ("Monedas","monedas_total"), ("Servidor","servidor"),
                          ("Hora","hora")]
                for label, key in campos:
                    print(f"  {C.BOLD}{label:<15}{C.RESET} {stats.get(key,'?')}")
            else:
                err("No se pudo conectar al servidor")
            input("\n  Enter para volver...")

        elif op == "4":
            limpiar(); titulo("COMANDOS DEL BOT", C.AMARILLO)
            secciones = {
                "BÁSICOS": ["hola","saldo","perfil","historial","ranking",
                            "hora","fecha","chiste","dado","moneda"],
                "TRANSFERENCIAS": ["transferir 50 usuario"],
                "NOTAS": ["nota TEXTO","mis notas"],
                "GRUPOS": ["crear grupo NOMBRE","unirse NOMBRE","grupos"],
                "BATALLA": ["batalla","batalla registrar python",
                            "batalla retar USUARIO","atacar for_loop",
                            "defender try_except","batalla ranking"],
                "LIGA": ["liga","equipo cali"],
            }
            for sec, cmds in secciones.items():
                print(f"\n  {C.AMARILLO}{sec}{C.RESET}")
                for c in cmds:
                    print(f"  {C.GRIS}  {c}{C.RESET}")
            input("\n  Enter para volver...")

        elif op == "5" and sesion["rol"] >= ROL_ADMIN:
            menu_servidor()

        elif op == "6" and sesion["rol"] >= ROL_ADMIN:
            menu_pc()

        elif op == "7" and sesion["rol"] >= ROL_ADMIN:
            monitor_tiempo_real()

        elif op == "8":
            resultado = menu_seguridad()
            if resultado == "logout":
                return  # Volver al login

# ---------------------------------------------------------------------------
# INICIO
# ---------------------------------------------------------------------------

def main():
    limpiar()

    # Verificar conexión primero
    separador("▓", 50, C.MORADO)
    print(C.BOLD + C.MORADO + "  CHAT TERMUX v" + VERSION + C.RESET)
    print(C.GRIS + "  Verificando conexión..." + C.RESET)
    separador("▓", 50, C.MORADO)
    print()

    try:
        r = requests.get(SERVIDOR + "/ping", timeout=5)
        if r.status_code == 200:
            ok(f"Servidor conectado: {SERVIDOR}")
        else:
            warn(f"Servidor responde con código {r.status_code}")
    except Exception as e:
        err("No se pudo conectar al servidor.")
        warn(f"Verifica que el servidor esté en {SERVIDOR}")
        warn("y que estés en el mismo WiFi.")
        input("\n  Enter para salir...")
        return

    print()

    # Loop de autenticación
    while True:
        if pantalla_login():
            menu_principal()
            # Si vuelve aquí, puede ser logout o salida normal
            resp = input("\n  ¿Iniciar otra sesión? (si/no): ").strip().lower()
            if resp != "si":
                break
        else:
            if esta_bloqueado():
                time.sleep(2)
            resp = input("\n  ¿Intentar de nuevo? (si/no): ").strip().lower()
            if resp != "si":
                break

    print()
    ok("Chat Termux cerrado.")

if __name__ == "__main__":
    main()
