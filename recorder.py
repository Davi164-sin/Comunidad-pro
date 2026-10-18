import subprocess
import sys
import os
import signal

def start_recording():
    # Estructura básica para ffmpeg. 
    # Nota: ':0.0' depende de la configuración de X11 del usuario.
    # El archivo PID asegura que podamos detener el proceso correcto.
    cmd = [
        'ffmpeg', '-f', 'x11grab', '-video_size', '1920x1080', 
        '-i', ':0.0', '-c:v', 'libx264', 'output.mp4'
    ]
    
    print("Iniciando grabación... Presiona Ctrl+C para detener.")
    process = subprocess.Popen(cmd)
    
    with open('recorder.pid', 'w') as f:
        f.write(str(process.pid))
    print(f"Grabación iniciada con PID: {process.pid}")

def stop_recording():
    if not os.path.exists('recorder.pid'):
        print("No hay grabación activa.")
        return
        
    with open('recorder.pid', 'r') as f:
        pid = int(f.read())
        
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Grabación detenida (PID: {pid}).")
        os.remove('recorder.pid')
    except ProcessLookupError:
        print("Proceso no encontrado.")
        os.remove('recorder.pid')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 recorder.py [start|stop]")
        sys.exit(1)
        
    action = sys.argv[1]
    if action == "start":
        start_recording()
    elif action == "stop":
        stop_recording()
