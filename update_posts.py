import requests
import xml.etree.ElementTree as ET
from html import unescape
import re

# URL del feed RSS de Substack
SUBSTACK_FEED = 'https://gavilanbiost.substack.com/feed'
MAX_POSTS = 5  # Número máximo de posts a mostrar

print('Obteniendo posts de Substack...')
response = requests.get(SUBSTACK_FEED)

if response.status_code != 200:
    print(f'Error al obtener el feed: {response.status_code}')
    raise SystemExit(1)

# Parsear el XML del feed RSS
root = ET.fromstring(response.content)
posts = []

# Buscar todos los items (posts)
for item in root.findall('.//item')[:MAX_POSTS]:
    try:
        # Extraer título
        title_elem = item.find('title')
        title = title_elem.text if title_elem is not None else 'Sin título'
        
        # Extraer link
        link_elem = item.find('link')
        link = link_elem.text if link_elem is not None else ''
        
        # Extraer fecha de publicación
        pub_date_elem = item.find('pubDate')
        pub_date = 'Fecha no disponible'
        if pub_date_elem is not None and pub_date_elem.text:
            # Formato: Mon, 27 Jan 2026 10:00:00 GMT
            # Extraer el año y mes
            date_parts = pub_date_elem.text.split()
            if len(date_parts) >= 4:
                day = date_parts[1]
                month = date_parts[2]
                year = date_parts[3]
                pub_date = f'{day} {month} {year}'
        
        # Extraer descripción/extracto
        description_elem = item.find('description')
        description = ''
        if description_elem is not None and description_elem.text:
            # Limpiar HTML y obtener solo texto
            desc_text = unescape(description_elem.text)
            # Eliminar tags HTML
            desc_text = re.sub(r'<[^>]+>', '', desc_text)
            # Obtener las primeras 200 caracteres
            description = desc_text[:200].strip()
            if len(desc_text) > 200:
                description += '...'
        
        if link:
            # Generar HTML en formato card
            post_html = f'<div class="card">\n'
            post_html += f'    <div class="pub-meta">SUBSTACK · {pub_date}</div>\n'
            post_html += f'    <a href="{link}" class="pub-title" target="_blank">{title}</a>\n'
            if description:
                post_html += f'    <p class="text-small">{description}</p>\n'
            post_html += f'    <div class="pub-links">\n'
            post_html += f'        <a href="{link}" class="btn-outline" target="_blank"><i class="fa-solid fa-arrow-up-right-from-square"></i> Leer Post</a>\n'
            post_html += f'    </div>\n'
            post_html += f'</div>'
            
            posts.append(post_html)
            print(f'✓ Post encontrado: {title}')
    except Exception as e:
        print(f'Error procesando post: {e}')

if not posts:
    print('No se encontraron posts en el feed')
    raise SystemExit(0)

# Actualizar el archivo index.html
try:
    with open('index.html', 'r', encoding='utf-8') as file:
        content = file.read()

    # Buscar la sección de posts
    start_marker = '<div id="posts-content"'
    start_index = content.find(start_marker)
    
    if start_index == -1:
        # Si no existe, buscar la sección de posts para agregar el contenedor
        section_marker = '<section class="content-section" id="posts">'
        section_index = content.find(section_marker)
        
        if section_index != -1:
            # Buscar el cierre de la sección header
            header_close = content.find('</div>', section_index)
            section_close = content.find('</section>', section_index)
            
            if header_close != -1 and section_close != -1:
                # Insertar el contenedor de posts
                post_items = '\n'.join(posts)
                posts_container = f'\n                <div id="posts-content">\n{post_items}\n                </div>\n            '
                
                updated_content = content[:header_close + 6] + posts_container + content[section_close:]
                
                with open('index.html', 'w', encoding='utf-8') as file:
                    file.write(updated_content)
                print(f'✓ Se creó el contenedor y se escribieron {len(posts)} posts en index.html')
            else:
                print('Error: No se pudo encontrar la estructura de la sección')
        else:
            print('Error: No se encontró la sección de posts')
    else:
        # El contenedor ya existe, actualizar contenido
        start_index = content.find('>', start_index) + 1
        end_marker = '</div>'
        end_index = content.find(end_marker, start_index)
        
        if end_index != -1:
            new_content = '\n'.join(posts)
            updated_content = content[:start_index] + '\n' + new_content + '\n' + content[end_index:]
            
            with open('index.html', 'w', encoding='utf-8') as file:
                file.write(updated_content)
            print(f'✓ Se actualizaron {len(posts)} posts en index.html')
        else:
            print('Error: No se encontró la etiqueta de cierre del contenedor')

except Exception as e:
    print(f'Error al actualizar index.html: {e}')
    import traceback
    traceback.print_exc()
