import requests
import os

USUARIO = "Achip"
TOKEN = "e49feba63815147f36c647450d5d43b7a969d9f6"
HEADERS = {"Authorization": f"Token {TOKEN}"}

# Ruta en el servidor remoto que queremos verificar
ruta_remota = "/home/Achip/mysite/templates/layout.html"

def verificar_archivo_remoto():
    print(f"🔍 Verificando contenido de {ruta_remota} en el servidor...")
    url = f"https://www.pythonanywhere.com/api/v0/user/{USUARIO}/files/path{ruta_remota}"
    
    # PythonAnywhere API files/path GET devuelve el contenido si es un archivo
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        contenido = response.text
        if "TEST DE DESPLIEGUE" in contenido:
            print("✅ ¡ÉXITO! El aviso rojo está presente en el archivo remoto.")
        else:
            print("❌ El archivo remoto NO contiene el aviso rojo.")
    else:
        print(f"❌ Error al acceder al archivo remoto: {response.status_code} - {response.text}")

if __name__ == "__main__":
    verificar_archivo_remoto()
