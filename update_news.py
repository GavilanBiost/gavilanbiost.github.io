import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests

MAX_NEWS = 100  # Obtener hasta 100 noticias para el archivo
MAX_INDEX_NEWS = 3  # Mostrar solo últimas 3 en index
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=es-419&gl=ES&ceid=ES:es-419"
QUERY_TERMS = [
    '"Jesus F Garcia Gavilan"',
    '"Jesus F Garcia-Gavilan"',
    '"Jesus Garcia Gavilan"',
    '"Jesus Garcia-Gavilan"',
    '"Jesus Francisco Garcia Gavilan"',
    '"Jesus Francisco Garcia-Gavilan"',
    '"J F Garcia Gavilan"',
    '"J. F. Garcia Gavilan"',
    '"J F Garcia-Gavilan"',
    '"J. F. Garcia-Gavilan"',
]


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def contains_name_variant(text: str) -> bool:
    normalized = normalize_text(text)
    token_set = set(normalized.split())

    # Normalization already removes accents and punctuation, so equivalent variants
    # like Garcia-Gavilan / García-Gavilán collapse to the same token pattern.
    has_gavilan = "gavilan" in token_set
    has_garcia = "garcia" in token_set
    has_jesus = "jesus" in token_set
    has_initials = bool(re.search(r"\bj\s+f\b", normalized))

    # Strict match: require both surnames and Jesus (or initials J F).
    if has_gavilan and has_garcia and (has_jesus or has_initials):
        return True

    patterns = [
        r"\bjesus\s+f(?:rancisco)?\s+garcia\s+gavilan\b",
        r"\bjesus\s+garcia\s+gavilan\b",
        r"\bj\s*f\s+garcia\s+gavilan\b",
        r"\bgarcia\s+gavilan\b",
        r"\bjesus\s+f\s+garcia\b",
    ]

    return any(re.search(pattern, normalized) for pattern in patterns)


def format_pub_date(raw_date: str) -> tuple[datetime, str]:
    if not raw_date:
        return datetime.min, "Fecha no disponible"

    try:
        dt = parsedate_to_datetime(raw_date)
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt, dt.strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return datetime.min, "Fecha no disponible"


def get_item_text(item: ET.Element, tag_name: str) -> str:
    elem = item.find(tag_name)
    if elem is None or elem.text is None:
        return ""
    return elem.text.strip()


def fetch_news() -> list[dict]:
    all_news = {}

    for query_term in QUERY_TERMS:
        feed_url = GOOGLE_NEWS_RSS.format(query=quote_plus(query_term))
        print(f"Consultando: {query_term}")

        response = requests.get(feed_url, timeout=20)
        if response.status_code != 200:
            print(f"  Error en feed ({response.status_code})")
            continue

        root = ET.fromstring(response.content)
        items = root.findall(".//item")

        for item in items:
            title = get_item_text(item, "title")
            link = get_item_text(item, "link")
            description = get_item_text(item, "description")
            source = get_item_text(item, "source") or "Google News"
            pub_date_raw = get_item_text(item, "pubDate")

            combined_text = f"{title} {description}"
            if not contains_name_variant(combined_text):
                continue

            pub_dt, pub_date = format_pub_date(pub_date_raw)

            key = link or normalize_text(title)
            existing = all_news.get(key)
            candidate = {
                "title": title,
                "link": link,
                "source": source,
                "pub_date": pub_date,
                "pub_dt": pub_dt,
            }

            if existing is None or candidate["pub_dt"] > existing["pub_dt"]:
                all_news[key] = candidate

    deduped = list(all_news.values())
    deduped.sort(key=lambda x: x["pub_dt"], reverse=True)
    return deduped[:MAX_NEWS]


def build_news_cards(news_items: list[dict], limit: int = None) -> str:
    """Genera tarjetas HTML de noticias."""
    cards = []
    items_to_show = news_items[:limit] if limit else news_items

    for item in items_to_show:
        title = html.escape(item["title"] or "Sin titulo")
        link = html.escape(item["link"] or "#", quote=True)
        source = html.escape(item["source"] or "Google News")
        pub_date = html.escape(item["pub_date"] or "Fecha no disponible")

        card_html = (
            '<div class="card">\n'
            f'    <div class="pub-meta">{source} · {pub_date}</div>\n'
            f'    <a href="{link}" class="pub-title" target="_blank" rel="noopener noreferrer">{title}</a>\n'
            "</div>"
        )
        cards.append(card_html)

    if not cards:
        cards.append(
            '<div class="card">\n'
            '    <div class="pub-meta">SIN RESULTADOS · Fecha no disponible</div>\n'
            '    <p class="text-small">No se encontraron noticias recientes con menciones a Jesus F Garcia Gavilan.</p>\n'
            "</div>"
        )

    return "\n".join(cards)


def update_index_html(news_html: str) -> None:
    """Actualiza la sección de noticias en index.html con solo las últimas 3 noticias."""
    with open("index.html", "r", encoding="utf-8") as file:
        content = file.read()

    pattern = (
        r'(<div id="noticias-content">)'
        r'(.*?)'
        r'(</div>\s*<div style="text-align: center; margin-top: 20px;">\s*(?:<button id="ver-mas-noticias"|<a href="news\.html"))'
    )

    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise RuntimeError("No se encontro la seccion de noticias en index.html")

    replacement = "\n" + news_html + "\n"
    updated = content[: match.start(2)] + replacement + content[match.end(2) :]

    with open("index.html", "w", encoding="utf-8") as file:
        file.write(updated)


def create_news_page(all_news: list[dict]) -> None:
    """Crea la página news.html con todas las noticias agrupadas por año."""
    generated_at = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    if not all_news:
        html_content = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Noticias - Jesús F García Gavilán</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body class="news-page">
    <div class="main-container" style="display:block;width:100%;max-width:1200px;">
        <main role="main" style="width:100%;max-width:none;">
            <section class="content-section" style="width:100%;max-width:none;">
                <div class="section-header">
                    <h2>Noticias</h2>
                </div>
                <p class="text-small" style="margin-bottom: 16px;">Última actualización: ''' + generated_at + '''</p>
                <div class="card">
                    <p class="text-small">No se encontraron noticias aún.</p>
                </div>
                <div style="margin-top: 20px;">
                    <a href="index.html" class="btn-outline">← Volver al inicio</a>
                </div>
            </section>
        </main>
    </div>
</body>
</html>'''
        with open("news.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        return

    # Agrupar noticias por año
    news_by_year = {}
    for item in all_news:
        year = item["pub_dt"].year
        if year not in news_by_year:
            news_by_year[year] = []
        news_by_year[year].append(item)

    # Ordenar años en orden descendente
    sorted_years = sorted(news_by_year.keys(), reverse=True)

    # Construir contenido HTML
    news_sections = []
    for year in sorted_years:
        year_html = f'<div class="section-header"><h3>{year}</h3></div>\n'
        for item in news_by_year[year]:
            title = html.escape(item["title"] or "Sin titulo")
            link = html.escape(item["link"] or "#", quote=True)
            source = html.escape(item["source"] or "Google News")
            pub_date = html.escape(item["pub_date"] or "Fecha no disponible")

            year_html += (
                '<div class="card">\n'
                f'    <div class="pub-meta">{source} · {pub_date}</div>\n'
                f'    <a href="{link}" class="pub-title" target="_blank" rel="noopener noreferrer">{title}</a>\n'
                "</div>\n"
            )
        news_sections.append(year_html)

    html_content = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Noticias - Jesús F García Gavilán</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="styles.css">
</head>
<body class="news-page">
    <nav class="navbar" role="navigation" aria-label="Navegación principal">
        <div class="nav-container">
            <a href="index.html" class="brand">JFGG <span class="highlight"></span></a>
            <div class="nav-links">
                <a href="index.html#inicio">Inicio</a>
                <a href="index.html#posts">Posts</a>
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
            <section class="content-section" id="noticias-archive" style="width:100%;max-width:none;">
                <div class="section-header">
                    <h2><span class="mono-text"></span> Noticias</h2>
                </div>
                <p class="text-small" style="margin-bottom: 16px;">Última actualización: {generated_at}</p>
                
                {"".join(news_sections)}
                
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

    with open("news.html", "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    print("Buscando noticias...")
    all_news = fetch_news()
    print(f"Noticias relevantes encontradas: {len(all_news)}")
    
    # Actualizar index con solo las últimas 3 noticias
    html_cards_index = build_news_cards(all_news, limit=MAX_INDEX_NEWS)
    update_index_html(html_cards_index)
    print(f"✓ index.html actualizado con {min(len(all_news), MAX_INDEX_NEWS)} noticias")
    
    # Crear página de archivo con todas las noticias por año
    create_news_page(all_news)
    print(f"✓ news.html creado con {len(all_news)} noticias agrupadas por año")
