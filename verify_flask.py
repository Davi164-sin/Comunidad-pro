import requests

USUARIO = "Achip"
TOKEN = "e49feba63815147f36c647450d5d43b7a969d9f6"
HEADERS = {"Authorization": f"Token {TOKEN}"}

# Ruta en el servidor remoto que queremos verificar
ruta_remota = "/home/Achip/mysite/flask_app.py"

def verificar_archivo_remoto():
    print(f"🔍 Verificando contenido de {ruta_remota}...")
    url = f"https://www.pythonanywhere.com/api/v0/user/{USUARIO}/files/path{ruta_remota}"
    
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        contenido = response.text
        if "db_check.db" in contenido:
            print("✅ ¡ÉXITO! La ruta de la base de datos es correcta en el servidor.")
        else:
            print("❌ La ruta de la base de datos ES INCORRECTA en el servidor remoto.")
            # Buscar qué ruta tiene
            for linea in contenido.split('\n'):
                if 'DB_PATH' in linea:
                    print(f"   Actual: {linea.strip()}")
    else:
        print(f"❌ Error al acceder al archivo remoto: {response.status_code}")

if __name__ == "__main__":
    verificar_archivo_remoto()
