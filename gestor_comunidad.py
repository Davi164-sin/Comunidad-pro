import os
import sqlite3
import csv
import io
import shutil
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# Usar SECRET_KEY fija de entorno o clave persistente de producción para evitar cierre de sesión al reiniciar
app.secret_key = os.environ.get("SECRET_KEY", "comunidad_pro_prod_static_secret_key_2026_x9z8y7")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
is_render = os.environ.get("RENDER") or not os.access(BASE_DIR, os.W_OK)

# Selección garantizada y robusta de base de datos persistente en Render (/data) sin modificar el punto de montaje raíz
env_db = os.environ.get("DATABASE_PATH", "/data/community_database.db")
if is_render:
    DB_PATH = "/data/community_database.db"
else:
    DB_PATH = env_db

try:
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and db_dir != "/data" and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    test_conn = sqlite3.connect(DB_PATH)
    test_conn.close()
    print(f"✅ Base de datos conectada correctamente en: {DB_PATH}")
except Exception as e:
    print(f"⚠️ Error conectando a {DB_PATH}: {e}. Usando base local de respaldo.")
    DB_PATH = os.path.join(BASE_DIR, "community_database.db")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Migración/Sincronización segura de datos locales a /data si fuera necesario
local_fallback_db = os.path.join(BASE_DIR, "community_database.db")
if DB_PATH == "/data/community_database.db" and os.path.exists(local_fallback_db) and local_fallback_db != DB_PATH:
    try:
        conn_target = sqlite3.connect(DB_PATH)
        c_target = conn_target.cursor()
        c_target.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='usuarios'")
        has_table = c_target.fetchone()[0] > 0
        conn_target.close()
        if not has_table and os.path.getsize(local_fallback_db) > 0:
            print("📦 Sincronizando base de datos existente hacia el disco persistente /data...")
            shutil.copy2(local_fallback_db, DB_PATH)
    except Exception as ex:
        print(f"Nota en sincronización de DB: {ex}")

# Selección segura de carpeta de subidas (Uploads) persistente
try:
    if "/data" in DB_PATH:
        UPLOAD_FOLDER = os.path.join("/data", "uploads")
    else:
        UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    test_up = os.path.join(UPLOAD_FOLDER, ".test")
    with open(test_up, "w") as f:
        f.write("test")
    os.remove(test_up)
except Exception:
    UPLOAD_FOLDER = os.path.join("/tmp", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if filename.startswith('http'):
        return redirect(filename)
    return send_from_directory(UPLOAD_FOLDER, filename)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "mp4", "webm", "ogg", "mov", "mkv", "avi", "mp3", "wav", "m4a", "aac", "pdf", "zip", "txt"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabla de usuarios
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'miembro', -- 'admin', 'moderador', 'creador', 'miembro'
            estado TEXT DEFAULT 'activo', -- 'activo', 'suspendido'
            puntos_contribucion INTEGER DEFAULT 0,
            nivel_maximo INTEGER DEFAULT 1,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN puntos_contribucion INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN nivel_maximo INTEGER DEFAULT 1")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Recuperar puntos y nivel para todos los usuarios existentes
    try:
        c.execute("UPDATE usuarios SET puntos_contribucion = MAX(puntos_contribucion, 50000), nivel_maximo = MAX(COALESCE(nivel_maximo, 1), 10)")
        conn.commit()
    except Exception:
        pass

    # Tabla de niveles personalizados gestionados por el administrador
    c.execute('''
        CREATE TABLE IF NOT EXISTS niveles_personalizados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_nivel INTEGER UNIQUE NOT NULL,
            nombre_nivel TEXT NOT NULL,
            bichos_velocidad REAL DEFAULT 1.5,
            descripcion TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de perfiles de creadores / talentos
    c.execute('''
        CREATE TABLE IF NOT EXISTS creadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER UNIQUE,
            nombre_artistico TEXT NOT NULL,
            categoria TEXT NOT NULL, -- 'Arte', 'Tecnología', 'Educación', 'Streaming', 'Diseño', 'Contenido Exclusivo', 'Otro'
            biografia TEXT,
            enlace_contenido TEXT,
            redes TEXT,
            avatar TEXT,
            multimedia_destacada TEXT,
            estado_aprobacion TEXT DEFAULT 'pendiente', -- 'pendiente', 'aprobado', 'rechazado'
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')

    for col in ["avatar TEXT", "multimedia_destacada TEXT"]:
        try:
            c.execute(f"ALTER TABLE creadores ADD COLUMN {col}")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # Tabla de enlaces de la comunidad (WhatsApp, Grupos, etc.)
    c.execute('''
        CREATE TABLE IF NOT EXISTS enlaces_grupo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            url TEXT NOT NULL,
            descripcion TEXT,
            categoria TEXT DEFAULT 'WhatsApp'
        )
    ''')

    # Tabla de anuncios / noticias de la comunidad
    c.execute('''
        CREATE TABLE IF NOT EXISTS anuncios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            contenido TEXT NOT NULL,
            archivo TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de chat de la comunidad
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_comunidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            usuario_nombre TEXT,
            mensaje TEXT,
            archivo TEXT,
            tipo_archivo TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de recursos descargables / guías
    c.execute('''
        CREATE TABLE IF NOT EXISTS recursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            archivo TEXT NOT NULL,
            tipo TEXT DEFAULT 'documento', -- 'video', 'audio', 'imagen', 'documento'
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de reseñas / valoraciones de creadores
    c.execute('''
        CREATE TABLE IF NOT EXISTS resenas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creador_id INTEGER,
            usuario_id INTEGER,
            usuario_nombre TEXT,
            calificacion INTEGER CHECK(calificacion BETWEEN 1 AND 5),
            comentario TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creador_id) REFERENCES creadores (id) ON DELETE CASCADE
        )
    ''')

    # Tabla de donaciones / apoyo a creadores
    c.execute('''
        CREATE TABLE IF NOT EXISTS donaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creador_id INTEGER,
            usuario_id INTEGER,
            usuario_nombre TEXT,
            monto REAL,
            mensaje TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creador_id) REFERENCES creadores (id) ON DELETE CASCADE
        )
    ''')

    # Tabla de notificaciones internas
    c.execute('''
        CREATE TABLE IF NOT EXISTS notificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            titulo TEXT,
            mensaje TEXT,
            leido INTEGER DEFAULT 0,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')

    # Tablas para encuestas y votaciones
    c.execute('''
        CREATE TABLE IF NOT EXISTS encuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta TEXT NOT NULL,
            activa INTEGER DEFAULT 1,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS opciones_encuesta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encuesta_id INTEGER,
            texto TEXT NOT NULL,
            votos INTEGER DEFAULT 0,
            FOREIGN KEY (encuesta_id) REFERENCES encuestas (id) ON DELETE CASCADE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS votos_encuesta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encuesta_id INTEGER,
            usuario_id INTEGER,
            opcion_id INTEGER,
            UNIQUE(encuesta_id, usuario_id)
        )
    ''')

    # Tabla de reportes de contenido
    c.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL, -- 'chat' o 'creador'
            item_id INTEGER NOT NULL,
            usuario_id INTEGER,
            usuario_nombre TEXT,
            motivo TEXT,
            estado TEXT DEFAULT 'pendiente',
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de almacenamiento personal de archivos
    c.execute('''
        CREATE TABLE IF NOT EXISTS archivos_almacenamiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            nombre_original TEXT NOT NULL,
            nombre_guardado TEXT NOT NULL,
            tipo TEXT DEFAULT 'documento',
            tamano INTEGER DEFAULT 0,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    
    # Crear un administrador por defecto si no existe y asegurar puntos de recuperación
    c.execute("SELECT id FROM usuarios WHERE email = 'admin@comunidad.com'")
    if not c.fetchone():
        hashed_pw = generate_password_hash("admin123")
        c.execute("INSERT INTO usuarios (nombre, email, password, rol, puntos_contribucion) VALUES (?, ?, ?, ?, ?)",
                  ("Administrador Principal", "admin@comunidad.com", hashed_pw, "admin", 50000))
        conn.commit()
    else:
        c.execute("UPDATE usuarios SET puntos_contribucion = MAX(puntos_contribucion, 50000) WHERE email = 'admin@comunidad.com'")
        conn.commit()

    # Crear usuario David por defecto si no existe y asegurar puntos de recuperación
    c.execute("SELECT id FROM usuarios WHERE email = 'david@comunidad.com'")
    if not c.fetchone():
        hashed_pw = generate_password_hash("david123")
        c.execute("INSERT INTO usuarios (nombre, email, password, rol, puntos_contribucion) VALUES (?, ?, ?, ?, ?)",
                  ("David", "david@comunidad.com", hashed_pw, "miembro", 50000))
        conn.commit()
    else:
        c.execute("UPDATE usuarios SET puntos_contribucion = MAX(puntos_contribucion, 50000) WHERE email = 'david@comunidad.com'")
        conn.commit()
        
    # Insertar enlaces de ejemplo si está vacío
    c.execute("SELECT COUNT(*) FROM enlaces_grupo")
    if c.fetchone()[0] == 0:
        ejemplos = [
            ("Grupo Principal de WhatsApp", "https://chat.whatsapp.com/ejemplo_principal", "Normas y debate general de la comunidad.", "WhatsApp"),
            ("Canal de Anuncios Oficial", "https://chat.whatsapp.com/ejemplo_anuncios", "Solo avisos importantes y normativas.", "WhatsApp"),
            ("Comunidad de Creadores", "https://chat.whatsapp.com/ejemplo_creadores", "Espacio exclusivo para creadores verificados.", "WhatsApp")
        ]
        c.executemany("INSERT INTO enlaces_grupo (titulo, url, descripcion, categoria) VALUES (?, ?, ?, ?)", ejemplos)
        conn.commit()

    # Insertar recursos de ejemplo si está vacío
    c.execute("SELECT COUNT(*) FROM recursos")
    if c.fetchone()[0] == 0:
        ejemplos_recursos = [
            ("Big Buck Bunny (Video Demo)", "Cortometraje animado de demostración en alta definición.", "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", "video"),
            ("Elephants Dream (Video Demo)", "Primer cortometraje animado de Blender Foundation.", "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4", "video"),
            ("Paisaje Natural (Imagen Demo)", "Fotografía de alta resolución de paisajes naturales.", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800", "imagen")
        ]
        c.executemany("INSERT INTO recursos (titulo, descripcion, archivo, tipo) VALUES (?, ?, ?, ?)", ejemplos_recursos)
        conn.commit()

    # Insertar anuncios de ejemplo si está vacío
    c.execute("SELECT COUNT(*) FROM anuncios")
    if c.fetchone()[0] == 0:
        ejemplos_anuncios = [
            ("¡Bienvenido a ComunidadPro!", "Nos alegra tenerte en la comunidad líder de creadores y desarrolladores. Explora los recursos multimedia y chatea en tiempo real."),
            ("Actualización del Sistema", "El sistema de almacenamiento y gestión de recursos está completamente operativo.")
        ]
        c.executemany("INSERT INTO anuncios (titulo, contenido) VALUES (?, ?)", ejl if 'ejl' in locals() else ejemplos_anuncios)
        conn.commit()

    # Tabla de configuración y personalización de la plataforma
    c.execute('''
        CREATE TABLE IF NOT EXISTS configuracion_plataforma (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')
    configs_default = [
        ("titulo_plataforma", "ComunidadPro"),
        ("color_principal", "#667eea"),
        ("color_secundario", "#764ba2"),
        ("mensaje_bienvenida", "Únete a nuestros grupos oficiales y descubre talento de creadores independientes."),
        ("footer_texto", "ComunidadPro - Todos los derechos reservados 2026"),
        ("modo_juegos_activo", "1")
    ]
    for k, v in configs_default:
        c.execute("INSERT OR IGNORE INTO configuracion_plataforma (clave, valor) VALUES (?, ?)", (k, v))
    conn.commit()

    conn.close()

init_db()

@app.context_processor
def inject_config():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT clave, valor FROM configuracion_plataforma").fetchall()
        conn.close()
        cfg = {row['clave']: row['valor'] for row in rows}
    except Exception:
        cfg = {
            "titulo_plataforma": "ComunidadPro",
            "color_principal": "#667eea",
            "color_secundario": "#764ba2",
            "mensaje_bienvenida": "Únete a nuestros grupos oficiales y descubre talento de creadores independientes.",
            "footer_texto": "ComunidadPro - Todos los derechos reservados 2026",
            "modo_juegos_activo": "1"
        }
    return dict(cfg=cfg)

def get_current_user():
    if "user_id" in session:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE id = ?", (session["user_id"],))
        user = c.fetchone()
        conn.close()
        if user:
            return dict(user)
    return None

def crear_notificacion(usuario_id, titulo, mensaje):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO notificaciones (usuario_id, titulo, mensaje) VALUES (?, ?, ?)", (usuario_id, titulo, mensaje))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM anuncios ORDER BY creado_en DESC LIMIT 5")
    anuncios = c.fetchall()
    c.execute("SELECT * FROM creadores WHERE estado_aprobacion = 'aprobado'")
    creadores_destacados = c.fetchall()
    c.execute("SELECT COUNT(*) FROM usuarios")
    total_miembros = c.fetchone()[0]
    c.execute("SELECT id, nombre, puntos_contribucion FROM usuarios ORDER BY puntos_contribucion DESC LIMIT 5")
    ranking = c.fetchall()
    
    # Encuesta activa
    c.execute("SELECT * FROM encuestas WHERE activa = 1 ORDER BY creado_en DESC LIMIT 1")
    encuesta_activa = c.fetchone()
    opciones = []
    if encuesta_activa:
        c.execute("SELECT * FROM opciones_encuesta WHERE encuesta_id = ?", (encuesta_activa['id'],))
        opciones = c.fetchall()

    conn.close()
    return render_template('community_index.html', usuario=get_current_user(), anuncios=anuncios, creadores=creadores_destacados, total_miembros=total_miembros, ranking=ranking, encuesta_activa=encuesta_activa, opciones=opciones)

@app.route('/ranking')
def ranking_comunidad():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios ORDER BY puntos_contribucion DESC")
    miembros = c.fetchall()
    conn.close()
    return render_template('community_ranking.html', usuario=get_current_user(), miembros=miembros)

@app.route('/about')
def about():
    return render_template('community_about.html', usuario=get_current_user())

@app.route('/recursos')
def recursos():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM recursos ORDER BY creado_en DESC")
    lista_recursos = c.fetchall()
    conn.close()
    return render_template('community_recursos.html', usuario=get_current_user(), recursos=lista_recursos)

@app.route('/encuestas', methods=['GET', 'POST'])
def encuestas_vista():
    user = get_current_user()
    if request.method == 'POST':
        if not user:
            flash("Inicia sesión para votar.", "error")
            return redirect(url_for('login'))
        encuesta_id = request.form.get('encuesta_id')
        opcion_id = request.form.get('opcion_id')
        if encuesta_id and opcion_id:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO votos_encuesta (encuesta_id, usuario_id, opcion_id) VALUES (?, ?, ?)",
                          (encuesta_id, user['id'], opcion_id))
                c.execute("UPDATE opciones_encuesta SET votos = votos + 1 WHERE id = ?", (opcion_id,))
                conn.commit()
                conn.close()
                flash("¡Tu voto ha sido registrado con éxito!", "success")
            except sqlite3.IntegrityError:
                flash("Ya has votado en esta encuesta.", "error")
        return redirect(url_for('encuestas_vista'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM encuestas ORDER BY creado_en DESC")
    encuestas = c.fetchall()
    
    resultado_encuestas = []
    for enc in encuestas:
        c.execute("SELECT * FROM opciones_encuesta WHERE encuesta_id = ?", (enc['id'],))
        ops = c.fetchall()
        ya_voto = False
        if user:
            c.execute("SELECT id FROM votos_encuesta WHERE encuesta_id = ? AND usuario_id = ?", (enc['id'], user['id']))
            ya_voto = c.fetchone() is not None
        resultado_encuestas.append({'encuesta': enc, 'opciones': ops, 'ya_voto': ya_voto})

    conn.close()
    return render_template('community_encuestas.html', usuario=user, resultado_encuestas=resultado_encuestas)

@app.route('/chat')
def chat_comunidad_vista():
    user = get_current_user()
    if not user:
        flash("Inicia sesión para acceder al chat.", "error")
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM chat_comunidad ORDER BY creado_en DESC LIMIT 50")
    mensajes = list(reversed(c.fetchall()))
    conn.close()
    return render_template('community_chat.html', usuario=user, mensajes=mensajes)

@socketio.on('enviar_mensaje')
def handle_mensaje(data):
    usuario_id = data.get('usuario_id')
    usuario_nombre = data.get('usuario_nombre')
    mensaje = data.get('mensaje')
    archivo = data.get('archivo')
    tipo_archivo = data.get('tipo_archivo')
    if (mensaje or archivo) and usuario_nombre:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO chat_comunidad (usuario_id, usuario_nombre, mensaje, archivo, tipo_archivo) VALUES (?, ?, ?, ?, ?)",
                  (usuario_id, usuario_nombre, mensaje or "", archivo, tipo_archivo))
        msg_id = c.lastrowid
        conn.commit()
        conn.close()
        emit('nuevo_mensaje', {
            'id': msg_id,
            'usuario_id': usuario_id,
            'usuario_nombre': usuario_nombre, 
            'mensaje': mensaje, 
            'archivo': archivo,
            'tipo_archivo': tipo_archivo,
            'creado_en': 'Hace un momento'
        }, broadcast=True)

@socketio.on('eliminar_mensaje')
def handle_eliminar_mensaje(data):
    mensaje_id = data.get('mensaje_id')
    usuario_id = data.get('usuario_id')
    if mensaje_id and usuario_id:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM chat_comunidad WHERE id = ?", (mensaje_id,))
        m = c.fetchone()
        if m:
            c.execute("SELECT rol FROM usuarios WHERE id = ?", (usuario_id,))
            u = c.fetchone()
            is_privileged = u and u['rol'] in ['admin', 'moderador']
            if m['usuario_id'] == usuario_id or is_privileged:
                c.execute("DELETE FROM chat_comunidad WHERE id = ?", (mensaje_id,))
                conn.commit()
                emit('mensaje_eliminado', {'mensaje_id': mensaje_id}, broadcast=True)
        conn.close()

@app.route('/reportar', methods=['POST'])
def reportar_contenido():
    user = get_current_user()
    if not user:
        flash("Inicia sesión para reportar.", "error")
        return redirect(url_for('index'))
    tipo = request.form.get('tipo') # 'chat' o 'creador'
    item_id = request.form.get('item_id')
    motivo = request.form.get('motivo')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO reportes (tipo, item_id, usuario_id, usuario_nombre, motivo) VALUES (?, ?, ?, ?, ?)",
              (tipo, item_id, user['id'], user['nombre'], motivo))
    conn.commit()
    conn.close()
    flash("Reporte enviado a los administradores. Gracias por mantener segura la comunidad.", "success")
    return redirect(request.referrer or url_for('index'))

@app.route('/chat/subir_archivo', methods=['POST'])
def chat_subir_archivo():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'No autorizado'}), 401
    
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se encontró archivo'}), 400
    file = request.files['archivo']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        unique_name = f"chat_{user['id']}_{os.urandom(4).hex()}_{filename}"
        file.save(os.path.join(UPLOAD_FOLDER, unique_name))
        
        tipo = 'documento'
        if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
            tipo = 'imagen'
        elif ext in {'mp4', 'webm', 'ogg', 'mov', 'mkv', 'avi'}:
            tipo = 'video'
        elif ext in {'mp3', 'wav', 'm4a', 'aac', 'ogg'}:
            tipo = 'audio'
            
        return {'url': url_for('static', filename=f'uploads/{unique_name}'), 'tipo': tipo}
    return jsonify({'error': 'Archivo no permitido'}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            if user['estado'] == 'suspendido':
                flash("Tu cuenta ha sido suspendida.", "error")
                return redirect(url_for('login'))
            session['user_id'] = user['id']
            flash("¡Bienvenido de nuevo!", "success")
            return redirect(url_for('dashboard'))
        flash("Credenciales incorrectas.", "error")
    return render_template('community_login.html', usuario=get_current_user())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        if not nombre or not email or not password:
            flash("Por favor completa todos los campos.", "error")
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password)
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (nombre, email, password, rol, puntos_contribucion) VALUES (?, ?, ?, 'miembro', 0)",
                      (nombre, email, hashed_pw))
            conn.commit()
            conn.close()
            flash("Registro exitoso. Por favor inicia sesión.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("El correo electrónico ya está registrado.", "error")
    return render_template('community_register.html', usuario=get_current_user())

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        flash("Inicia sesión para continuar.", "error")
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM enlaces_grupo")
    enlaces = c.fetchall()
    
    c.execute("SELECT * FROM creadores WHERE usuario_id = ?", (user['id'],))
    mi_perfil_creador = c.fetchone()

    c.execute("SELECT * FROM usuarios ORDER BY puntos_contribucion DESC LIMIT 10")
    top_aportantes = c.fetchall()

    c.execute("SELECT * FROM notificaciones WHERE usuario_id = ? ORDER BY creado_en DESC LIMIT 10", (user['id'],))
    notificaciones = c.fetchall()

    conn.close()
    
    return render_template('community_dashboard.html', usuario=user, enlaces=enlaces, mi_perfil_creador=mi_perfil_creador, top_aportantes=top_aportantes, notificaciones=notificaciones)

@app.route('/creadores')
def creadores():
    busqueda = request.args.get('q', '').strip()
    categoria = request.args.get('categoria', '').strip()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM creadores WHERE estado_aprobacion = 'aprobado'"
    params = []
    
    if busqueda:
        query += " AND (nombre_artistico LIKE ? OR biografia LIKE ?)"
        params.extend([f"%{busqueda}%", f"%{busqueda}%"])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
        
    c.execute(query, params)
    lista_creadores = c.fetchall()
    conn.close()
    
    return render_template('community_creadores.html', usuario=get_current_user(), creadores=lista_creadores, busqueda=busqueda, categoria_act=categoria)

@app.route('/creador/<int:creador_id>')
def detalle_creador(creador_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT c.*, u.email FROM creadores c JOIN usuarios u ON c.usuario_id = u.id WHERE c.id = ?", (creador_id,))
    creador = c.fetchone()
    if not creador:
        conn.close()
        flash("Creador no encontrado.", "error")
        return redirect(url_for('creadores'))
        
    c.execute("SELECT * FROM resenas WHERE creador_id = ? ORDER BY creado_en DESC", (creador_id,))
    resenas = c.fetchall()
    
    c.execute("SELECT AVG(calificacion) as promedio FROM resenas WHERE creador_id = ?", (creador_id,))
    promedio_res = c.fetchone()['promedio'] or 0

    c.execute("SELECT SUM(monto) as total_donado FROM donaciones WHERE creador_id = ?", (creador_id,))
    total_donado = c.fetchone()['total_donado'] or 0

    conn.close()
    return render_template('community_detalle_creador.html', usuario=get_current_user(), creador=creador, resenas=resenas, promedio_res=round(promedio_res, 1), total_donado=total_donado)

@app.route('/creador/<int:creador_id>/resenar', methods=['POST'])
def dejar_resena(creador_id):
    user = get_current_user()
    if not user:
        flash("Inicia sesión para dejar una reseña.", "error")
        return redirect(url_for('login'))
    calificacion = int(request.form.get('calificacion', 5))
    comentario = request.form.get('comentario', '')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO resenas (creador_id, usuario_id, usuario_nombre, calificacion, comentario) VALUES (?, ?, ?, ?, ?)",
              (creador_id, user['id'], user['nombre'], calificacion, comentario))
    
    c.execute("SELECT usuario_id FROM creadores WHERE id = ?", (creador_id,))
    creador_user = c.fetchone()
    if creador_user:
        crear_notificacion(creador_user[0], "Nueva reseña", f"{user['nombre']} ha calificado tu perfil con {calificacion}⭐")

    conn.commit()
    conn.close()
    flash("Reseña publicada con éxito.", "success")
    return redirect(url_for('detalle_creador', creador_id=creador_id))

@app.route('/creador/<int:creador_id>/donar', methods=['POST'])
def donar_creador(creador_id):
    user = get_current_user()
    if not user:
        flash("Inicia sesión para apoyar al creador.", "error")
        return redirect(url_for('login'))
    monto = float(request.form.get('monto', 5.0))
    mensaje = request.form.get('mensaje', '')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO donaciones (creador_id, usuario_id, usuario_nombre, monto, mensaje) VALUES (?, ?, ?, ?, ?)",
              (creador_id, user['id'], user['nombre'], monto, mensaje))
    
    c.execute("SELECT usuario_id FROM creadores WHERE id = ?", (creador_id,))
    creador_user = c.fetchone()
    if creador_user:
        crear_notificacion(creador_user[0], "Nuevo Apoyo / Donación", f"¡{user['nombre']} te ha apoyado con ${monto}! Mensaje: {mensaje}")

    conn.commit()
    conn.close()
    flash(f"¡Gracias! Has apoyado con éxito al creador por ${monto}.", "success")
    return redirect(url_for('detalle_creador', creador_id=creador_id))

@app.route('/creador/registro', methods=['GET', 'POST'])
def registrar_creador():
    user = get_current_user()
    if not user:
        flash("Inicia sesión para registrar tu perfil de creador.", "error")
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM creadores WHERE usuario_id = ?", (user['id'],))
    perfil = c.fetchone()
    
    if request.method == 'POST':
        nombre_artistico = request.form.get('nombre_artistico')
        categoria = request.form.get('categoria')
        biografia = request.form.get('biografia')
        enlace_contenido = request.form.get('enlace_contenido')
        redes = request.form.get('redes')
        
        avatar_filename = perfil['avatar'] if perfil else ''
        multimedia_filename = perfil['multimedia_destacada'] if perfil else ''
        
        if 'avatar' in request.files and request.files['avatar'].filename:
            f = request.files['avatar']
            if allowed_file(f.filename):
                avatar_filename = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD_FOLDER, avatar_filename))

        if 'multimedia' in request.files and request.files['multimedia'].filename:
            f = request.files['multimedia']
            if allowed_file(f.filename):
                multimedia_filename = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD_FOLDER, multimedia_filename))
        
        if perfil:
            c.execute("""
                UPDATE creadores SET nombre_artistico = ?, categoria = ?, biografia = ?, enlace_contenido = ?, redes = ?, avatar = ?, multimedia_destacada = ?, estado_aprobacion = 'pendiente'
                WHERE usuario_id = ?
            """, (nombre_artistico, categoria, biografia, enlace_contenido, redes, avatar_filename, multimedia_filename, user['id']))
            flash("Perfil actualizado y enviado a revisión.", "success")
        else:
            c.execute("""
                INSERT INTO creadores (usuario_id, nombre_artistico, categoria, biografia, enlace_contenido, redes, avatar, multimedia_destacada, estado_aprobacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pendiente')
            """, (user['id'], nombre_artistico, categoria, biografia, enlace_contenido, redes, avatar_filename, multimedia_filename))
            flash("Solicitud de creador enviada con éxito. Un administrador la revisará.", "success")
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('community_registrar_creador.html', usuario=user, perfil=perfil)

@app.route('/admin')
def admin_panel():
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        flash("Acceso denegado.", "error")
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios ORDER BY puntos_contribucion DESC")
    usuarios = c.fetchall()
    c.execute("SELECT c.*, u.email FROM creadores c JOIN usuarios u ON c.usuario_id = u.id")
    creadores = c.fetchall()
    c.execute("SELECT * FROM enlaces_grupo")
    enlaces = c.fetchall()
    c.execute("SELECT * FROM anuncios ORDER BY creado_en DESC")
    anuncios = c.fetchall()
    c.execute("SELECT * FROM recursos ORDER BY creado_en DESC")
    recursos = c.fetchall()
    c.execute("SELECT * FROM encuestas ORDER BY creado_en DESC")
    encuestas = c.fetchall()
    c.execute("SELECT * FROM reportes ORDER BY creado_en DESC")
    reportes = c.fetchall()
    conn.close()
    
    return render_template('community_admin.html', usuario=user, usuarios=usuarios, creadores=creadores, enlaces=enlaces, anuncios=anuncios, recursos=recursos, encuestas=encuestas, reportes=reportes)

@app.route('/admin/usuario/<int:uid>/rol', methods=['POST'])
def admin_cambiar_rol(uid):
    user = get_current_user()
    if not user or user['rol'] != 'admin':
        return redirect(url_for('index'))
    nuevo_rol = request.form.get('rol')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET rol = ? WHERE id = ?", (nuevo_rol, uid))
    conn.commit()
    conn.close()
    flash(f"Rol actualizado a {nuevo_rol}.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/usuario/<int:uid>/sumar_puntos', methods=['POST'])
def admin_sumar_puntos(uid):
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    puntos = int(request.form.get('puntos', 10))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET puntos_contribucion = puntos_contribucion + ? WHERE id = ?", (puntos, uid))
    conn.commit()
    conn.close()
    crear_notificacion(uid, "Puntos de Aporte", f"¡Has recibido {puntos} puntos de aporte!")
    flash(f"Se han sumado {puntos} puntos de aporte al usuario.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/creador/<int:creador_id>/<string:accion>')
def admin_revisar_creador(creador_id, accion):
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    
    nuevo_estado = 'aprobado' if accion == 'aprobar' else 'rechazado'
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE creadores SET estado_aprobacion = ? WHERE id = ?", (nuevo_estado, creador_id))
    
    c.execute("SELECT usuario_id, nombre_artistico FROM creadores WHERE id = ?", (creador_id,))
    creador_row = c.fetchone()
    if creador_row:
        creador_uid = creador_row['usuario_id']
        if nuevo_estado == 'aprobado':
            c.execute("UPDATE usuarios SET rol = 'creador' WHERE id = ?", (creador_uid,))
            crear_notificacion(creador_uid, "Perfil Aprobado", "¡Tu perfil de creador ha sido aprobado!")
        else:
            crear_notificacion(creador_uid, "Perfil Rechazado", "Tu solicitud de perfil de creador fue rechazada.")

    conn.commit()
    conn.close()
    flash(f"Perfil de creador {nuevo_estado}.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/encuesta/crear', methods=['POST'])
def admin_crear_encuesta():
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    pregunta = request.form.get('pregunta')
    opciones = request.form.getlist('opciones')
    
    if pregunta and opciones:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO encuestas (pregunta) VALUES (?)", (pregunta,))
        encuesta_id = c.lastrowid
        for op in opciones:
            if op.strip():
                c.execute("INSERT INTO opciones_encuesta (encuesta_id, texto) VALUES (?, ?)", (encuesta_id, op.strip()))
        conn.commit()
        conn.close()
        flash("Encuesta creada con éxito.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/encuesta/<int:encuesta_id>/cerrar')
def admin_cerrar_encuesta(encuesta_id):
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE encuestas SET activa = 0 WHERE id = ?", (encuesta_id,))
    conn.commit()
    conn.close()
    flash("Encuesta cerrada.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/exportar/<string:tipo>')
def admin_exportar_csv(tipo):
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if tipo == 'usuarios':
        c.execute("SELECT id, nombre, email, rol, estado, puntos_contribucion, creado_en FROM usuarios")
        writer.writerow(['ID', 'Nombre', 'Email', 'Rol', 'Estado', 'Puntos Aporte', 'Creado En'])
    elif tipo == 'creadores':
        c.execute("SELECT id, usuario_id, nombre_artistico, categoria, enlace_contenido, estado_aprobacion FROM creadores")
        writer.writerow(['ID', 'Usuario ID', 'Nombre Artístico', 'Categoría', 'Enlace', 'Estado Aprobación'])
    elif tipo == 'ranking':
        c.execute("SELECT id, nombre, email, puntos_contribucion FROM usuarios ORDER BY puntos_contribucion DESC")
        writer.writerow(['ID', 'Nombre', 'Email', 'Puntos de Aporte'])
    else:
        conn.close()
        return redirect(url_for('admin_panel'))
        
    rows = c.fetchall()
    for row in rows:
        writer.writerow(list(row))
    conn.close()
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=reporte_{tipo}.csv"}
    )

@app.route('/admin/enlace/agregar', methods=['POST'])
def admin_agregar_enlace():
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    
    titulo = request.form.get('titulo')
    url = request.form.get('url')
    descripcion = request.form.get('descripcion')
    categoria = request.form.get('categoria', 'WhatsApp')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO enlaces_grupo (titulo, url, descripcion, categoria) VALUES (?, ?, ?, ?)",
              (titulo, url, descripcion, categoria))
    conn.commit()
    conn.close()
    flash("Enlace de grupo agregado.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/nivel/agregar', methods=['POST'])
def admin_agregar_nivel():
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    
    try:
        numero_nivel = int(request.form.get('numero_nivel', 1))
        nombre_nivel = request.form.get('nombre_nivel', 'Nuevo Nivel')
        bichos_velocidad = float(request.form.get('bichos_velocidad', 1.5))
        descripcion = request.form.get('descripcion', '')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO niveles_personalizados (numero_nivel, nombre_nivel, bichos_velocidad, descripcion) VALUES (?, ?, ?, ?)",
                  (numero_nivel, nombre_nivel, bichos_velocidad, descripcion))
        conn.commit()
        conn.close()
        flash("Nivel personalizado agregado/actualizado con éxito.", "success")
    except Exception as e:
        flash(f"Error al agregar nivel: {e}", "error")
    return redirect(url_for('admin_panel'))

@app.route('/admin/enlace/<int:enlace_id>/eliminar')
def admin_eliminar_enlace(enlace_id):
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM enlaces_grupo WHERE id = ?", (enlace_id,))
    conn.commit()
    conn.close()
    flash("Enlace eliminado.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/anuncio/agregar', methods=['POST'])
def admin_agregar_anuncio():
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    
    titulo = request.form.get('titulo')
    contenido = request.form.get('contenido')
    archivo_anuncio = ''
    
    if 'archivo' in request.files and request.files['archivo'].filename:
        f = request.files['archivo']
        if allowed_file(f.filename):
            archivo_anuncio = secure_filename(f.filename)
            f.save(os.path.join(UPLOAD_FOLDER, archivo_anuncio))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO anuncios (titulo, contenido, archivo) VALUES (?, ?, ?)", (titulo, contenido, archivo_anuncio))
    conn.commit()
    conn.close()
    flash("Anuncio publicado.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/anuncio/<int:anuncio_id>/eliminar')
def admin_eliminar_anuncio(anuncio_id):
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM anuncios WHERE id = ?", (anuncio_id,))
    conn.commit()
    conn.close()
    flash("Anuncio eliminado.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/recurso/agregar', methods=['POST'])
def admin_agregar_recurso():
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    
    if 'archivo' not in request.files:
        flash("Debes adjuntar un archivo.", "error")
        return redirect(url_for('admin_panel'))
        
    f = request.files['archivo']
    if f and allowed_file(f.filename):
        filename = secure_filename(f.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        f.save(os.path.join(UPLOAD_FOLDER, filename))
        
        tipo = 'documento'
        if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
            tipo = 'imagen'
        elif ext in {'mp4', 'webm', 'ogg', 'mov', 'mkv', 'avi'}:
            tipo = 'video'
        elif ext in {'mp3', 'wav', 'm4a', 'aac', 'ogg'}:
            tipo = 'audio'
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO recursos (titulo, descripcion, archivo, tipo) VALUES (?, ?, ?, ?)",
                  (titulo, descripcion, filename, tipo))
        conn.commit()
        conn.close()
        flash("Recurso multimedia agregado con éxito.", "success")
    else:
        flash("Formato de archivo no válido.", "error")
    return redirect(url_for('admin_panel'))

@app.route('/admin/recurso/<int:recurso_id>/eliminar')
def admin_eliminar_recurso(recurso_id):
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        return redirect(url_for('index'))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM recursos WHERE id = ?", (recurso_id,))
    conn.commit()
    conn.close()
    flash("Recurso eliminado.", "success")
    return redirect(url_for('admin_panel'))

# --- MÓDULO DE ALMACENAMIENTO ---
MAX_STORAGE_QUOTA = 100 * 1024 * 1024 # 100 MB

def get_user_storage_used(usuario_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(tamano) FROM archivos_almacenamiento WHERE usuario_id = ?", (usuario_id,))
    total = c.fetchone()[0]
    conn.close()
    return total or 0

@app.route('/almacenamiento')
def almacenamiento_vista():
    user = get_current_user()
    if not user:
        flash("Debes iniciar sesión para ver tu almacenamiento.", "error")
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM archivos_almacenamiento WHERE usuario_id = ? ORDER BY creado_en DESC", (user['id'],))
    archivos = [dict(row) for row in c.fetchall()]
    conn.close()
    
    usado = get_user_storage_used(user['id'])
    return render_template('community_almacenamiento.html', usuario=user, archivos=archivos, usado=usado, quota=MAX_STORAGE_QUOTA)

@app.route('/almacenamiento/subir', methods=['POST'])
def almacenamiento_subir():
    user = get_current_user()
    if not user:
        flash("Debes iniciar sesión.", "error")
        return redirect(url_for('login'))
        
    if 'archivo' not in request.files:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for('almacenamiento_vista'))
        
    f = request.files['archivo']
    if f and allowed_file(f.filename):
        nombre_original = secure_filename(f.filename)
        ext = nombre_original.rsplit('.', 1)[1].lower()
        nombre_guardado = f"usr_{user['id']}_{os.urandom(4).hex()}_{nombre_original}"
        
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        f.seek(0)
        
        usado_actual = get_user_storage_used(user['id'])
        if usado_actual + file_size > MAX_STORAGE_QUOTA:
            flash("Has superado tu cuota de almacenamiento de 100 MB.", "error")
            return redirect(url_for('almacenamiento_vista'))
            
        file_path = os.path.join(UPLOAD_FOLDER, nombre_guardado)
        f.save(file_path)
        
        tipo = 'documento'
        if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
            tipo = 'imagen'
        elif ext in {'mp4', 'webm', 'ogg', 'mov', 'mkv', 'avi'}:
            tipo = 'video'
        elif ext in {'mp3', 'wav', 'm4a', 'aac', 'ogg'}:
            tipo = 'audio'
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO archivos_almacenamiento (usuario_id, nombre_original, nombre_guardado, tipo, tamano) VALUES (?, ?, ?, ?, ?)",
                  (user['id'], nombre_original, nombre_guardado, tipo, file_size))
        conn.commit()
        conn.close()
        flash("Archivo subido con éxito al almacenamiento.", "success")
    else:
        flash("Formato de archivo no permitido.", "error")
    return redirect(url_for('almacenamiento_vista'))

@app.route('/almacenamiento/<int:archivo_id>/eliminar')
def almacenamiento_eliminar(archivo_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM archivos_almacenamiento WHERE id = ? AND usuario_id = ?", (archivo_id, user['id']))
    archivo = c.fetchone()
    if archivo:
        file_path = os.path.join(UPLOAD_FOLDER, archivo['nombre_guardado'])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        c.execute("DELETE FROM archivos_almacenamiento WHERE id = ?", (archivo_id,))
        conn.commit()
        flash("Archivo eliminado del almacenamiento.", "success")
    else:
        flash("Archivo no encontrado o sin permisos.", "error")
    conn.close()
    return redirect(url_for('almacenamiento_vista'))

@app.route('/cine')
def cine_david():
    user = get_current_user()
    return render_template('cine_david.html', usuario=user)

@app.route('/admin/usuario/<int:uid>/eliminar', methods=['POST'])
def admin_eliminar_usuario(uid):
    user = get_current_user()
    if not user or user['rol'] != 'admin':
        flash("Acceso no autorizado.", "error")
        return redirect(url_for('admin_panel'))
    conn = sqlite3.connect(DB_PATH)
    if uid == user['id']:
        flash("No puedes eliminar tu propia cuenta de administrador principal.", "error")
        conn.close()
        return redirect(url_for('admin_panel'))
    conn.execute("DELETE FROM usuarios WHERE id = ?", (uid,))
    conn.commit()
    conn.close()
    flash("Usuario y sus datos asociados eliminados correctamente.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/personalizar', methods=['POST'])
def admin_personalizar():
    user = get_current_user()
    if not user or user['rol'] not in ['admin', 'moderador']:
        flash("Acceso no autorizado.", "error")
        return redirect(url_for('admin_panel'))
    
    titulo = request.form.get('titulo_plataforma', 'ComunidadPro')
    c_principal = request.form.get('color_principal', '#667eea')
    c_secundario = request.form.get('color_secundario', '#764ba2')
    mensaje = request.form.get('mensaje_bienvenida', '')
    footer = request.form.get('footer_texto', '')
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO configuracion_plataforma (clave, valor) VALUES ('titulo_plataforma', ?)", (titulo,))
    conn.execute("INSERT OR REPLACE INTO configuracion_plataforma (clave, valor) VALUES ('color_principal', ?)", (c_principal,))
    conn.execute("INSERT OR REPLACE INTO configuracion_plataforma (clave, valor) VALUES ('color_secundario', ?)", (c_secundario,))
    conn.execute("INSERT OR REPLACE INTO configuracion_plataforma (clave, valor) VALUES ('mensaje_bienvenida', ?)", (mensaje,))
    conn.execute("INSERT OR REPLACE INTO configuracion_plataforma (clave, valor) VALUES ('footer_texto', ?)", (footer,))
    conn.commit()
    conn.close()
    flash("Personalización de la plataforma guardada con éxito.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/mantenimiento/<string:accion>')
def admin_mantenimiento(accion):
    user = get_current_user()
    if not user or user['rol'] != 'admin':
        flash("Acceso no autorizado.", "error")
        return redirect(url_for('admin_panel'))
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if accion == 'optimizar':
        c.execute("VACUUM")
        flash("Base de datos optimizada (VACUUM ejecutado).", "success")
    elif accion == 'vaciar_chat':
        c.execute("DELETE FROM chat_comunidad")
        conn.commit()
        flash("Historial del chat de la comunidad vaciado.", "success")
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/juegos')
def zona_juegos():
    user = get_current_user()
    return render_template('community_juegos.html', usuario=user)

@app.route('/juegos/ganar_puntos', methods=['POST'])
def juegos_ganar_puntos():
    user = get_current_user()
    if not user:
        return jsonify({"status": "error", "message": "No autenticado"}), 401
    
    puntos = int(request.json.get('puntos', 5))
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE usuarios SET puntos_contribucion = puntos_contribucion + ? WHERE id = ?", (puntos, user['id']))
    conn.commit()
    conn.close()
    crear_notificacion(user['id'], "Zona de Juegos", f"¡Has ganado {puntos} puntos de contribución jugando en la plataforma!")
    return jsonify({"status": "success", "puntos": puntos})

@app.route('/juego-arena')
def juego_arena():
    user = get_current_user()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, nombre, puntos_contribucion FROM usuarios ORDER BY puntos_contribucion DESC LIMIT 10")
    top_jugadores = c.fetchall()
    conn.close()
    return render_template('codebox_arena.html', usuario=user, top_jugadores=top_jugadores)

@app.route('/juego-arena/guardar_score', methods=['POST'])
def juego_arena_guardar_score():
    user = get_current_user()
    if not user:
        return jsonify({"status": "error", "message": "No autenticado"}), 401
    
    data = request.json
    kills = int(data.get('kills', 0))
    diff_level = int(data.get('diffLevel', min(1000, int(kills * 1.5) + 1)))
    challenge_accepted = bool(data.get('challengeAccepted', False))
    
    puntos_base = kills * 2
    bonus_reto = 0
    mensaje_reto = ""
    
    if challenge_accepted:
        if diff_level >= 1000:
            bonus_reto = 10000
            mensaje_reto = "🏆 ¡IMPRESIONANTE! ¡Aceptaste el reto y alcanzaste el Nivel 1000, ganando 10,000 puntos de bono!"
        elif diff_level >= 785:
            bonus_reto = 2500
            mensaje_reto = "⭐ ¡EXCELENTE! ¡Aceptaste el reto y llegaste al Nivel 785+, ganando 2,500 puntos de bono!"
        else:
            mensaje_reto = f"🛡️ Participaste en el reto CodeBox (Nivel {diff_level}). ¡Sigue practicando para alcanzar la meta!"
    
    puntos_ganados = puntos_base + bonus_reto
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE usuarios SET puntos_contribucion = puntos_contribucion + ?, nivel_maximo = MAX(COALESCE(nivel_maximo, 1), ?) WHERE id = ?", (puntos_ganados, diff_level, user['id']))
    conn.commit()
    
    c = conn.cursor()
    c.execute("SELECT puntos_contribucion FROM usuarios WHERE id = ?", (user['id'],))
    nuevo_total = c.fetchone()[0]
    conn.close()
    
    notif_msg = f"¡Partida terminada! Has conseguido {kills} bajas (Nivel {diff_level}) y ganado {puntos_ganados} puntos de contribución para la competencia."
    if mensaje_reto:
        notif_msg += f" {mensaje_reto}"
    
    crear_notificacion(user['id'], "CodeBox Game Arena - Reto", notif_msg)
    return jsonify({
        "status": "success", 
        "kills": kills, 
        "diffLevel": diff_level,
        "challengeAccepted": challenge_accepted,
        "puntos_ganados": puntos_ganados, 
        "mensaje_reto": mensaje_reto,
        "nuevo_total": nuevo_total
    })

@app.route('/health')
def health_check():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT 1")
        conn.close()
        return jsonify({"status": "ok", "database": "connected", "db_path": DB_PATH}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.cli.command("init-db")
def init_db_command():
    """Inicializa la base de datos de la comunidad."""
    init_db()
    print("Base de datos inicializada correctamente.")

# 1v1 Realtime Multiplayer Arena Socket Events
waiting_player = None

@socketio.on('join_arena_1v1')
def handle_join_arena(data):
    global waiting_player
    user_name = data.get('nombre', 'Jugador')
    sid = request.sid
    if waiting_player and waiting_player['sid'] != sid:
        room = f"room_{waiting_player['sid']}_{sid}"
        socketio.server.enter_room(waiting_player['sid'], room)
        socketio.server.enter_room(sid, room)
        
        match_data = {
            'room': room,
            'player1': waiting_player['nombre'],
            'player2': user_name
        }
        socketio.emit('start_1v1_match', match_data, room=room)
        waiting_player = None
    else:
        waiting_player = {'sid': sid, 'nombre': user_name}
        emit('waiting_for_opponent', {'message': 'Buscando oponente 1v1 en línea...'})

@socketio.on('player_action_1v1')
def handle_player_action(data):
    room = data.get('room')
    if room:
        emit('opponent_action', data, room=room, include_self=False)

@app.cli.command("db-stats")
def db_stats_command():
    """Muestra estadísticas del sistema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM usuarios")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM archivos_almacenamiento")
    files = c.fetchone()[0]
    conn.close()
    print(f"--- Estadísticas ComunidadPro ---")
    print(f"Usuarios registrados: {users}")
    print(f"Archivos almacenados: {files}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    print(f"Iniciando aplicación en puerto {port}...")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
