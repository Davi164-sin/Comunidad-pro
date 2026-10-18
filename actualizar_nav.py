import os
glob_pattern = "templates/community_*.html"
import glob

files = glob.glob(glob_pattern)
print(f"Encontrados {len(files)} archivos de comunidad.")

target_link = '<li class="nav-item"><a class="nav-link" href="{{ url_for(\'almacenamiento_vista\') }}">Almacenamiento</a></li>'
target_link_active = '<li class="nav-item"><a class="nav-link active" href="{{ url_for(\'almacenamiento_vista\') }}">Almacenamiento</a></li>'

for filepath in files:
    if "almacenamiento" in filepath:
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "almacenamiento_vista" in content:
        print(f"Ya tiene almacenamiento: {filepath}")
        continue
    
    # Insert before Chat or before Acerca de or before Inicio
    inserted = False
    for anchor in ['href="{{ url_for(\'chat_comunidad_vista\') }}"', 'href="{{ url_for(\'about\') }}"', 'href="{{ url_for(\'recursos\') }}"']:
        if anchor in content:
            # find the opening <li... of that anchor
            idx = content.find(anchor)
            # find the start of the <li> tag containing anchor
            li_start = content.rfind("<li", 0, idx)
            if li_start != -1:
                content = content[:li_start] + '<li class="nav-item"><a class="nav-link" href="{{ url_for(\'almacenamiento_vista\') }}">Almacenamiento</a></li>\n                    ' + content[li_start:]
                inserted = True
                break
    
    if inserted:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Actualizado con éxito: {filepath}")
    else:
        print(f"No se encontró punto de anclaje en: {filepath}")
