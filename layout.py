"""Plantillas compartidas del sitio.

Todas las páginas estáticas (archivos, posts y tutoriales) se generan desde aquí
para que compartan el mismo diseño que la portada. Los enlaces a recursos son
absolutos desde la raíz del dominio, así que el mismo HTML sirve tanto para
páginas en la raíz como para las que viven en post/ o tutoriales/.
"""

import html
import re

# PubMed devuelve el nombre con muchas grafías (con o sin acentos, inicial o
# nombre completo), así que el resaltado las contempla todas.
AUTHOR_NAME_PATTERN = re.compile(
    r"(?:Jes[u\u00fa]s(?:\s+Francisco)?|J\.?)\s+"
    r"(?:F(?:rancisco)?\.?\s+)?"
    r"Garc[i\u00ed]a-Gavil[a\u00e1]n"
)

SITE_URL = "https://gavilanbiost.com"
SITE_NAME = "Jesús F. García Gavilán"
DEFAULT_IMAGE = f"{SITE_URL}/img/jesus.jpg"

NAV_ITEMS = [
    ("/", "Inicio"),
    ("/posts.html", "Posts"),
    ("/tutoriales.html", "Tutoriales"),
    ("/publicaciones.html", "Publicaciones"),
    ("/#proyectos", "Proyectos"),
    ("/news.html", "Noticias"),
    ("/#contact", "Contacto"),
]

ICON_ARROW_UP_RIGHT = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M7 7h10v10"/><path d="M7 17 17 7"/></svg>'
)

ICON_ARROW_LEFT = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>'
)

ICON_MENU = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="12" y2="12"/>'
    '<line x1="4" x2="20" y1="18" y2="18"/></svg>'
)


def esc(value, quote=False):
    return html.escape(value or "", quote=quote)


def highlight_author(text):
    """Pone en negrita el nombre del autor dentro de un texto YA escapado."""
    return AUTHOR_NAME_PATTERN.sub(
        lambda match: f'<strong class="author-name">{match.group(0)}</strong>', text
    )


def head(title, description, canonical, extra_head=""):
    """Cabecera HTML común a todas las páginas estáticas."""
    title_safe = esc(title, quote=True)
    description_safe = esc(description, quote=True)
    canonical_safe = esc(canonical, quote=True)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{title_safe}</title>

    <meta name="description" content="{description_safe}">
    <meta name="author" content="Jesús F García Gavilán">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <link rel="canonical" href="{canonical_safe}">

    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_safe}">
    <meta property="og:title" content="{title_safe}">
    <meta property="og:description" content="{description_safe}">
    <meta property="og:image" content="{DEFAULT_IMAGE}">
    <meta property="og:site_name" content="{SITE_NAME}">
    <meta property="og:locale" content="es_ES">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="{canonical_safe}">
    <meta name="twitter:title" content="{title_safe}">
    <meta name="twitter:description" content="{description_safe}">
    <meta name="twitter:image" content="{DEFAULT_IMAGE}">

    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="icon" href="/jf-icon.png" sizes="any">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">

    <link rel="stylesheet" href="/assets/site.css">
    <link rel="stylesheet" href="/assets/pages.css">
{extra_head}</head>"""


def navbar(current=""):
    """Barra de navegación idéntica a la de la portada."""
    desktop_items = []
    for url, label in NAV_ITEMS:
        current_attr = ' aria-current="page"' if url == current else ""
        desktop_items.append(f'<a href="{esc(url, quote=True)}"{current_attr}>{esc(label)}</a>')
    desktop = "".join(desktop_items)
    mobile = "\n".join(
        f'        <a href="{esc(url, quote=True)}">{esc(label)}</a>' for url, label in NAV_ITEMS
    )

    return f"""<body>
    <a class="skip-link" href="#main-content">Saltar al contenido</a>
    <header class="navbar">
        <div class="nav-container">
            <a href="/" class="brand" aria-label="{SITE_NAME} — Inicio"><img src="/img/jfg-logo.png" alt="JFG" width="96" height="38"></a>
            <nav class="nav-links desktop-nav" aria-label="Navegación principal">{desktop}</nav>
            <button class="mobile-menu" id="menu-toggle" type="button" aria-label="Abrir menú de navegación" aria-expanded="false" aria-controls="mobile-navigation">{ICON_MENU}</button>
        </div>
        <nav class="mobile-nav" id="mobile-navigation" hidden aria-label="Navegación móvil">
{mobile}
        </nav>
    </header>"""


def footer():
    return """    <footer>
        <img src="/img/jfg-logo.png" alt="JFG" width="96" height="38">
        <span>© 2026 Jesús F. García Gavilán</span>
        <span>Ciencia rigurosa. Ideas claras.</span>
    </footer>
    <script src="/assets/site.js"></script>
</body>
</html>"""


def card(title, url, meta="", description="", links=(), year="", external=False, journal=""):
    """Tarjeta de contenido con el mismo marcado que la portada."""
    target = ' target="_blank" rel="noopener noreferrer"' if external else ""
    year_attr = f' data-year="{esc(year, quote=True)}"' if year else ""
    journal_attr = f' data-journal="{esc(journal, quote=True)}"' if journal else ""

    parts = [f'<article class="card content-card"{year_attr}{journal_attr}>']
    if meta:
        parts.append(f'    <div class="pub-meta">{esc(meta)}</div>')
    parts.append(f'    <a href="{esc(url, quote=True)}" class="pub-title"{target}>{esc(title)}</a>')
    if description:
        parts.append(f'    <p class="text-small">{highlight_author(esc(description))}</p>')
    if links:
        parts.append('    <div class="pub-links">')
        for label, link_url, link_external in links:
            link_target = ' target="_blank" rel="noopener noreferrer"' if link_external else ""
            parts.append(
                f'        <a class="btn-outline" href="{esc(link_url, quote=True)}"{link_target}>'
                f"{esc(label)}{ICON_ARROW_UP_RIGHT}</a>"
            )
        parts.append("    </div>")
    parts.append("</article>")
    return "\n".join(parts)


def archive_filter_controls(placeholder, years=(), journals=(), indent=" " * 20):
    """Buscador y desplegables de una página de archivo.

    Se genera aparte del contenedor para que los scripts de actualización puedan
    reescribir solo los controles y las opciones sigan el contenido real. `indent`
    es la sangría de las líneas siguientes a la primera.
    """
    search_icon = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>'
    )

    controls = [
        f'<div class="filter-search">{search_icon}'
        f'<input type="search" data-archive-search placeholder="{esc(placeholder, quote=True)}" '
        f'aria-label="{esc(placeholder, quote=True)}"></div>'
    ]

    if years:
        options = "".join(f'<option value="{esc(y, quote=True)}">{esc(y)}</option>' for y in years)
        controls.append(
            '<select data-archive-year aria-label="Filtrar por año">'
            '<option value="all">Todos los años</option>'
            f"{options}</select>"
        )

    if journals:
        options = "".join(f'<option value="{esc(j, quote=True)}">{esc(j)}</option>' for j in journals)
        controls.append(
            '<select data-archive-journal aria-label="Filtrar por revista" class="journal-select">'
            '<option value="all">Todas las revistas</option>'
            f"{options}</select>"
        )

    return ("\n" + indent).join(controls)


def archive_filters(placeholder, years=(), journals=()):
    """Bloque completo de filtros para las páginas de archivo."""
    return f"""                <div class="archive-filters">
                    {archive_filter_controls(placeholder, years, journals)}
                </div>
                <p class="result-count" data-archive-count role="status"></p>"""


def page_actions(back_label="Volver al inicio", back_url="/", extra_links=()):
    links = [f'        <a class="btn-outline" href="{esc(back_url, quote=True)}">{ICON_ARROW_LEFT}{esc(back_label)}</a>']
    for label, url in extra_links:
        links.append(f'        <a class="btn-outline" href="{esc(url, quote=True)}">{esc(label)}{ICON_ARROW_UP_RIGHT}</a>')
    joined = "\n".join(links)
    return f"""    <div class="page-actions">
{joined}
    </div>"""
