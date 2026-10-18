import requests
import os
from dotenv import load_dotenv

# Carga explícita del archivo .env en la misma carpeta que este script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'asistente_project', '.env'))

USUARIO = "Achip"
TOKEN = os.getenv("PYTHONANYWHERE_TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}"}

# Directorio base del proyecto
BASE_PROYECTO = "asistente_project"

# Directorios y archivos CRÍTICOS a sincronizar
rutas_a_sincronizar = [
    (os.path.join(BASE_PROYECTO, "flask_app.py"), "/home/Achip/mysite/flask_app.py"),
    (os.path.join(BASE_PROYECTO, "wsgi.py"), "/home/Achip/mysite/wsgi.py"),
    (os.path.join(BASE_PROYECTO, "templates", "dashboard.html"), "/home/Achip/mysite/templates/dashboard.html"),
]

def subir_archivo(local, servidor):
    print(f"🚀 Subiendo {local} a {servidor}...")
    url = f"https://www.pythonanywhere.com/api/v0/user/{USUARIO}/files/path{servidor}"
    
    try:
        with open(local, "rb") as f:
            response = requests.post(url, headers=HEADERS, files={"content": f})
    except Exception as e:
        print(f"❌ Error al leer {local}: {e}")
        return False
    
    if response.status_code in [200, 201]:
        print(f"✅ {local} subido.")
        return True
    else:
        print(f"❌ Error al subir {local}: {response.status_code} - {response.text}")
        return False

# Ejecutar sincronización
print("--- Iniciando sincronización quirúrgica (Solo archivos críticos) ---")
exito = True
for local, servidor in rutas_a_sincronizar:
    if not subir_archivo(local, servidor):
        exito = False

if exito:
    print("🔄 Reiniciando servidor...")
    url_reload = f"https://www.pythonanywhere.com/api/v0/user/{USUARIO}/webapps/{USUARIO}.pythonanywhere.com/reload/"
    res_reload = requests.post(url_reload, headers=HEADERS)
    if res_reload.status_code == 200:
        print("⚡ ¡Sincronización completa! Prueba tu web.")
    else:
        print(f"⚠️ Reinicia manualmente en el panel de PythonAnywhere ({res_reload.status_code})")
else:
    print("❌ La sincronización tuvo errores. Revisa la salida.")

