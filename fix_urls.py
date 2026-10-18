import os

# Mapeo de rutas antiguas a nuevas (blueprint.endpoint)
URL_MAPPING = {
    "url_for('desafio'": "url_for('education.desafio'",
    "url_for('cursos'": "url_for('education.cursos'",
    "url_for('leccion'": "url_for('education.leccion'",
    "url_for('dashboard'": "url_for('education.dashboard'",
    "url_for('login'": "url_for('auth.login'",
    "url_for('logout'": "url_for('auth.logout'",
    "url_for('chat'": "url_for('chat.chat'",
    "url_for('admin'": "url_for('admin.admin'",
}

TEMPLATE_DIR = '/root/templates'

def fix_templates():
    for filename in os.listdir(TEMPLATE_DIR):
        if filename.endswith(".html"):
            file_path = os.path.join(TEMPLATE_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in URL_MAPPING.items():
                new_content = new_content.replace(old, new)
            
            if content != new_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Actualizado: {filename}")
            else:
                print(f"⚪ Sin cambios: {filename}")

if __name__ == "__main__":
    fix_templates()
