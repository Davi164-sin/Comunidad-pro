# Ejercicio de Lógica: Escáner Inteligente de Puertos

# Objetivo: Mejorar la lógica del escáner para identificar servicios.
# Instrucciones:
# 1. Utiliza lo que sabes sobre listas, bucles (for/while) y condicionales (if/elif/else).
# 2. Crea un diccionario que mapee puertos comunes con sus servicios (ej: 80: "HTTP", 22: "SSH").
# 3. Modifica la función 'analizar_puerto' para que recorra una lista de puertos y,
#    si el puerto está abierto, imprima qué servicio es, o "Servicio desconocido" si no está en el mapa.

def analizar_puertos(puertos):
    # Mapa de puertos: servicio
    servicios = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        443: "HTTPS",
        8080: "HTTP-Proxy"
    }

    print("--- Iniciando Análisis de Servicios ---")
    
    # TU CÓDIGO AQUÍ:
    # 1. Usa un bucle 'for' para recorrer la lista 'puertos'.
    # 2. Usa un 'if' para verificar si el puerto existe en el diccionario 'servicios'.
    # 3. Imprime el resultado.
    
    pass # Reemplaza esto con tu lógica

if __name__ == "__main__":
    puertos_a_probar = [21, 22, 80, 443, 3306]
    analizar_puertos(puertos_a_probar)
