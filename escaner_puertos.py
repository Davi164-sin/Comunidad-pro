import socket
import servidor_pruba as sv

verificando_contenido = sv 
print("Buscando el contenido")

contenido = {} 
print(f"El contenido es: {contenido} más {verificando_contenido}") 


# Escanearemos tu propia máquina local
objetivo = "127.0.0.1"

# Lista de puertos populares en desarrollo y servicios comunes
puertos_a_escanear = [21, 22, 23, 25, 53, 80, 443, 8080, 8888, 5003]

print(f"🔍 Escaneando puertos populares en {objetivo}...")

for puerto in puertos_a_escanear:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(0.5) 
    
    resultado = s.connect_ex((objetivo, puerto))
    if resultado == 0:
        print(f"✅ Puerto {puerto}: ABIERTO")
    else:
        print(f"❌ Puerto {puerto}: CERRADO")
    s.close()

print("🏁 Escaneo finalizado.")
