import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import escape
from html import unescape
import re

# URL del feed RSS de Substack
SUBSTACK_FEED = 'https://gavilanbiost.substack.com/feed'
SUBSTACK_ARCHIVE_API = 'https://gavilanbiost.substack.com/api/v1/archive'
JINA_MIRROR_FEED = 'https://r.jina.ai/http://gavilanbiost.substack.com/feed'
JINA_MIRROR_ARCHIVE = 'https://r.jina.ai/http://gavilanbiost.substack.com/archive'
MAX_INDEX_POSTS = 3
MAX_ARCHIVE_POSTS = 200
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

def parse_date_value(date_text):
    if date_text is None or date_text == '':
        return datetime.min, 'Fecha no disponible'

    if isinstance(date_text, (int, float)):
        try:
            ts = float(date_text)
            if ts > 10_000_000_000:
                ts = ts / 1000.0
            dt = datetime.utcfromtimestamp(ts)
            return dt, dt.strftime('%d/%m/%Y')
        except (ValueError, OSError):
            return datetime.min, 'Fecha no disponible'

    text = str(date_text).strip()
    if not text:
        return datetime.min, 'Fecha no disponible'

    try:
        normalized = text.replace('Z', '+00:00')
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt, dt.strftime('%d/%m/%Y')
    except ValueError:
        return datetime.min, text[:10] if len(text) >= 10 else text


def parse_rss_pub_date(raw_date):
    if not raw_date:
        return datetime.min, 'Fecha no disponible'

    try:
        dt = parsedate_to_datetime(raw_date)
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt, dt.strftime('%d/%m/%Y')
    except (TypeError, ValueError):
        return datetime.min, 'Fecha no disponible'


def format_post_entry(title, link, pub_dt, pub_date, description):
    return {
        'title': title or 'Sin título',
        'link': link or '',
        'pub_dt': pub_dt if pub_dt else datetime.min,
        'pub_date': pub_date or 'Fecha no disponible',
        'description': description or '',
    }


def build_post_card(post):
    link = post.get('link', '')
    if not link:
        return ''

    safe_title = escape(post.get('title') or 'Sin título')
    safe_link = escape(link, quote=True)
    safe_date = escape(post.get('pub_date') or 'Fecha no disponible')
    safe_description = escape(post.get('description') or '')

    post_html = '<div class="card">\n'
    post_html += f'    <div class="pub-meta">SUBSTACK · {safe_date}</div>\n'
    post_html += f'    <a href="{safe_link}" class="pub-title" target="_blank" rel="noopener noreferrer">{safe_title}</a>\n'
    if safe_description:
        post_html += f'    <p class="text-small">{safe_description}</p>\n'
    post_html += '    <div class="pub-links">\n'
    post_html += (
        f'        <a href="{safe_link}" class="btn-outline" target="_blank" '
        'rel="noopener noreferrer"><i class="fa-solid fa-arrow-up-right-from-square"></i> '
        'Leer Post</a>\n'
    )
    post_html += '    </div>\n'
    post_html += '</div>'
    return post_html


def dedupe_and_sort_posts(posts):
    unique = {}
    for post in posts:
        link = post.get('link', '').strip()
        if not link:
            continue

        existing = unique.get(link)
        if existing is None:
            unique[link] = post
            continue

        # Mantener el que tenga mejor fecha o mejor descripción.
        if post.get('pub_dt', datetime.min) > existing.get('pub_dt', datetime.min):
            unique[link] = post
        elif len(post.get('description', '')) > len(existing.get('description', '')):
            unique[link] = post

    deduped = list(unique.values())
    deduped.sort(key=lambda x: x.get('pub_dt', datetime.min), reverse=True)
    return deduped


def build_cards_html(posts):
    cards = []
    for post in posts:
        card = build_post_card(post)
        if card:
            cards.append(card)
    return '\n'.join(cards)


def fetch_substack_posts_from_jina_mirror(limit):
    print('Intentando fallback final via espejo de lectura (r.jina.ai)...')

    candidates = []
    for mirror_url in (JINA_MIRROR_FEED, JINA_MIRROR_ARCHIVE):
        try:
            response = requests.get(
                mirror_url,
                timeout=REQUEST_TIMEOUT + 10,
                headers={
                    **COMMON_HEADERS,
                    'Accept': 'text/plain, text/markdown, */*',
                },
            )
        except requests.RequestException as exc:
            print(f'Error de red con {mirror_url}: {exc}')
            continue

        if response.status_code != 200:
            print(f'Espejo devolvio estado {response.status_code} para {mirror_url}')
            continue

        candidates.append(response.text)

    if not candidates:
        print('No fue posible recuperar contenido desde el espejo')
        return []

    link_pattern = re.compile(r'\[([^\]]+)\]\((https?://gavilanbiost\.substack\.com/p/[^)\s]+)\)')
    posts = []

    for text in candidates:
        for title, link in link_pattern.findall(text):
            title_clean = re.sub(r'\s+', ' ', title).strip()
            if not title_clean or title_clean.lower().startswith('http'):
                continue

            posts.append(
                format_post_entry(
                    title=title_clean,
                    link=link.strip(),
                    pub_dt=datetime.min,
                    pub_date='Fecha no disponible',
                    description='',
                )
            )

    posts = dedupe_and_sort_posts(posts)
    for post in posts[:limit]:
        print(f"✓ Post encontrado (espejo): {post['title']}")
    return posts[:limit]


def fetch_substack_posts_from_api(limit):
    print('Intentando fallback con API publica de Substack...')

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
        return fetch_substack_posts_from_jina_mirror(limit)

    if response.status_code != 200:
        print(f'Fallback API devolvio estado {response.status_code}')
        return fetch_substack_posts_from_jina_mirror(limit)

    try:
        payload = response.json()
    except ValueError as exc:
        print(f'Fallback API devolvio JSON invalido: {exc}')
        return fetch_substack_posts_from_jina_mirror(limit)

    items = payload if isinstance(payload, list) else payload.get('posts', [])
    posts = []

    for item in items[:limit]:
        title = item.get('title') or 'Sin título'
        link = item.get('canonical_url') or item.get('post_url') or ''
        if not link and item.get('slug'):
            link = f'https://gavilanbiost.substack.com/p/{item.get("slug")}'

        pub_dt, pub_date = parse_date_value(item.get('post_date') or item.get('published_at') or item.get('created_at'))
        description = clean_description(item.get('subtitle') or item.get('description') or item.get('body_html') or '')

        posts.append(
            format_post_entry(
                title=title,
                link=link,
                pub_dt=pub_dt,
                pub_date=pub_date,
                description=description,
            )
        )

    posts = dedupe_and_sort_posts(posts)
    for post in posts[:limit]:
        print(f"✓ Post encontrado (API): {post['title']}")

    if posts:
        return posts[:limit]
    return fetch_substack_posts_from_jina_mirror(limit)


def fetch_substack_posts(limit=MAX_ARCHIVE_POSTS):
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
        return fetch_substack_posts_from_api(limit)

    if response.status_code != 200:
        print(f'Error al obtener el feed: {response.status_code}')
        return fetch_substack_posts_from_api(limit)

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        print(f'Error parseando XML del feed: {exc}')
        return fetch_substack_posts_from_api(limit)

    posts = []
    for item in root.findall('.//item')[:limit]:
        try:
            title_elem = item.find('title')
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else 'Sin título'

            link_elem = item.find('link')
            link = link_elem.text.strip() if link_elem is not None and link_elem.text else ''

            pub_date_elem = item.find('pubDate')
            pub_dt, pub_date = parse_rss_pub_date(pub_date_elem.text if pub_date_elem is not None else '')

            description_elem = item.find('description')
            description = clean_description(description_elem.text if description_elem is not None else '')

            posts.append(
                format_post_entry(
                    title=title,
                    link=link,
                    pub_dt=pub_dt,
                    pub_date=pub_date,
                    description=description,
                )
            )
        except Exception as exc:
            print(f'Error procesando post: {exc}')

    posts = dedupe_and_sort_posts(posts)
    for post in posts[:limit]:
        print(f"✓ Post encontrado: {post['title']}")

    if posts:
        return posts[:limit]

    print('Feed RSS no devolvio items utilizables. Intentando fallback API...')
    return fetch_substack_posts_from_api(limit)


def update_index_html(posts, generated_at):
    with open('index.html', 'r', encoding='utf-8') as file:
        content = file.read()

    pattern_posts = (
        r'(<div id="posts-content">)'
        r'(.*?)'
        r'(</div>\s*<div style="text-align: center; margin-top: 20px;">\s*(?:<button id="ver-mas-posts"|<a href="posts\.html"))'
    )

    match_posts = re.search(pattern_posts, content, re.DOTALL)
    if not match_posts:
        raise RuntimeError('No se encontro la seccion de posts en index.html con el formato esperado')

    new_cards = '\n' + build_cards_html(posts[:MAX_INDEX_POSTS]) + '\n'
    updated_content = content[:match_posts.start(2)] + new_cards + content[match_posts.end(2):]

    date_text = f'Ultima actualizacion: {generated_at}'
    pattern_date = r'(<p class="text-small" id="posts-last-updated"[^>]*>)(.*?)(</p>)'
    if re.search(pattern_date, updated_content, re.DOTALL):
        updated_content = re.sub(pattern_date, rf'\1{date_text}\3', updated_content, count=1, flags=re.DOTALL)
    else:
        insert_after_header = (
            r'(<section class="content-section" id="posts">\s*<div class="section-header">\s*'
            r'<h2><span class="mono-text"></span> Ultimos Posts</h2>\s*</div>)'
        )
        updated_content = re.sub(
            insert_after_header,
            r'\1\n                <p class="text-small" id="posts-last-updated" style="margin-bottom: 16px;">'
            + date_text
            + '</p>',
            updated_content,
            count=1,
            flags=re.DOTALL,
        )

    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(updated_content)


def create_posts_page(all_posts, generated_at):
    if not all_posts:
        html_content = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Posts - Jesus F Garcia Gavilan</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body class="news-page">
    <div class="main-container" style="display:block;width:100%;max-width:1200px;">
        <main role="main" style="width:100%;max-width:none;">
            <section class="content-section" style="width:100%;max-width:none;">
                <div class="section-header">
                    <h2>Posts</h2>
                </div>
                <p class="text-small" style="margin-bottom: 16px;">Ultima actualizacion: ''' + generated_at + '''</p>
                <div class="card">
                    <p class="text-small">No se encontraron posts aun.</p>
                </div>
                <div style="margin-top: 20px;">
                    <a href="index.html" class="btn-outline">← Volver al inicio</a>
                </div>
            </section>
        </main>
    </div>
</body>
</html>'''
        with open('posts.html', 'w', encoding='utf-8') as file:
            file.write(html_content)
        return

    posts_by_year = {}
    for post in all_posts:
        year = post['pub_dt'].year if post.get('pub_dt', datetime.min) != datetime.min else 0
        posts_by_year.setdefault(year, []).append(post)

    sorted_years = sorted(posts_by_year.keys(), reverse=True)
    sections = []

    for year in sorted_years:
        year_label = str(year) if year != 0 else 'Sin fecha'
        year_html = f'<div class="section-header"><h3>{year_label}</h3></div>\n'
        year_html += build_cards_html(posts_by_year[year]) + '\n'
        sections.append(year_html)

    html_content = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Posts - Jesus F Garcia Gavilan</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="styles.css">
</head>
<body class="news-page">
    <nav class="navbar" role="navigation" aria-label="Navegacion principal">
        <div class="nav-container">
            <a href="index.html" class="brand">JFGG <span class="highlight"></span></a>
            <div class="nav-links">
                <a href="index.html#inicio">Inicio</a>
                <a href="posts.html">Posts</a>
                <a href="index.html#publicaciones">Papers</a>
                <a href="index.html#proyectos">Proyectos</a>
                <a href="news.html">Noticias</a>
                <a href="index.html#newsletter">Newsletter</a>
                <a href="index.html#contact">Contacto</a>
            </div>
        </div>
    </nav>

    <div class="main-container" style="display:block;width:100%;max-width:1200px;">
        <main role="main" aria-label="Contenido principal" style="width:100%;max-width:none;">
            <section class="content-section" id="posts-archive" style="width:100%;max-width:none;">
                <div class="section-header">
                    <h2><span class="mono-text"></span> Posts</h2>
                </div>
                <p class="text-small" style="margin-bottom: 16px;">Ultima actualizacion: {generated_at}</p>

                {''.join(sections)}

                <div style="text-align: center; margin-top: 30px;">
                    <a href="index.html" class="btn-outline">
                        <i class="fa-solid fa-arrow-left"></i> Volver al inicio
                    </a>
                </div>
            </section>
        </main>
    </div>
</body>
</html>'''

    with open('posts.html', 'w', encoding='utf-8') as file:
        file.write(html_content)


if __name__ == '__main__':
    all_posts = fetch_substack_posts(limit=MAX_ARCHIVE_POSTS)

    if not all_posts:
        print('No se encontraron posts desde ninguna fuente. Se detiene para evitar un exito silencioso.')
        raise SystemExit(1)

    generated_at = datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')

    try:
        update_index_html(all_posts, generated_at)
        create_posts_page(all_posts, generated_at)
        print(f'✓ Se actualizaron {min(len(all_posts), MAX_INDEX_POSTS)} posts en index.html')
        print(f'✓ Se creo posts.html con {len(all_posts)} posts')
    except Exception as exc:
        print(f'Error al actualizar archivos de posts: {exc}')
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
