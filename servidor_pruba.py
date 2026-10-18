from flask import Flask, session, request, redirect, url_for, render_template_string
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Usar variable de entorno con valor predeterminado seguro
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_change_me_in_production')

# --- RUTA DE TU SD ---
# Se recomienda mover esta ruta a una variable de entorno también si es específica del entorno
RUTA_SD = os.environ.get('RUTA_SD', '/storage/45D3-0DF6/Android/media/com.termux/Almacenamiento_Servidor')
ARCHIVO_JSON = 'peliculas.json'

# Mover usuarios a variables de entorno o gestión de BD segura
# Ejemplo: USUARIOS = json.loads(os.environ.get('USUARIOS_JSON', '{}'))
USUARIOS = {"admin": os.environ.get('ADMIN_PASSWORD', 'admin77'), "david": os.environ.get('DAVID_PASSWORD', '123'), "invitado": "pago"}

# Intentar crear la ruta si no existe (si da error de permiso, el try lo ignora)
try:
    if not os.path.exists(RUTA_SD):
        os.makedirs(c)
except:
    pass

def cargar_datos():
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

HTML_COMPLETO = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nube Pro - Streaming</title>
    <style>
        :root { --accent: #00d4ff; --bg: #0f0f0f; --card: #1e1e1e; }
        body { background: var(--bg); color: white; font-family: sans-serif; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--accent); padding-bottom: 10px; }
        .buscador { width: 90%; max-width: 500px; padding: 12px; border-radius: 25px; border: 1px solid #333; background: var(--card); color: white; margin: 20px auto; display: block; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
        .card { background: var(--card); border-radius: 12px; overflow: hidden; border: 1px solid #333; }
        video { width: 100%; background: #000; height: 200px; }
        .info { padding: 15px; }
        .tag { background: var(--accent); color: black; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .login-box { background: var(--card); padding: 40px; border-radius: 15px; border: 1px solid var(--accent); max-width: 350px; margin: 100px auto; text-align: center; }
        input { width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #444; background: #111; color: white; }
        .btn { background: var(--accent); color: black; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; }
    </style>
</head>
<body>

    {% if not session.get('user') %}
        <div class="login-box">
            <h2>🔐 Acceso Privado</h2>
            <form method="post" action="/login">
                <input type="text" name="u" placeholder="Usuario" required>
                <input type="password" name="p" placeholder="Contraseña" required>
                <button type="submit" class="btn">ENTRAR AL SISTEMA</button>
            </form>
            {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
        </div>
    {% else %}
        <div class="header">
            <h2>🎬 Mi Catálogo</h2>
            <div>
                <span style="margin-right:15px;">👤 {{ session['user'] }}</span>
                <a href="/logout" style="color:#ff4444; text-decoration:none;">Cerrar Sesión</a>
            </div>
        </div>

        <input type="text" id="busqueda" class="buscador" placeholder="🔍 Buscar..." onkeyup="filtrar()">

        <div class="grid" id="catalogo">
            {% for v in videos %}
            <div class="card" data-search="{{ v.nombre.lower() }}">
                <video controls preload="metadata">
                    <source src="/stream/{{ v.archivo }}" type="video/mp4">
                    Tu navegador no soporta video.
                </video>
                <div class="info">
                    <span class="tag">{{ v.categoria }}</span>
                    <h3 style="margin: 10px 0;">{{ v.nombre }}</h3>
                    <p style="color:var(--accent); font-weight:bold;">Precio: {{ v.precio }}</p>
                </div>
            </div>
            {% endfor %}
        </div>

        <script>
            function filtrar() {
                let term = document.getElementById('busqueda').value.toLowerCase();
                document.querySelectorAll('.card').forEach(card => {
                    let contenido = card.getAttribute('data-search');
                    card.style.display = contenido.includes(term) ? "block" : "none";
                });
            }
        </script>
    {% endif %}

</body>
</html>
'''

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5004)
