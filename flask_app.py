import os, sqlite3, uuid, json, urllib.request, dotenv
import google.generativeai as genai
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Cargar variables de entorno
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
# Configuración segura desde variables de entorno
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_change_me")
base_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(base_dir, "database.db"))
USER_FILES_FOLDER = os.path.join(base_dir, "user_files")
os.makedirs(USER_FILES_FOLDER, exist_ok=True)
WOMPI_PUBLIC_KEY = os.environ.get("WOMPI_PUBLIC_KEY")
WOMPI_PRIVATE_KEY = os.environ.get("WOMPI_PRIVATE_KEY")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
EXTENSIONES_PERMITIDAS = {"png","jpg","jpeg","gif","webp","py","html","js","css"}

def extension_valida(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in EXTENSIONES_PERMITIDAS

DESAFIOS = [
    {"id":1,"tema":"HTML","icono":"🏗️","titulo":"Primera etiqueta","descripcion":"Escribe un h1 que diga Hola","pista":"&lt;h1&gt;Hola&lt;/h1&gt;","instrucciones":"Las etiquetas HTML van entre menor y mayor que.","xp":30,"dificultad":"Fácil","tipo":"exacto","solucion":"<h1>hola</h1>","nivel_requerido":0},
    {"id":2,"tema":"HTML","icono":"🏗️","titulo":"Párrafo","descripcion":"Crea un párrafo con: Bienvenido a Génesis","pista":"&lt;p&gt;Bienvenido a Génesis&lt;/p&gt;","instrucciones":"La etiqueta p define un párrafo.","xp":30,"dificultad":"Fácil","tipo":"exacto","solucion":"<p>bienvenido a génesis</p>","nivel_requerido":1},
    {"id":3,"tema":"HTML","icono":"🏗️","titulo":"Lista","descripcion":"Lista con Python, HTML, CSS","pista":"ul con tres li","instrucciones":"ul es el contenedor, li cada elemento.","xp":40,"dificultad":"Fácil","tipo":"contiene","solucion":["<ul>","<li>python</li>","<li>html</li>","<li>css</li>","</ul>"],"nivel_requerido":2},
    {"id":4,"tema":"HTML","icono":"🏗️","titulo":"Enlace","descripcion":"Enlace a https://google.com con texto Google","pista":"&lt;a href='https://google.com'&gt;Google&lt;/a&gt;","instrucciones":"Los enlaces usan la etiqueta a con href.","xp":40,"dificultad":"Fácil","tipo":"contiene","solucion":["href=\"https://google.com\"",">google<"],"nivel_requerido":3},
    {"id":5,"tema":"HTML","icono":"🏗️","titulo":"Estructura base","descripcion":"Estructura mínima con html, head y body","pista":"html head body","instrucciones":"Toda página tiene html, head y body.","xp":50,"dificultad":"Media","tipo":"contiene","solucion":["<html>","<head>","<body>","</body>","</html>"],"nivel_requerido":4},
    {"id":6,"tema":"CSS","icono":"🎨","titulo":"Color rojo","descripcion":"Pon el texto del body en rojo","pista":"body { color: red; }","instrucciones":"CSS: selector { propiedad: valor; }","xp":40,"dificultad":"Fácil","tipo":"contiene","solucion":["body","color","red"],"nivel_requerido":5},
    {"id":7,"tema":"CSS","icono":"🎨","titulo":"Fondo negro","descripcion":"Fondo del body en negro","pista":"body { background-color: black; }","instrucciones":"background-color cambia el fondo.","xp":40,"dificultad":"Fácil","tipo":"contiene","solucion":["body","background-color","black"],"nivel_requerido":6},
    {"id":8,"tema":"CSS","icono":"🎨","titulo":"Tamaño fuente","descripcion":"Párrafos con font-size 20px","pista":"p { font-size: 20px; }","instrucciones":"font-size controla el tamaño del texto.","xp":50,"dificultad":"Media","tipo":"contiene","solucion":["p","font-size","20px"],"nivel_requerido":7},
    {"id":9,"tema":"CSS","icono":"🎨","titulo":"Centrar texto","descripcion":"Centra el texto de los h1","pista":"h1 { text-align: center; }","instrucciones":"text-align alinea el texto.","xp":50,"dificultad":"Media","tipo":"contiene","solucion":["h1","text-align","center"],"nivel_requerido":8},
    {"id":10,"tema":"CSS","icono":"🎨","titulo":"Clase CSS","descripcion":".destacado con fondo yellow y texto bold","pista":".destacado { background-color: yellow; font-weight: bold; }","instrucciones":"Las clases se definen con punto.","xp":60,"dificultad":"Media","tipo":"contiene","solucion":[".destacado","background-color","yellow","font-weight","bold"],"nivel_requerido":9},
    {"id":11,"tema":"JavaScript","icono":"⚡","titulo":"Variable","descripcion":"Declara nombre con valor David","pista":"let nombre = 'David';","instrucciones":"let declara variables en JS moderno.","xp":50,"dificultad":"Media","tipo":"contiene","solucion":["let nombre","david"],"nivel_requerido":10},
    {"id":12,"tema":"JavaScript","icono":"⚡","titulo":"Alert","descripcion":"Muestra alerta con Hola Mundo","pista":"alert('Hola Mundo');","instrucciones":"alert() muestra un mensaje emergente.","xp":50,"dificultad":"Media","tipo":"contiene","solucion":["alert","hola mundo"],"nivel_requerido":11},
    {"id":13,"tema":"JavaScript","icono":"⚡","titulo":"Función","descripcion":"Función saludar() que retorne Hola","pista":"function saludar() { return 'Hola'; }","instrucciones":"Las funciones son bloques reutilizables.","xp":60,"dificultad":"Media","tipo":"contiene","solucion":["function saludar","return"],"nivel_requerido":12},
    {"id":14,"tema":"JavaScript","icono":"⚡","titulo":"Condicional","descripcion":"Si edad mayor a 18 imprime Mayor en consola","pista":"if (edad > 18) { console.log('Mayor'); }","instrucciones":"if ejecuta código si la condición es verdadera.","xp":70,"dificultad":"Media","tipo":"contiene","solucion":["if","edad","> 18","console.log"],"nivel_requerido":13},
    {"id":15,"tema":"JavaScript","icono":"⚡","titulo":"Bucle for","descripcion":"Imprime números del 1 al 5","pista":"for (let i = 1; i <= 5; i++) { console.log(i); }","instrucciones":"El for repite código un número de veces.","xp":80,"dificultad":"Difícil","tipo":"contiene","solucion":["for","i = 1","i <= 5","console.log"],"nivel_requerido":14},
    {"id":16,"tema":"Python","icono":"🐍","titulo":"Hola Mundo","descripcion":"Imprime Hola Mundo en Python","pista":"print('Hola Mundo')","instrucciones":"print() muestra texto en consola.","xp":50,"dificultad":"Fácil","tipo":"contiene","solucion":["print","hola mundo"],"nivel_requerido":15},
    {"id":17,"tema":"Python","icono":"🐍","titulo":"Variable","descripcion":"Declara edad igual a 20 e imprímela","pista":"edad = 20 luego print(edad)","instrucciones":"En Python asignas con igual sin declarar tipo.","xp":50,"dificultad":"Fácil","tipo":"contiene","solucion":["edad = 20","print"],"nivel_requerido":16},
    {"id":18,"tema":"Python","icono":"🐍","titulo":"Lista","descripcion":"Lista frutas con manzana pera uva","pista":"frutas = ['manzana', 'pera', 'uva']","instrucciones":"Las listas usan corchetes.","xp":60,"dificultad":"Media","tipo":"contiene","solucion":["frutas = [","manzana","pera","uva"],"nivel_requerido":17},
    {"id":19,"tema":"Python","icono":"🐍","titulo":"Función","descripcion":"Función suma que reciba a y b y retorne la suma","pista":"def suma(a, b): return a + b","instrucciones":"Las funciones Python usan def.","xp":70,"dificultad":"Media","tipo":"contiene","solucion":["def suma","return a + b"],"nivel_requerido":18},
    {"id":20,"tema":"Python","icono":"🐍","titulo":"Bucle","descripcion":"Imprime números del 1 al 10","pista":"for i in range(1, 11): print(i)","instrucciones":"range(1,11) genera del 1 al 10.","xp":80,"dificultad":"Media","tipo":"contiene","solucion":["for i in range","print"],"nivel_requerido":19},
    {"id":21,"tema":"Python","icono":"🐍","titulo":"Diccionario","descripcion":"Diccionario persona con nombre y edad","pista":"persona = {'nombre': 'David', 'edad': 20}","instrucciones":"Los diccionarios guardan pares clave valor.","xp":90,"dificultad":"Difícil","tipo":"contiene","solucion":["persona = {","nombre","edad"],"nivel_requerido":20},
    {"id":22,"tema":"Python","icono":"🐍","titulo":"Clase","descripcion":"Clase Animal con init que acepte nombre","pista":"class Animal:\n    def __init__(self, nombre):\n        self.nombre = nombre","instrucciones":"Las clases son plantillas para crear objetos.","xp":120,"dificultad":"Experto","tipo":"contiene","solucion":["class animal","def __init__","self.nombre"],"nivel_requerido":21},
    {"id":23,"tema":"Python","icono":"🐍","titulo":"List Comprehension","descripcion":"Crea una lista de los cuadrados de los números del 1 al 5 usando comprensión de listas.","pista":"[x**2 for x in range(1, 6)]","instrucciones":"La comprensión de listas es una forma concisa de crear listas: [expresion for item in iterable].","xp":100,"dificultad":"Difícil","tipo":"contiene","solucion":["[","for","in range","**2"],"nivel_requerido":22},
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuario (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(50) NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, password VARCHAR(100) NOT NULL, puntos INTEGER DEFAULT 0, nivel VARCHAR(50) DEFAULT "Iniciado", plan TEXT DEFAULT "gratis", es_admin INTEGER DEFAULT 0)''')
    for col in ["plan TEXT DEFAULT 'gratis'", "es_admin INTEGER DEFAULT 0"]:
        try: c.execute(f"ALTER TABLE usuario ADD COLUMN {col}")
        except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS progreso (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, desafio_id INTEGER NOT NULL, UNIQUE(usuario_id, desafio_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS lecciones (id INTEGER PRIMARY KEY AUTOINCREMENT, modulo TEXT, titulo TEXT, contenido TEXT, es_premium INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mensajes (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, usuario_nombre TEXT, contenido TEXT, codigo TEXT DEFAULT "", creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS comentarios (id INTEGER PRIMARY KEY AUTOINCREMENT, mensaje_id INTEGER, usuario_id INTEGER, usuario_nombre TEXT, contenido TEXT, creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reacciones (id INTEGER PRIMARY KEY AUTOINCREMENT, mensaje_id INTEGER, usuario_id INTEGER, tipo TEXT, UNIQUE(mensaje_id, usuario_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, usuario_nombre TEXT, mensaje TEXT, imagen TEXT, archivo TEXT, respondiendo_a INTEGER, creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    for col in ["imagen TEXT", "archivo TEXT", "respondiendo_a INTEGER"]:
        try: c.execute(f"ALTER TABLE chat ADD COLUMN {col}")
        except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS chat_reacciones (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, usuario_id INTEGER, tipo TEXT, UNIQUE(chat_id, usuario_id))''')
    c.execute("UPDATE usuario SET es_admin=1 WHERE nombre='david_achipiz'")
    conn.commit()
    conn.close()

init_db()

def get_user():
    if "user_id" in session:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id,nombre,email,puntos,plan,es_admin FROM usuario WHERE id=?", (session["user_id"],))
        u = c.fetchone()
        conn.close()
        if u:
            return {"id":u["id"],"nombre":u["nombre"],"email":u["email"] or "","puntos":u["puntos"] or 0,"plan":u["plan"] or "gratis","es_admin":u["es_admin"] or 0,"is_authenticated":True}
    return {"is_authenticated":False}

def verificar_sol(d, codigo_raw):
    codigo = codigo_raw.strip().lower()
    if d["tipo"] == "exacto":
        return codigo.replace(" ","").replace("\n","") == d["solucion"].replace(" ","").replace("\n","")
    return all(p.lower() in codigo for p in d["solucion"])

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT nombre,puntos,plan FROM usuario ORDER BY puntos DESC")
    torneo = c.fetchall()
    conn.close()
    return render_template('index.html', torneo=torneo, usuario=get_user())

@app.route('/dashboard')
def dashboard():
    u = get_user()
    if not u["is_authenticated"]:
        flash("Inicia sesión.", "error")
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT desafio_id FROM progreso WHERE usuario_id=?", (u["id"],))
    completados = {r[0] for r in c.fetchall()}
    conn.close()
    total = len(DESAFIOS)
    progreso_pct = int((len(completados)/total)*100)
    temas = {}
    for d in DESAFIOS:
        t = d["tema"]
        if t not in temas:
            temas[t] = []
        temas[t].append({**d,"completado":d["id"] in completados,"bloqueado":d["nivel_requerido"]>len(completados)})
    return render_template('dashboard.html', usuario=u, temas=temas, completados=len(completados), total=total, progreso_pct=progreso_pct)

@app.route('/desafio/<int:did>', methods=['GET','POST'])
def desafio(did):
    u = get_user()
    if not u["is_authenticated"]:
        flash("Inicia sesión.", "error")
        return redirect(url_for('login'))
    d = next((x for x in DESAFIOS if x["id"]==did), None)
    if not d:
        flash("No encontrado.", "error")
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT desafio_id FROM progreso WHERE usuario_id=?", (u["id"],))
    completados = {r[0] for r in c.fetchall()}
    conn.close()
    if d["nivel_requerido"] > len(completados):
        flash(f"Completa {d['nivel_requerido']} desafíos primero.", "error")
        return redirect(url_for('dashboard'))
    ya = did in completados
    if request.method == 'POST':
        codigo = request.form.get('codigo','')
        if verificar_sol(d, codigo):
            if not ya:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO progreso (usuario_id,desafio_id) VALUES (?,?)", (u["id"],did))
                c.execute("UPDATE usuario SET puntos=puntos+? WHERE id=?", (d["xp"],u["id"]))
                conn.commit()
                conn.close()
                flash(f"Correcto! +{d['xp']} XP", "success")
            else:
                flash("Ya completado!", "success")
            return redirect(url_for('dashboard'))
        flash("Respuesta incorrecta. Revisa la pista.", "error")
    return render_template('desafio.html', usuario=u, d=d, ya_completado=ya)

@app.route('/admin')
def admin():
    u = get_user()
    if not (u.get("is_authenticated") and u.get("es_admin")):
        flash("Acceso denegado.", "error")
        return redirect(url_for('index'))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM usuario ORDER BY puntos DESC")
    usuarios = c.fetchall()
    c.execute("SELECT COUNT(*) FROM usuario"); tu = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM usuario WHERE plan='premium'"); tp = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM mensajes"); tm = c.fetchone()[0]
    c.execute("SELECT SUM(puntos) FROM usuario"); tx = c.fetchone()[0] or 0
    c.execute("SELECT * FROM mensajes ORDER BY creado_en DESC LIMIT 20")
    mensajes = c.fetchall()
    conn.close()
    return render_template('admin.html', usuario=u, usuarios=usuarios, total_usuarios=tu, total_premium=tp, total_mensajes=tm, total_xp=tx, mensajes=mensajes)

@app.route('/admin/usuario/<int:uid>/premium')
def admin_dar_premium(uid):
    u = get_user()
    if not (u.get("is_authenticated") and u.get("es_admin")): return redirect(url_for('index'))
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("UPDATE usuario SET plan='premium' WHERE id=?", (uid,)); conn.commit(); conn.close()
    flash("Premium activado.", "success"); return redirect(url_for('admin'))

@app.route('/admin/usuario/<int:uid>/gratis')
def admin_quitar_premium(uid):
    u = get_user()
    if not (u.get("is_authenticated") and u.get("es_admin")): return redirect(url_for('index'))
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("UPDATE usuario SET plan='gratis' WHERE id=?", (uid,)); conn.commit(); conn.close()
    flash("Plan cambiado.", "success"); return redirect(url_for('admin'))

@app.route('/admin/usuario/<int:uid>/eliminar')
def admin_eliminar_usuario(uid):
    u = get_user()
    if not (u.get("is_authenticated") and u.get("es_admin")): return redirect(url_for('index'))
    if uid == u["id"]: flash("No puedes eliminarte.", "error"); return redirect(url_for('admin'))
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM usuario WHERE id=?", (uid,)); conn.commit(); conn.close()
    flash("Eliminado.", "success"); return redirect(url_for('admin'))

@app.route('/admin/mensaje/<int:mid>/eliminar')
def admin_eliminar_mensaje(mid):
    u = get_user()
    if not (u.get("is_authenticated") and u.get("es_admin")): return redirect(url_for('index'))
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM mensajes WHERE id=?", (mid,)); conn.commit(); conn.close()
    flash("Eliminado.", "success"); return redirect(url_for('admin'))

@app.route('/admin/usuario/<int:uid>/puntos', methods=['POST'])
def admin_editar_puntos(uid):
    u = get_user()
    if not (u.get("is_authenticated") and u.get("es_admin")): return redirect(url_for('index'))
    puntos = int(request.form.get('puntos',0))
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("UPDATE usuario SET puntos=? WHERE id=?", (puntos,uid)); conn.commit(); conn.close()
    flash("XP actualizado.", "success"); return redirect(url_for('admin'))

@app.route('/chat')
def chat():
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM chat ORDER BY creado_en DESC LIMIT 50")
    raw = list(reversed(c.fetchall()))
    mensajes = []
    for m in raw:
        c.execute("SELECT tipo, COUNT(*) as total FROM chat_reacciones WHERE chat_id=? GROUP BY tipo", (m["id"],))
        reacciones = {r["tipo"]: r["total"] for r in c.fetchall()}
        c.execute("SELECT tipo FROM chat_reacciones WHERE chat_id=? AND usuario_id=?", (m["id"], u["id"]))
        mir = c.fetchone()
        respondiendo_nombre = None
        respondiendo_texto = None
        if m["respondiendo_a"]:
            c.execute("SELECT usuario_nombre, mensaje FROM chat WHERE id=?", (m["respondiendo_a"],))
            ref = c.fetchone()
            if ref:
                respondiendo_nombre = ref["usuario_nombre"]
                respondiendo_texto = ref["mensaje"]
        mensajes.append({"msg": m, "reacciones": reacciones, "mi_reaccion": mir["tipo"] if mir else None, "respondiendo_a": m["respondiendo_a"], "respondiendo_nombre": respondiendo_nombre, "respondiendo_texto": respondiendo_texto})
    conn.close()
    return render_template('chat.html', usuario=u, mensajes=mensajes)

@app.route('/chat/enviar', methods=['POST'])
def chat_enviar():
    u = get_user()
    if not u["is_authenticated"]: return redirect(url_for('login'))
    msg = request.form.get('mensaje','').strip()
    respondiendo_a = request.form.get('respondiendo_a','').strip()
    respondiendo_a = int(respondiendo_a) if respondiendo_a.isdigit() else None
    imagen_nombre = None
    archivo_nombre = None
    if 'archivo' in request.files:
        f = request.files['archivo']
        if f and f.filename and extension_valida(f.filename):
            ext = f.filename.rsplit('.',1)[1].lower()
            nombre_seguro = secure_filename(uuid.uuid4().hex[:10] + "_" + f.filename)
            ruta = os.path.join(UPLOAD_FOLDER, nombre_seguro)
            f.save(ruta)
            if ext in ['png','jpg','jpeg','gif','webp']:
                imagen_nombre = nombre_seguro
            else:
                archivo_nombre = nombre_seguro
    if msg or imagen_nombre or archivo_nombre:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("INSERT INTO chat (usuario_id,usuario_nombre,mensaje,imagen,archivo,respondiendo_a) VALUES (?,?,?,?,?,?)",
                   (u["id"],u["nombre"],msg or "",imagen_nombre,archivo_nombre,respondiendo_a))
        conn.commit(); conn.close()
    return redirect(url_for('chat'))

@app.route('/chat/reaccionar/<int:cid>/<tipo>')
def chat_reaccionar(cid, tipo):
    u = get_user()
    if not u["is_authenticated"]: return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT tipo FROM chat_reacciones WHERE chat_id=? AND usuario_id=?", (cid, u["id"]))
    existente = c.fetchone()
    if existente and existente[0] == tipo:
        c.execute("DELETE FROM chat_reacciones WHERE chat_id=? AND usuario_id=?", (cid, u["id"]))
    else:
        c.execute("INSERT OR REPLACE INTO chat_reacciones (chat_id,usuario_id,tipo) VALUES (?,?,?)", (cid, u["id"], tipo))
    conn.commit(); conn.close()
    return redirect(url_for('chat'))

@app.route('/chat/mensajes')
def chat_mensajes():
    u = get_user()
    if not u["is_authenticated"]: return Response("[]", mimetype='application/json')
    desde = request.args.get('desde',0,type=int)
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM chat WHERE id>? ORDER BY creado_en ASC LIMIT 30", (desde,))
    msgs = [{"id":m["id"],"nombre":m["usuario_nombre"],"mensaje":m["mensaje"],"hora":m["creado_en"]} for m in c.fetchall()]
    conn.close()
    return Response(json.dumps(msgs), mimetype='application/json')

@app.route('/cursos')
def cursos():
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM lecciones ORDER BY id ASC"); lecciones = c.fetchall(); conn.close()
    return render_template('cursos.html', usuario=u, lecciones=lecciones)

@app.route('/leccion/<int:lid>')
def leccion(lid):
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM lecciones WHERE id=?", (lid,)); lec = c.fetchone(); conn.close()
    if not lec: flash("No encontrada.", "error"); return redirect(url_for('cursos'))
    if lec["es_premium"] and u["plan"]!="premium": flash("Leccion Premium.", "error"); return redirect(url_for('cursos'))
    return render_template('leccion.html', usuario=u, leccion=lec)

@app.route('/pago_premium')
def pago_premium():
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    if u["plan"]=="premium": flash("Ya tienes Premium.", "success"); return redirect(url_for('cursos'))
    ref = f"genesis-{u['id']}-{uuid.uuid4().hex[:8]}"
    return render_template('pago.html', usuario=u, wompi_public_key=WOMPI_PUBLIC_KEY, amount_cents=990000, referencia=ref, redirect_url="https://achip.pythonanywhere.com/pago_exitoso")

@app.route('/pago_exitoso')
def pago_exitoso():
    u = get_user()
    if not u["is_authenticated"]: return redirect(url_for('login'))
    tid = request.args.get('id')
    if not tid: flash("Sin confirmación.", "error"); return redirect(url_for('pago_premium'))
    try:
        req = urllib.request.Request(f"https://sandbox.wompi.co/v1/transactions/{tid}", headers={"Authorization":f"Bearer {WOMPI_PRIVATE_KEY}"})
        with urllib.request.urlopen(req) as r: data = json.loads(r.read())
        if data.get("data",{}).get("status")=="APPROVED":
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("UPDATE usuario SET plan='premium' WHERE id=?", (u["id"],)); conn.commit(); conn.close()
            flash("Pago aprobado! Ya eres Premium.", "success"); return redirect(url_for('cursos'))
        flash("Pago no aprobado.", "error"); return redirect(url_for('pago_premium'))
    except: flash("Error al verificar.", "error"); return redirect(url_for('pago_premium'))

@app.route('/comunidad')
def comunidad():
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; c = conn.cursor()
    c.execute("SELECT * FROM mensajes ORDER BY creado_en DESC LIMIT 50")
    mensajes_raw = c.fetchall()
    mensajes = []
    for m in mensajes_raw:
        c.execute("SELECT tipo, COUNT(*) as total FROM reacciones WHERE mensaje_id=? GROUP BY tipo", (m["id"],))
        reacciones = {r["tipo"]: r["total"] for r in c.fetchall()}
        c.execute("SELECT * FROM comentarios WHERE mensaje_id=? ORDER BY creado_en ASC", (m["id"],))
        comentarios = c.fetchall()
        c.execute("SELECT tipo FROM reacciones WHERE mensaje_id=? AND usuario_id=?", (m["id"], u["id"]))
        mi_reaccion = c.fetchone()
        mensajes.append({"msg": m, "reacciones": reacciones, "comentarios": comentarios, "mi_reaccion": mi_reaccion["tipo"] if mi_reaccion else None})
    conn.close()
    return render_template('comunidad.html', usuario=u, mensajes=mensajes)

@app.route('/comunidad_interactuar', methods=['POST'])
def comunidad_interactuar():
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    contenido = request.form.get('contenido','').strip()
    codigo = request.form.get('codigo','').strip()
    if not contenido: flash("Vacío.", "error"); return redirect(url_for('comunidad'))
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT INTO mensajes (usuario_id,usuario_nombre,contenido,codigo) VALUES (?,?,?,?)", (u["id"],u["nombre"],contenido,codigo))
    c.execute("UPDATE usuario SET puntos=puntos+20 WHERE id=?", (u["id"],)); conn.commit(); conn.close()
    flash("Publicado! +20 XP", "success"); return redirect(url_for('comunidad'))

@app.route('/comunidad/reaccionar/<int:mid>/<tipo>')
def reaccionar(mid, tipo):
    u = get_user()
    if not u["is_authenticated"]: return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO reacciones (mensaje_id,usuario_id,tipo) VALUES (?,?,?)", (mid,u["id"],tipo))
    except: pass
    conn.commit(); conn.close()
    return redirect(url_for('comunidad'))

@app.route('/comunidad/comentar/<int:mid>', methods=['POST'])
def comentar(mid):
    u = get_user()
    if not u["is_authenticated"]: return redirect(url_for('login'))
    contenido = request.form.get('comentario','').strip()
    if contenido:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("INSERT INTO comentarios (mensaje_id,usuario_id,usuario_nombre,contenido) VALUES (?,?,?,?)", (mid,u["id"],u["nombre"],contenido))
        conn.commit(); conn.close()
    return redirect(url_for('comunidad'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; c = conn.cursor()
        c.execute("SELECT * FROM usuario WHERE LOWER(nombre)=LOWER(?) OR LOWER(email)=LOWER(?)", (username,username))
        user = c.fetchone(); conn.close()
        if user and user['password']==password:
            session['user_id']=user['id']; flash(f"Bienvenido, {user['nombre']}!", "success"); return redirect(url_for('dashboard'))
        flash("Credenciales incorrectas.", "error"); return redirect(url_for('login'))
    return render_template('login.html', usuario=get_user())

@app.route('/registro', methods=['GET','POST'])
def registro():
    if request.method=='POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        email = request.form.get('email','').strip() or f"{username}@genesis.com"
        if not username or not password: flash("Campos obligatorios.", "error"); return redirect(url_for('registro'))
        try:
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("INSERT INTO usuario (nombre,email,password,puntos,nivel) VALUES (?,?,?,0,'Iniciado')", (username,email,password))
            conn.commit(); conn.close(); flash("Registro exitoso!", "success"); return redirect(url_for('login'))
        except sqlite3.IntegrityError: flash("Usuario ya existe.", "error"); return redirect(url_for('registro'))
    return render_template('registro.html', usuario=get_user())

@app.route('/logout')
def logout():
    session.pop('user_id',None); flash("Sesión cerrada.", "success"); return redirect(url_for('index'))

# --- CORRECCIÓN DE SEGURIDAD INTEGRADA ---
USER_FILES_FOLDER = os.path.join(base_dir, "user_files")
os.makedirs(USER_FILES_FOLDER, exist_ok=True)

@app.route('/api/files/save', methods=['POST'])
def api_files_save():
    u = get_user()
    if not u["is_authenticated"]:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    if not data or 'path' not in data or 'content' not in data:
        return jsonify({"error": "Invalid request"}), 400
        
    file_path = data.get('path')
    content = data.get('content')
    
    # Sanitización de ruta más estricta
    safe_file_path = os.path.normpath(file_path)
    parts = [p for p in safe_file_path.split(os.sep) if p and p not in ('.', '..')]
    safe_file_path = os.path.join(*parts)
    full_path = os.path.join(USER_FILES_FOLDER, str(u["id"]), safe_file_path)
    
    # Asegurar directorio padre
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
    except Exception as e:
        return jsonify({"error": f"Error al crear directorio: {str(e)}"}), 500
    
    # Verificación estricta: si ya existe y es directorio, abortar
    if os.path.isdir(full_path):
        return jsonify({"error": "La ruta destino es un directorio"}), 400

    # Escritura segura
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        return jsonify({"error": f"Error al escribir archivo: {str(e)}"}), 500
        
    return jsonify({"status": "success"})

@app.route('/api/files/list', methods=['GET'])
def api_files_list():
    u = get_user()
    if not u["is_authenticated"]:
        return jsonify({"error": "Unauthorized"}), 401
    user_dir = os.path.join(USER_FILES_FOLDER, str(u["id"]))
    os.makedirs(user_dir, exist_ok=True)
    files = []
    for root, dirs, filenames in os.walk(user_dir):
        for fn in filenames:
            rel = os.path.relpath(os.path.join(root, fn), user_dir)
            files.append(rel)
    return jsonify(files)

@app.route('/api/files/read', methods=['POST'])
def api_files_read():
    u = get_user()
    if not u["is_authenticated"]:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    if not data or 'path' not in data:
        return jsonify({"error": "Invalid request"}), 400
    file_path = data.get('path')
    safe_file_path = os.path.normpath(file_path)
    parts = [p for p in safe_file_path.split(os.sep) if p and p not in ('.', '..')]
    full_path = os.path.join(USER_FILES_FOLDER, str(u["id"]), os.path.join(*parts))
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return jsonify({"content": ""})
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        content = f"Error al leer archivo: {str(e)}"
    return jsonify({"content": content})

@app.route('/api/ejecutar', methods=['POST'])
def api_ejecutar():
    u = get_user()
    if not u["is_authenticated"]:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    if not data or 'codigo' not in data:
        return jsonify({"salida": "Error: Código no proporcionado"}), 400
    codigo = data.get('codigo')
    
    import subprocess, tempfile
    try:
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as tmp:
            tmp.write(codigo)
            tmp_name = tmp.name
        
        result = subprocess.run(
            ['python3', tmp_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        salida = result.stdout + result.stderr
        if not salida:
            salida = "[Ejecutado sin salida]\n"
    except subprocess.TimeoutExpired:
        salida = "Error: Tiempo de ejecución agotado (Timeout)\n"
    except Exception as e:
        salida = f"Error al ejecutar: {str(e)}\n"
    finally:
        try:
            os.unlink(tmp_name)
        except:
            pass
            
    return jsonify({"salida": salida})

@app.route('/codebox')
def codebox():
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    return render_template('codebox.html', usuario=u)

@app.route('/ide')
def ide():
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    return render_template('ide.html', usuario=u)

@app.route('/terminal')
def terminal():
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    return render_template('terminal.html', usuario=u)

@app.route('/about')
def about():
    u = get_user()
    return render_template('about.html', usuario=u)

@app.route('/quiz')
def quiz():
    u = get_user()
    if not u["is_authenticated"]: flash("Inicia sesión.", "error"); return redirect(url_for('login'))
    return render_template('quiz.html', usuario=u)

@app.route('/api/asistente', methods=['POST'])
def api_asistente():
    data = request.json or {}
    pregunta = data.get('pregunta', '').strip()
    if not pregunta:
        return jsonify({"error": "Pregunta vacía"}), 400
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3.8-flash')
            response = model.generate_content(f"Eres el Asistente David, un experto programador y guía del ecosistema Génesis. Responde de manera concisa y útil a la siguiente pregunta: {pregunta}")
            respuesta = response.text
        else:
            respuesta = f"Hola, soy el Asistente David. Recibí tu pregunta: '{pregunta}'."
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "Quota" in err_msg or "quota" in err_msg:
            respuesta = f"Hola, soy el Asistente David. He alcanzado el límite temporal de consultas gratuitas de la API (Cuota excedida). Como programador, te recomiendo revisar el código local o intentar en unos momentos cuando se renueve la cuota. ¡Sigue programando!"
        else:
            respuesta = f"Hola, soy el Asistente David. Recibí tu consulta, pero ocurrió un detalle técnico: {err_msg}"
        
    return jsonify({"respuesta": respuesta})

@socketio.on('comando')
def handle_comando(data):
    cmd = data.get('comando', '')
    import subprocess
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        if not output:
            output = "\n"
    except Exception as e:
        output = f"Error: {str(e)}\n"
    emit('salida', {'texto': output + '$ '})

if __name__=='__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
