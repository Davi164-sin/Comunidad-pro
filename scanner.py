import requests
import sys

def verificar_sitio(url):
    if not url.startswith("http"):
        url = "http://" + url
    
    try:
        print(f"🔗 Probando: {url}...")
        respuesta = requests.get(url, timeout=5)
        
        if respuesta.status_code == 200:
            print(f"✅ ¡El sitio está en línea! (Código: 200)")
            # AQUÍ ESTÁ LA MAGIA:
            servidor = respuesta.headers.get('Server', 'Desconocido')
            print(f"🔍 El servidor dice ser: {servidor}")
        else:
            print(f"⚠️ El sitio respondió con código: {respuesta.status_code}")
            
    except Exception as e:
        print(f"❌ Error: No se pudo conectar.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        verificar_sitio(sys.argv[1])
    else:
        print("Uso: python scanner.py <url>")
