# Automatización de Posts de Substack

Este proyecto incluye automatización para actualizar automáticamente la sección "Últimos Posts" con contenido de tu Substack.

## 📁 Archivos Creados

### 1. `update_posts.py`
Script que lee el feed RSS de Substack y actualiza `index.html` con las últimas publicaciones.

**Contenido del script:**
```python
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
            desc_text = re.sub(r'<[^>]+>', '', desc_text)
            description = desc_text[:200].strip()
            if len(desc_text) > 200:
                description += '...'
        
        if link:
            # Generar HTML en formato card
            post_html = '<div class="card">\n'
            post_html += f'    <div class="pub-meta">SUBSTACK · {pub_date}</div>\n'
            post_html += f'    <a href="{link}" class="pub-title" target="_blank">{title}</a>\n'
            if description:
                post_html += f'    <p class="text-small">{description}</p>\n'
            post_html += '    <div class="pub-links">\n'
            post_html += f'        <a href="{link}" class="btn-outline" target="_blank"><i class="fa-solid fa-arrow-up-right-from-square"></i> Leer Post</a>\n'
            post_html += '    </div>\n'
            post_html += '</div>'
            
            posts.append(post_html)
            print(f'✓ Post encontrado: {title}')
    except Exception as e:
        print(f'Error procesando post: {e}')

if not posts:
    print('No se encontraron posts en el feed')
    raise SystemExit(0)

# Actualizar el archivo index.html
with open('index.html', 'r', encoding='utf-8') as file:
    content = file.read()

start_marker = '<div id="posts-content"'
start_index = content.find(start_marker)

if start_index != -1:
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
else:
    print('Error: No se encontró el contenedor de posts')
```

### 2. `.github/workflows/update_posts.yml`
GitHub Action que ejecuta el script automáticamente cada 6 horas.

## 🚀 Uso Manual

Para actualizar los posts manualmente:

```bash
python3 update_posts.py
```

## ⚙️ Automatización con GitHub Actions

El workflow se ejecuta automáticamente:
- **Cada 6 horas** para detectar nuevos posts
- **Manualmente** desde la pestaña "Actions" en GitHub

### Para ejecutar manualmente:
1. Ve a tu repositorio en GitHub
2. Click en la pestaña "Actions"
3. Selecciona "Update Substack Posts"
4. Click en "Run workflow"

## 📝 Configuración

Si quieres cambiar la frecuencia de actualización, edita el archivo `.github/workflows/update_posts.yml`:

```yaml
schedule:
  - cron: "0 */6 * * *"  # Cambiar esto
```

Ejemplos de cron:
- `"0 */6 * * *"` - Cada 6 horas
- `"0 */12 * * *"` - Cada 12 horas
- `"0 9 * * *"` - Todos los días a las 9 AM
- `"0 9 * * 1"` - Todos los lunes a las 9 AM

## 📦 Dependencias

El script requiere Python 3 y el paquete `requests`:

```bash
pip install requests
```

GitHub Actions instala automáticamente las dependencias.
