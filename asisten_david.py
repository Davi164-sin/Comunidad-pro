import click
import os
import re
import shutil
import time
from gtts import gTTS
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

def hablar(texto):
    print(f"🤖: {texto}")
    try:
        # Nota: En un servidor, esto podría no funcionar si no hay dispositivo de audio.
        # Desactivado temporalmente en modo servidor.
        if not app.config.get('IS_SERVER', False):
            tts = gTTS(text=texto, lang='es')
            tts.save("voz.mp3")
            os.system("mpv --really-quiet voz.mp3 && rm voz.mp3 &")
    except: pass

def verificar_espacio():
    # Asegurar que la ruta exista, si no usar el directorio actual
    path = "/data" if os.path.exists("/data") else "."
    total, usado, libre = shutil.disk_usage(path)
    libre_mb = libre // (2**20)
    if libre_mb < 150:
        hablar(f"Atención, espacio muy bajo: {libre_mb} megas.")
        return False
    return True

def descargar_video(url, nombre_pelicula=None):
    if not verificar_espacio(): return "❌ Espacio insuficiente."

    # Ajustar ruta para que los videos aparezcan en la galería de Android (/sdcard/Movies o /sdcard/Download)
    if os.path.exists("/sdcard"):
        base_dir = "/sdcard/Movies/Videos_Asistente"
        if not os.path.exists("/sdcard/Movies"):
            base_dir = "/sdcard/Download/Videos_Asistente"
    else:
        base_dir = os.path.expanduser("~/storage/downloads/Videos_Asistente")
        if not os.path.exists(os.path.expanduser("~") + "/storage"):
            base_dir = "./downloads"
    
    os.makedirs(base_dir, exist_ok=True)

    hablar("Iniciando descarga.")

    if nombre_pelicula:
        titulo = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9 ]', '', nombre_pelicula).strip().replace(" ", "_")
    else:
        titulo = f"pelicula_{int(time.time())}"

    nombre = f"{base_dir}/{titulo}.mp4"

    comando = (
        f'yt-dlp --extractor-args "youtube:player_client=android,web" '
        f'--no-check-certificate --user-agent "Mozilla/5.0" '
        f'--merge-output-format mp4 '
        f'-o "{nombre}" "{url}"'
    )

    exito = False
    if os.path.exists("/sdcard"):
        hablar("Descargando en almacenamiento del teléfono.")

    if os.system(comando) == 0:
        exito = True
        hablar("Descarga lista.")
        os.system(f'ia upload cine-david-peliculas "{nombre}" 2>/dev/null')
    else:
        hablar("Reintentando en calidad básica.")
        comando_simple = f'yt-dlp -f b --merge-output-format mp4 -o "{nombre}" "{url}"'
        if os.system(comando_simple) == 0:
            exito = True
            os.system(f'ia upload cine-david-peliculas "{nombre}" 2>/dev/null')

    if exito:
        # Actualizar la galería de Android para que el video aparezca inmediatamente
        if os.path.exists("/sdcard"):
            if shutil.which("termux-media-scan"):
                os.system(f'termux-media-scan "{nombre}"')
            else:
                os.system(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://"{nombre}" 2>/dev/null')
            hablar("Video añadido a tu galería.")
            return f"✅ Descargado con éxito y visible en tu galería ({nombre})."
        else:
            return "✅ Descarga exitosa."
    else:
        return "❌ Falló la descarga."

@app.route('/download', methods=['POST'])
def api_download():
    data = request.json
    url = data.get('url')
    nombre = data.get('nombre')
    if not url:
        return jsonify({"error": "URL requerida"}), 400
    
    # Ejecutar en segundo plano para no bloquear el servidor
    threading.Thread(target=descargar_video, args=(url, nombre)).start()
    return jsonify({"message": "Descarga iniciada"}), 202

@click.command()
@click.argument('url', required=False)
@click.option('--instalar', is_flag=True)
@click.option('--nombre', default=None, help='Nombre de la película')
@click.option('--server', is_flag=True, help='Iniciar modo servidor')
def main(url, instalar, nombre, server):
    if server:
        app.config['IS_SERVER'] = True
        app.run(host='0.0.0.0', port=5000)
        return
    if instalar:
        os.system("pip install -U yt-dlp gtts click flask")
        print("🚀 Motores actualizados.")
        return
    if url: print(descargar_video(url, nombre))
    else: hablar("Pega el link para descargar.")

if __name__ == '__main__':
    main()
