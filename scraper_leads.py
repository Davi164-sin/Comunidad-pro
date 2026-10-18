import csv
import json
import time
import urllib.request

# Configuración básica
BUSQUEDA = "restaurantes"
CIUDAD = "Cali"
ARCHIVO_SALIDA = "leads_extraidos.csv"


def guardar_en_csv(datos):
  with open(
      ARCHIVO_SALIDA, mode="w", newline="", encoding="utf-8"
  ) as file:
    writer = csv.writer(file)
    writer.writerow(["Nombre", "Teléfono", "Dirección", "Estado"])
    for fila in datos:
      writer.writerow(fila)
  print(f"\n✅ Datos guardados con éxito en '{ARCHIVO_SALIDA}'")


def ejecutar_extraccion():
  print(f"🔎 Buscando clientes potenciales para '{BUSQUEDA}' en {CIUDAD}...\n")

  # Simulación de extracción estructurada
  # En producción se conecta a la API de Google Places o BeautifulSoup
  resultados = [
      ["Restaurante Don Pedro", "+57 300 123 4567", "Calle 5 # 10-20", "Nuevo"],
      ["Sabor Valluno", "+57 315 987 6543", "Av. Roosevelt # 25-14", "Nuevo"],
      ["Asadero El Cruce", "+57 312 456 7890", "Carrera 10 # 15-30", "Nuevo"],
  ]

  for lead in resultados:
    print(f"📍 Encontrado: {lead[0]} | Tel: {lead[1]}")
    time.sleep(1)

  guardar_en_csv(resultados)


if __name__ == "__main__":
  ejecutar_extraccion()
