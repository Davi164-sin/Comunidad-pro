import argparse
import sys
import threading
import time

# 1. Demostración de Argparse mejorado
def setup_args():
    parser = argparse.ArgumentParser(description="Demo de características modernas de Python")
    parser.add_argument("--feature", choices=["traceback", "thread"], help="Selecciona qué probar")
    # Python 3.13+ soporta deprecación de argumentos directamente
    parser.add_argument("--old-option", help="Opción antigua (deprecada)", deprecated=True)
    return parser.parse_args()

# 2. Demostración de Tracebacks mejorados (forzamos un error)
def demo_traceback():
    print("--- Demostración de Traceback mejorado ---")
    # Creando un error sintáctico o lógico para ver la salida coloreada
    a = [1, 2, 3]
    print(a[10]) # IndexError

# 3. Contexto de Free-Threading (conceptualmente)
def worker():
    print(f"Hilo {threading.current_thread().name} ejecutándose.")
    time.sleep(1)

def demo_thread():
    print("--- Demostración de hilos (en Python 3.14 con mejoras de GIL) ---")
    t1 = threading.Thread(target=worker, name="T1")
    t2 = threading.Thread(target=worker, name="T2")
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("Hilos finalizados.")

if __name__ == "__main__":
    args = setup_args()
    
    if args.feature == "traceback":
        demo_traceback()
    elif args.feature == "thread":
        demo_thread()
    else:
        print("Por favor, usa --feature traceback o --feature thread")
