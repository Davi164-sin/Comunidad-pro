import csv
import json
from faker import Faker

fake = Faker("es_MX")

cantidad = 1000
datos = []

for _ in range(cantidad):
    registro = {
        "nombre": fake.name(),
        "email": fake.email(),
        "telefono": fake.phone_number(),
        "direccion": fake.address().replace("\n", ", ")
    }
    datos.append(registro)

# Guardar en CSV
with open("leads_falsos.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["nombre", "email", "telefono", "direccion"])
    writer.writeheader()
    writer.writerows(datos)

# Guardar en JSON
with open("leads_falsos.json", "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=4)

print(f"¡Se generaron y guardaron {cantidad} registros en 'leads_falsos.csv' y 'leads_falsos.json'!")
