#!/usr/bin/env python3
"""
ASISTENTE PERSONAL DAVID - Edición Termux (Android)
===================================================
"""

import os, json, hashlib, time, sys, subprocess
import urllib.request
import urllib.error
from datetime import datetime

# API Key y Configuración de Modelo
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
MODELO = "gemini-flash-latest"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent?key={API_KEY}"

# Archivos adaptados para el almacenamiento local de Termux
HOME_DIR = os.path.expanduser("~")
ARCHIVO_MEMORIA = os.path.join(HOME_DIR, "asistente_memoria.json")
ARCHIVO_USUARIOS = os.path.join(HOME_DIR, "asistente_users.json")

CONOCIMIENTO = {
    "nombre": "David",
    "ubicacion": "Cali, Colombia",
    "entorno": "Termux (Android)",
    "lenguaje": "Python"
}

def hash_pass(p):
    return hashlib.pbkdf2_hmac('sha256', p.encode(), b'salt', 100000).hex()

def verificar_usuario():
    if not os.path.exists(ARCHIVO_USUARIOS):
        print("\n🔐 Primera vez - Configurar seguridad")
        p = input("Crea contraseña: ").strip()
        usuarios = {"david": {"hash": hash_pass(p), "ultimo": time.time()}}
        with open(ARCHIVO_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f)
        print("✅ Listo\n")
        return True
    
    with open(ARCHIVO_USUARIOS, 'r', encoding='utf-8') as f:
        usuarios = json.load(f)
    
    for i in range(3):
        p = input("🔑 Contraseña: ").strip()
        if hash_pass(p) == usuarios["david"]["hash"]:
            return True
        print(f"❌ Incorrecto ({2-i} intentos)")
    print("\n🚫 Bloqueado")
    return False

def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        try:
            with open(ARCHIVO_MEMORIA, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"conversaciones": [], "aprendizajes": {}}

def guardar_memoria(m):
    with open(ARCHIVO_MEMORIA, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

def ejecutar_comando_sistema(comando):
    """Ejecuta un comando directamente en la terminal Bash de Termux."""
    try:
        resultado = subprocess.check_output(comando, shell=True, stderr=subprocess.STDOUT, text=True)
        return resultado if resultado else "Comando ejecutado con éxito."
    except subprocess.CalledProcessError as e:
        return f"Error al ejecutar comando:\n{e.output}"

def preguntar_gemini(pregunta, contexto=None):
    directorio_actual = os.getcwd()
    
    sistema = (
        f"Eres asistente de {CONOCIMIENTO['nombre']}. Ubicación: {CONOCIMIENTO['ubicacion']}.\n"
        f"Entorno actual: Termux en Android. Directorio actual: {directorio_actual}\n"
        "Si el usuario te pide crear, modificar o listar archivos/carpetas, dale la explicación "
        "y si vas a sugerir un comando bash de Termux/Linux para crear o escribir archivos, pon ÚNICAMENTE el comando ejecutable entre bloques ```bash ```."
    )
    
    if contexto:
        sistema += f"\nContexto adicional: {contexto}"

    prompt_completo = f"{sistema}\n\nUsuario: {pregunta}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_completo}]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(URL, data=data, headers={'Content-Type': 'application/json'})

    # Aumentamos el timeout a 30s y reintentamos ante problemas de red móvil o cuota 429
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['candidates'][0]['content']['parts'][0]['text']
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"\n⚠️ Límite de cuota (429). Reintentando en 10s ({intento+1}/3)...")
                time.sleep(10)
                continue
            error_body = e.read().decode('utf-8')
            return f"Error HTTP {e.code}:\n{error_body}"
        except urllib.error.URLError as e:
            print(f"\n⚠️ Reintento por fallo de conexión/timeout ({intento+1}/3)...")
            time.sleep(3)
            continue
        except Exception as e:
            return f"Error de conexión: {str(e)}"
            
    return "❌ Error: La conexión a la API tardó demasiado. Revisa tu red móvil/Wi-Fi e inténtalo de nuevo."

def main():
    if not verificar_usuario():
        return
    
    memoria = cargar_memoria()
    
    print("\n" + "═"*45)
    print("  🤖 ASISTENTE DAVID - Modo Termux (Android)")
    print("═"*45)
    print("\n  chat | cmd | aprender | memoria | salir\n")
    
    while True:
        try:
            cmd = input("» ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 ¡Hasta luego!\n")
            break
        
        if not cmd or cmd == "salir":
            print("👋 ¡Hasta luego!\n")
            break
        
        elif cmd == "cmd":
            print("\n⚡ Modo Comando Directo Bash (escribe 'x' para volver)")
            print(f"📍 Directorio actual: {os.getcwd()}\n")
            while True:
                c = input("Termux > ").strip()
                if c.lower() == "x":
                    break
                if not c:
                    continue
                if c.startswith("cd "):
                    nueva_ruta = c.split(maxsplit=1)[1]
                    try:
                        os.chdir(os.path.expanduser(nueva_ruta))
                        print(f"📍 Ahora estás en: {os.getcwd()}\n")
                    except Exception as e:
                        print(f"❌ Error: {e}\n")
                else:
                    out = ejecutar_comando_sistema(c)
                    print(f"\n{out}\n")

        elif cmd == "chat":
            print("\n💬 Chat activo (escribe 'x' para volver al menú)\n")
            while True:
                p = input("Tú: ").strip()
                if p.lower() == "x":
                    break
                if not p:
                    continue
                
                ctx = None
                for tema, datos in memoria["aprendizajes"].items():
                    if tema.lower() in p.lower():
                        ctx = datos["info"]
                        break
                
                print("⏳ Consultando Gemini...")
                r = preguntar_gemini(p, ctx)
                print(f"\n🤖: {r}\n")
                
                # Detectar si Gemini propone un comando Bash para ejecutarlo en Termux
                if "```bash" in r or "```sh" in r:
                    tag = "```bash" if "```bash" in r else "```sh"
                    try:
                        cmd_sugerido = r.split(tag)[1].split("```")[0].strip()
                        confirmar = input("⚡ ¿Deseas ejecutar este comando en Termux? (s/n): ").strip().lower()
                        if confirmar == 's':
                            out = ejecutar_comando_sistema(cmd_sugerido)
                            print(f"\n📂 Resultado del sistema:\n{out}\n")
                    except Exception as err:
                        print(f"No se pudo procesar el comando: {err}")

                memoria["conversaciones"].append({
                    "fecha": datetime.now().isoformat(),
                    "q": p,
                    "a": r
                })
                if len(memoria["conversaciones"]) > 50:
                    memoria["conversaciones"] = memoria["conversaciones"][-50:]
                guardar_memoria(memoria)
        
        elif cmd == "aprender":
            tema = input("Tema: ").strip()
            info = input("Info: ").strip()
            if tema and info:
                memoria["aprendizajes"][tema] = {
                    "info": info,
                    "fecha": datetime.now().isoformat()
                }
                guardar_memoria(memoria)
                print(f"✅ Aprendí sobre: {tema}\n")
        
        elif cmd == "memoria":
            if memoria["aprendizajes"]:
                print("\n🧠 Aprendizajes:\n")
                for t, d in memoria["aprendizajes"].items():
                    print(f"  • {t}: {d['info'][:40]}...")
                print()
            else:
                print("\n📝 No hay aprendizajes aún\n")
        
        else:
            print(f"❌ Comando desconocido\n")

if __name__ == '__main__':
    main()
