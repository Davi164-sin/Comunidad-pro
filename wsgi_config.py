import sys
import os

# Ruta a la carpeta que contiene flask_app.py
path = '/home/Achip/mysite'
if path not in sys.path:
    sys.path.append(path)

# Importamos el objeto 'app' definido en flask_app.py
# y le asignamos el nombre 'application' que es lo que espera PythonAnywhere
from flask_app import app as application
