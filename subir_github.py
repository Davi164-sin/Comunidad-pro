import os
import subprocess

print("Actualizando archivos con la nueva página Acerca de...")
subprocess.run(["git", "config", "http.postBuffer", "524288000"])
subprocess.run(["git", "add", "gestor_comunidad.py", "templates/"])
subprocess.run(["git", "commit", "-m", "Añadir pagina Acerca de (About) y rutas"])
push_res = subprocess.run(["git", "push", "origin", "main", "--force"])

if push_res.returncode == 0:
    print("\n¡Actualización subida con éxito a GitHub!")
else:
    print("\nError al subir.")
