import requests
import json

USUARIO = "Achip"
TOKEN = "e49feba63815147f36c647450d5d43b7a969d9f6"
HEADERS = {"Authorization": f"Token {TOKEN}"}

# Ruta para listar archivos
ruta_directorio = "/home/Achip/mysite/"

def listar_archivos():
    print(f"🔍 Listando archivos en {ruta_directorio}...")
    url = f"https://www.pythonanywhere.com/api/v0/user/{USUARIO}/files/list?path={ruta_directorio}"
    
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        archivos = response.json()
        print("Archivos encontrados:")
        for a in archivos:
            print(f"- {a}")
    else:
        print(f"❌ Error al listar: {response.status_code} - {response.text}")

if __name__ == "__main__":
    listar_archivos()
