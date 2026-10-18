import socket
import concurrent.futures
import sys
import re

def validar_ip(ip):
    # Expresión regular simple para validar formato IP (ej. 127.0.0.1)
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
        return True
    return False

def escanear_puerto(ip, puerto):
    # Uso de socket con contextos ('with') para asegurar cierre automático y seguro
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex((ip, puerto)) == 0:
                banner = capturar_banner(ip, puerto)
                return f"✅ Puerto {puerto}: ABIERTO | {banner}"
    except Exception:
        pass
    return None

def capturar_banner(ip, puerto):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect((ip, puerto))
            # Algunos servicios requieren un empujón para responder
            s.send(b'HEAD / HTTP/1.0\r\n\r\n')
            banner = s.recv(1024)
            if banner:
                return f"Banner: {banner.decode().strip()[:50]}"
            return "Banner: (Servicio silencioso)"
    except Exception:
        return "Banner: (No se pudo capturar)"

def main(ip):
    if not validar_ip(ip):
        print("❌ Error: Formato de IP no válido.")
        return

    puertos = [21, 22, 23, 25, 53, 80, 443, 8080, 8888, 5003]
    
    print(f"🚀 Escaneo avanzado iniciado en {ip} (Rendimiento optimizado)...")
    
    # Concurrencia: Escanear puertos en paralelo para mejorar el rendimiento
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        resultados = {executor.submit(escanear_puerto, ip, p): p for p in puertos}
        for future in concurrent.futures.as_completed(resultados):
            resultado = future.result()
            if resultado:
                print(resultado)

    print("🏁 Escaneo finalizado.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Uso: python advanced_scanner.py <ip>")
