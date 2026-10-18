import socket

# Escanearemos tu propia máquina local
objetivo = "127.0.0.1"

# Puertos para probar (puedes añadir otros si montas servicios)
puertos_a_escanear = [21, 22, 23, 25, 53, 80, 443, 8080, 8888]

print(f"🔍 Escaneando y capturando Banners en {objetivo}...")

for puerto in puertos_a_escanear:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(1) # Un poco más de tiempo para esperar respuesta
    
    # Intentar conectar
    resultado = s.connect_ex((objetivo, puerto))
    
    if resultado == 0:
        print(f"✅ Puerto {puerto}: ABIERTO")
        try:
            # Enviar un pequeño saludo (opcional, ayuda a veces a obtener respuesta)
            s.send(b'HEAD / HTTP/1.0\r\n\r\n')
            
            # Recibir respuesta (el banner)
            banner = s.recv(1024)
            if banner:
                print(f"   💬 Banner: {banner.decode().strip()}")
            else:
                print(f"   💬 No se recibió banner (servicio silencioso)")
        except Exception as e:
            print(f"   ❌ No se pudo capturar banner: {e}")
    else:
        # No imprimir nada si está cerrado para que la salida sea limpia
        pass
    s.close()

print("🏁 Escaneo finalizado.")
