import sqlite3
import os

DB_PATH = "asistente_project/database.db"

def add_lesson():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return
    
    modulo = "Python"
    titulo = "Decoradores en Python"
    contenido = """
    <h2>Decoradores en Python</h2>
    <p>Los decoradores son una herramienta poderosa en Python que permite modificar el comportamiento de una función o clase sin cambiar su código fuente.</p>
    <p>Un decorador es esencialmente una función que recibe otra función como argumento y retorna una nueva función que extiende la funcionalidad de la original.</p>
    <pre><code>
def mi_decorador(func):
    def wrapper():
        print("Antes de llamar a la función")
        func()
        print("Después de llamar a la función")
    return wrapper

@mi_decorador
def saludar():
    print("¡Hola!")

saludar()
    </code></pre>
    <p>El uso del símbolo <code>@</code> es azúcar sintáctica para aplicar el decorador.</p>
    """
    es_premium = 1

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO lecciones (modulo, titulo, contenido, es_premium) VALUES (?, ?, ?, ?)", 
              (modulo, titulo, contenido, es_premium))
    conn.commit()
    conn.close()
    print("Lección añadida exitosamente.")

if __name__ == "__main__":
    add_lesson()
