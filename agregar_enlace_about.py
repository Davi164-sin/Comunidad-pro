import os, glob

files = glob.glob('templates/community_*.html')
for fpath in files:
    if 'about.html' in fpath:
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "url_for('about')" not in content:
        target = '<li class="nav-item"><a class="nav-link" href="{{ url_for(\'chat_comunidad_vista\') }}">Chat</a></li>'
        replacement = '<li class="nav-item"><a class="nav-link" href="{{ url_for(\'about\') }}">Acerca de</a></li>\n                    <li class="nav-item"><a class="nav-link" href="{{ url_for(\'chat_comunidad_vista\') }}">Chat</a></li>'
        if target in content:
            content = content.replace(target, replacement)
        else:
            target2 = '</ul>'
            replacement2 = '<li class="nav-item"><a class="nav-link" href="{{ url_for(\'about\') }}">Acerca de</a></li>\n                </ul>'
            content = content.replace(target2, replacement2, 1)
            
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Actualizado: {fpath}")

print("¡Todas las plantillas actualizadas!")
