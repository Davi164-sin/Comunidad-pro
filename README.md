# 🚀 ComunidadPro

Plataforma web moderna desarrollada en **Flask (Python)** para la gestión integral de comunidades, grupos de WhatsApp, directorio de creadores de contenido, chat en tiempo real con soporte multimedia, encuestas en vivo, sistema de aportes/ranking y panel de moderación.

---

## ✨ Características Principales

1. **Gestión de Comunidad y WhatsApp:**
   - Enlaces protegidos a grupos y canales oficiales de WhatsApp.
   - Anuncios oficiales de la administración.
2. **Directorio de Creadores y Talentos:**
   - Perfiles verificados organizados por categorías (Arte, Tecnología, Educación, Streaming, Diseño, Contenido Exclusivo).
   - Buscador avanzado y filtros por categoría.
   - Sistema de valoraciones con estrellas (reseñas) y perfiles detallados.
   - Sistema de apoyo / donaciones simuladas a creadores.
3. **Chat Multimedia en Tiempo Real:**
   - Chat comunitario interactivo impulsado por **Flask-SocketIO**.
   - Soporte para adjuntar y reproducir imágenes, videos (`.mp4`, `.webm`, etc.), audios/música (`.mp3`, `.wav`) y documentos.
   - Botón de borrado de mensajes (propios y de moderadores/administradores).
4. **Sistema de Reputación y Ranking:**
   - Puntos de aporte asignados por la administración a los miembros más activos.
   - Tabla de clasificación (ranking) pública con podio para los mejores aportantes.
5. **Encuestas y Votaciones:**
   - Módulo para crear encuestas en vivo y votar con gráficos de porcentaje en tiempo real.
6. **Moderación y Roles:**
   - Roles de **Administrador**, **Moderador**, **Creador** y **Miembro**.
   - Sistema de reportes de contenido.
   - Exportación de datos a **CSV** desde el panel de administración.
7. **Modo Oscuro / Claro:**
   - Interruptor de tema visual persistente en la barra de navegación.

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python 3, Flask, Flask-SocketIO, SQLite.
- **Frontend:** HTML5, Bootstrap 5, FontAwesome, JavaScript (WebSockets).
- **Despliegue:** Gunicorn, Gevent/Eventlet, Render.

---

## ⚙️ Instalación y Ejecución Local

1. Clona el repositorio:
   ```bash
   git clone https://github.com/Davi164-sin/Comunidad-pro.git
   cd Comunidad-pro
   ```
2. Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Ejecuta la aplicación:
   ```bash
   python gestor_comunidad.py
   ```
5. Abre en tu navegador: `http://localhost:5000`

---

## 🔑 Credenciales de Administrador por Defecto
- **Correo:** `admin@comunidad.com`
- **Contraseña:** `admin123`
