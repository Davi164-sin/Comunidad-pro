#!/usr/bin/env python3
import csv
import re
import urllib.parse
import urllib.request


def buscar_leads_directo(rubro, ciudad="Cali"):
  print(f"🔎 Buscando '{rubro}' en {ciudad} directamente sin API...\n")

  # Query codificada para búsqueda web
  query = urllib.parse.quote(f"{rubro} en {ciudad} Colombia telefono direccion")
  url = f"https://html.duckduckgo.com/html/?q={query}"

  # Encabezado para simular un navegador real
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like"
          " Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  req = urllib.request.Request(url, headers=headers)
  leads = []

  try:
    with urllib.request.urlopen(req, timeout=15) as response:
      html = response.read().decode("utf-8")

      # Extraer bloques de resultados
      resultados = re.findall(
          r'<a class="result__url" href="[^"]*">(.*?)</a>.*?<a'
          r' class="result__snippet[^"]*">(.*?)</a>',
          html,
          re.DOTALL,
      )

      for url_text, snippet in resultados[:10]:
        # Limpiar etiquetas HTML
        snippet_limpio = re.sub(r"<[^>]+>", "", snippet).strip()

        # Buscar patrones de números telefónicos colombianos
        telefonos = re.findall(
            r"(?:\+?57\s?)?(?:3\d{2}|60\d)\s?\d{3}\s?\d{4}", snippet_limpio
        )
        tel = telefonos[0] if telefonos else "Consultar directorio"

        # Extraer un nombre representativo desde la fuente
        nombre = re.sub(r"<[^>]+>", "", url_text).strip()
        nombre = nombre.replace("https://", "").replace("http://", "").split("/")[0]

        if len(nombre) > 3:
          leads.append({
              "nombre": nombre,
              "telefono": tel,
              "snippet": snippet_limpio[:120] + "...",
          })

  except Exception as e:
    print(f"❌ Error en la extracción directa: {e}")
    return []

  return leads


def guardar_csv(leads, archivo="leads_directos.csv"):
  if not leads:
    print("⚠️ No se encontraron resultados en esta pasada.")
    return

  with open(archivo, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=["nombre", "telefono", "snippet"]
    )
    writer.writeheader()
    writer.writerows(leads)

  print(f"\n✅ Se extrajeron {len(leads)} leads y se guardaron en '{archivo}'")


if __name__ == "__main__":
  rubro = (
      input("Tipo de negocio (ej: ferreterias, auto lavados): ").strip()
      or "ferreterias"
  )
  leads = buscar_leads_directo(rubro)

  if leads:
    print("--- RESULTADOS OBTENIDOS ---")
    for l in leads:
      print(f"📍 {l['nombre']} | Tel: {l['telefono']}")
      print(f"   Info: {l['snippet']}\n")
    guardar_csv(leads)
