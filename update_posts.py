import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from html import escape
from html import unescape
import re

# URL del feed RSS de Substack
SUBSTACK_FEED = 'https://gavilanbiost.substack.com/feed'
SUBSTACK_ARCHIVE_API = 'https://gavilanbiost.substack.com/api/v1/archive'
MAX_POSTS = 5  # Número máximo de posts a mostrar
REQUEST_TIMEOUT = 20
COMMON_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
}


def clean_description(text):
    if not text:
        return ''

    desc_text = unescape(text)
    desc_text = re.sub(r'<[^>]+>', '', desc_text)
    desc_text = re.sub(r'\s+', ' ', desc_text).strip()
    description = desc_text[:200].strip()
    if len(desc_text) > 200:
        description += '...'
    return description


def format_api_date(date_text):
    if not date_text:
        return 'Fecha no disponible'

    try:
        normalized = str(date_text).replace('Z', '+00:00')
        dt = datetime.fromisoformat(normalized)
        return dt.strftime('%d %b %Y')
    except ValueError:
        return str(date_text)[:10] if len(str(date_text)) >= 10 else str(date_text)


def build_post_card(title, link, pub_date, description):
    if not link:
        return ''

    safe_title = escape(title or 'Sin título')
    safe_link = escape(link, quote=True)
    safe_date = escape(pub_date or 'Fecha no disponible')
    safe_description = escape(description or '')

    post_html = f'<div class="card">\n'
    post_html += f'    <div class="pub-meta">SUBSTACK · {safe_date}</div>\n'
    post_html += f'    <a href="{safe_link}" class="pub-title" target="_blank" rel="noopener noreferrer">{safe_title}</a>\n'
    if description:
        post_html += f'    <p class="text-small">{safe_description}</p>\n'
    post_html += f'    <div class="pub-links">\n'
    post_html += (
        f'        <a href="{safe_link}" class="btn-outline" target="_blank" '
        'rel="noopener noreferrer"><i class="fa-solid fa-arrow-up-right-from-square"></i> '
        'Leer Post</a>\n'
    )
    post_html += f'    </div>\n'
    post_html += f'</div>'
    return post_html


def fetch_substack_posts_from_api():
    print('Intentando fallback con API pública de Substack...')

    try:
        response = requests.get(
            SUBSTACK_ARCHIVE_API,
            params={'sort': 'new'},
            timeout=REQUEST_TIMEOUT,
            headers={
                **COMMON_HEADERS,
                'Accept': 'application/json, text/plain, */*',
            },
        )
    except requests.RequestException as exc:
        print(f'Error de red en fallback API: {exc}')
        return []

    if response.status_code != 200:
        print(f'Fallback API devolvió estado {response.status_code}')
        return []

    try:
        payload = response.json()
    except ValueError as exc:
        print(f'Fallback API devolvió JSON inválido: {exc}')
        return []

    items = payload if isinstance(payload, list) else payload.get('posts', [])
    posts = []

    for item in items[:MAX_POSTS]:
        title = item.get('title') or 'Sin título'
        link = item.get('canonical_url') or item.get('post_url') or ''
        if not link and item.get('slug'):
            link = f'https://gavilanbiost.substack.com/p/{item.get("slug")}'

        pub_date = format_api_date(item.get('post_date') or item.get('published_at') or item.get('created_at'))
        description = clean_description(item.get('subtitle') or item.get('description') or item.get('body_html') or '')

        post_html = build_post_card(title, link, pub_date, description)
        if post_html:
            posts.append(post_html)
            print(f'✓ Post encontrado (API): {title}')

    return posts


def fetch_substack_posts():
    print('Obteniendo posts de Substack...')

    try:
        response = requests.get(
            SUBSTACK_FEED,
            timeout=REQUEST_TIMEOUT,
            headers={
                **COMMON_HEADERS,
                'Accept': 'application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5',
            },
        )
    except requests.RequestException as exc:
        print(f'Error de red al obtener el feed: {exc}')
        return fetch_substack_posts_from_api()

    if response.status_code != 200:
        print(f'Error al obtener el feed: {response.status_code}')
        return fetch_substack_posts_from_api()

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        print(f'Error parseando XML del feed: {exc}')
        return fetch_substack_posts_from_api()

    posts = []

    # Buscar todos los items (posts)
    for item in root.findall('.//item')[:MAX_POSTS]:
        try:
            # Extraer título
            title_elem = item.find('title')
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else 'Sin título'

            # Extraer link
            link_elem = item.find('link')
            link = link_elem.text.strip() if link_elem is not None and link_elem.text else ''

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
            description = clean_description(description_elem.text if description_elem is not None else '')

            post_html = build_post_card(title, link, pub_date, description)
            if post_html:
                posts.append(post_html)
                print(f'✓ Post encontrado: {title}')
        except Exception as exc:
            print(f'Error procesando post: {exc}')

    if posts:
        return posts

    print('Feed RSS no devolvió items utilizables. Intentando fallback API...')
    return fetch_substack_posts_from_api()


def update_index_html(posts):
    with open('index.html', 'r', encoding='utf-8') as file:
        content = file.read()

    pattern = (
        r'(<div id="posts-content">)'
        r'(.*?)'
        r'(</div>\s*<div style="text-align: center; margin-top: 20px;">\s*<button id="ver-mas-posts")'
    )

    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise RuntimeError('No se encontró la sección de posts en index.html con el formato esperado')

    new_content = '\n' + '\n'.join(posts) + '\n'
    updated_content = content[:match.start(2)] + new_content + content[match.end(2):]

    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(updated_content)

if __name__ == '__main__':
    posts = fetch_substack_posts()

    if not posts:
        print('No se encontraron posts en el feed. Se detiene para evitar un éxito silencioso sin actualizar index.html.')
        raise SystemExit(1)

    # Actualizar el archivo index.html
    try:
        update_index_html(posts)
        print(f'✓ Se actualizaron {len(posts)} posts en index.html')
    except Exception as exc:
        print(f'Error al actualizar index.html: {exc}')
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
