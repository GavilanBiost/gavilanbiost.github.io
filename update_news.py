import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from urllib.parse import urlparse

import requests

import home_data
import layout

MAX_NEWS = 400  # Obtener mas noticias para cubrir historico
NEWS_PROVIDERS = [
    {
        "name": "Google News",
        "rss_template": "https://news.google.com/rss/search?q={query}&hl=es-419&gl=ES&ceid=ES:es-419",
        "supports_date_windows": True,
    },
    {
        "name": "Bing News",
        "rss_template": "https://www.bing.com/news/search?q={query}&format=rss&setlang=es-es",
        "supports_date_windows": False,
    },
    {
        "name": "Yahoo News",
        "rss_template": "https://news.search.yahoo.com/rss?p={query}",
        "supports_date_windows": False,
    },
    {
        "name": "GDELT",
        "rss_template": "https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=ArtList&format=rss&maxrecords=50",
        "supports_date_windows": False,
    },
]
MIN_HISTORY_YEAR = 2010
NAME_QUERY_TERMS = [
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

SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


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
        # Mostrar fecha cruda evita perder informacion util cuando llega en
        # formatos no RFC822 (p. ej., cadenas localizadas del proveedor).
        raw_clean = re.sub(r"\s+", " ", html.unescape(raw_date)).strip()
        if raw_clean:
            return datetime.min, raw_clean
        return datetime.min, "Fecha no disponible"


def extract_relative_date_from_text(text: str) -> tuple[datetime, str]:
    if not text:
        return datetime.min, "Fecha no disponible"

    normalized = normalize_text(html.unescape(text))
    match = re.search(
        r"\bhace\s+(\d+)\s+(minuto|minutos|hora|horas|dia|dias|semana|semanas|mes|meses|ano|anos)\b",
        normalized,
    )
    if not match:
        return datetime.min, "Fecha no disponible"

    amount = int(match.group(1))
    unit = match.group(2)
    now = datetime.utcnow()

    if unit in {"minuto", "minutos"}:
        dt = now - timedelta(minutes=amount)
    elif unit in {"hora", "horas"}:
        dt = now - timedelta(hours=amount)
    elif unit in {"dia", "dias"}:
        dt = now - timedelta(days=amount)
    elif unit in {"semana", "semanas"}:
        dt = now - timedelta(weeks=amount)
    elif unit in {"mes", "meses"}:
        dt = now - timedelta(days=30 * amount)
    else:
        dt = now - timedelta(days=365 * amount)

    return dt, dt.strftime("%d/%m/%Y")


def extract_date_from_text(text: str) -> tuple[datetime, str]:
    if not text:
        return datetime.min, "Fecha no disponible"

    plain = html.unescape(text)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()

    # Formato dd/mm/yyyy o dd-mm-yyyy
    match_dmy = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", plain)
    if match_dmy:
        day, month, year = map(int, match_dmy.groups())
        try:
            dt = datetime(year, month, day)
            return dt, dt.strftime("%d/%m/%Y")
        except ValueError:
            pass

    # Formato yyyy-mm-dd
    match_ymd = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", plain)
    if match_ymd:
        year, month, day = map(int, match_ymd.groups())
        try:
            dt = datetime(year, month, day)
            return dt, dt.strftime("%d/%m/%Y")
        except ValueError:
            pass

    # Formato "25 de marzo de 2026"
    match_spanish = re.search(
        r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b",
        plain,
        flags=re.IGNORECASE,
    )
    if match_spanish:
        day = int(match_spanish.group(1))
        month_name = normalize_text(match_spanish.group(2))
        year = int(match_spanish.group(3))
        month = SPANISH_MONTHS.get(month_name)
        if month:
            try:
                dt = datetime(year, month, day)
                return dt, dt.strftime("%d/%m/%Y")
            except ValueError:
                pass

    return datetime.min, "Fecha no disponible"


def get_item_text(item: ET.Element, tag_name: str) -> str:
    elem = item.find(tag_name)
    if elem is None or elem.text is None:
        return ""
    return elem.text.strip()


def resolve_article_url(raw_url: str) -> str:
    """Resuelve links de Google News a la URL final del artículo cuando es posible."""
    if not raw_url:
        return ""

    parsed = urlparse(raw_url)
    if parsed.netloc.lower() not in {"news.google.com", "www.news.google.com"}:
        return raw_url

    try:
        response = requests.get(
            raw_url,
            timeout=15,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; JFGG-NewsBot/1.0; +https://github.com/GavilanBiost/gavilanbiost.github.io)"
            },
        )
        if response.ok:
            final_url = response.url or raw_url
            return final_url
    except requests.RequestException:
        pass

    try:
        response = requests.get(
            raw_url,
            timeout=15,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if response.ok:
            final_url = response.url or raw_url
            if final_url and "news.google.com" not in final_url:
                return final_url
    except requests.RequestException:
        pass

    return raw_url


def build_dedupe_key(
    title: str,
    link: str,
    pub_date: str,
    source: str,
) -> str:
    normalized_title = normalize_text(title or "sin titulo")
    if len(normalized_title) > 140:
        normalized_title = normalized_title[:140]

    domain = ""
    if link:
        parsed = urlparse(link)
        domain = (parsed.netloc or "").lower()
        if domain.startswith("www."):
            domain = domain[4:]

    if not domain:
        domain = normalize_text(source or "desconocido")

    normalized_date = pub_date if pub_date and pub_date != "Fecha no disponible" else ""
    return f"{normalized_title}|{domain}|{normalized_date}"


def build_search_queries(use_date_windows: bool = True) -> list[str]:
    current_year = datetime.utcnow().year
    date_windows = [""]

    # Dividir por año fuerza a Google News a devolver resultados historicos.
    if use_date_windows:
        for year in range(current_year, MIN_HISTORY_YEAR - 1, -1):
            date_windows.append(f" after:{year}-01-01 before:{year + 1}-01-01")

    queries = []
    seen = set()
    for base_term in NAME_QUERY_TERMS:
        for window in date_windows:
            query = f"{base_term}{window}".strip()
            if query not in seen:
                seen.add(query)
                queries.append(query)
    return queries


def fetch_news() -> list[dict]:
    all_news = {}

    for provider in NEWS_PROVIDERS:
        provider_name = provider["name"]
        rss_template = provider["rss_template"]
        use_date_windows = provider.get("supports_date_windows", False)

        for query_term in build_search_queries(use_date_windows=use_date_windows):
            strict_query = '"' in query_term
            feed_url = rss_template.format(query=quote_plus(query_term))
            print(f"[{provider_name}] Consultando: {query_term}")

            try:
                response = requests.get(feed_url, timeout=20)
                response.raise_for_status()
            except requests.RequestException as exc:
                print(f"  [{provider_name}] Error en feed: {exc}")
                continue

            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as exc:
                print(f"  [{provider_name}] XML invalido: {exc}")
                continue

            items = root.findall(".//item")

            for item in items:
                title = get_item_text(item, "title")
                link = resolve_article_url(get_item_text(item, "link"))
                description = get_item_text(item, "description")
                source = get_item_text(item, "source") or provider_name
                pub_date_raw = (
                    get_item_text(item, "pubDate")
                    or get_item_text(item, "published")
                    or get_item_text(item, "updated")
                )

                combined_text = f"{title} {description}"
                # Cuando la consulta usa frase exacta, el buscador ya aplica
                # una restriccion semantica fuerte.
                if not strict_query and not contains_name_variant(combined_text):
                    continue

                if not title and not description:
                    continue

                pub_dt, pub_date = format_pub_date(pub_date_raw)
                if pub_dt == datetime.min:
                    pub_dt, pub_date = extract_date_from_text(f"{title} {description}")
                if pub_dt == datetime.min:
                    pub_dt, pub_date = extract_relative_date_from_text(f"{title} {description}")

                key = build_dedupe_key(
                    title=title,
                    link=link,
                    pub_date=pub_date,
                    source=source,
                )
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


def news_year(item: dict) -> str:
    return str(item["pub_dt"].year) if item["pub_dt"] != datetime.min else ""


def build_news_card(item: dict) -> str:
    return layout.card(
        title=item["title"] or "Sin título",
        url=item["link"] or "#",
        meta=f"{item['source'] or 'Google News'} · {item['pub_date'] or 'Fecha no disponible'}",
        year=news_year(item),
        external=True,
    )


def update_home(news_items: list[dict]) -> None:
    """Guarda las noticias en los JSON que leen la portada y el buscador."""
    cards = [
        home_data.card_entry(
            title=item["title"] or "Sin título",
            url=item["link"] or "#",
            meta=f"{item['source'] or 'Google News'} · {item['pub_date'] or 'Fecha no disponible'}",
            description=item["source"] or "",
            year=news_year(item),
        )
        for item in news_items
    ]
    count = home_data.update_section("noticias", cards)
    print(f"✓ Se actualizaron {count} noticias en la portada")


def create_news_page(all_news: list[dict]) -> None:
    """Crea la página news.html con todas las noticias agrupadas por año."""
    generated_at = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    # Agrupar noticias por año, de más reciente a más antiguo.
    news_by_year: dict[int, list[dict]] = {}
    for item in all_news:
        year = item["pub_dt"].year if item["pub_dt"] != datetime.min else 0
        news_by_year.setdefault(year, []).append(item)

    body_parts = []
    for year in sorted(news_by_year, reverse=True):
        label = str(year) if year != 0 else "Sin fecha"
        body_parts.append(f'<h3 class="archive-year">{html.escape(label)}</h3>')
        for item in news_by_year[year]:
            body_parts.append(build_news_card(item))

    if not body_parts:
        body_parts.append(
            '<p class="archive-empty">No se encontraron noticias con menciones a Jesús F García Gavilán.</p>'
        )

    years = [str(year) for year in sorted(news_by_year, reverse=True) if year != 0]

    page = "\n".join(
        [
            layout.head(
                "Noticias · Jesús F. García Gavilán",
                "Menciones en prensa y divulgación de la investigación de Jesús F. García Gavilán.",
                f"{layout.SITE_URL}/news.html",
            ),
            layout.navbar(current="/news.html"),
            '    <div class="page-shell">',
            '        <main id="main-content">',
            '            <section class="content-section" id="noticias" data-archive aria-labelledby="noticias-heading">',
            '                <div class="page-header">',
            '                    <p class="eyebrow">PRENSA · MENCIONES</p>',
            '                    <h1 id="noticias-heading">Noticias</h1>',
            '                    <p>Menciones en prensa y divulgación de la investigación en la que he participado.</p>',
            "                </div>",
            f'                <p class="page-meta" id="noticias-archive-last-updated">Última actualización: {generated_at}</p>',
            layout.archive_filters("Buscar noticias", years),
            '                <div id="noticias-archive-content">',
            "\n".join(body_parts),
            "                </div>",
            '                <p class="archive-empty" data-archive-empty hidden>Sin coincidencias. Prueba otra palabra clave o quita los filtros.</p>',
            layout.page_actions(),
            "            </section>",
            "        </main>",
            "    </div>",
            layout.footer(),
        ]
    )

    with open("news.html", "w", encoding="utf-8") as f:
        f.write(page + "\n")


if __name__ == "__main__":
    print("Buscando noticias...")
    all_news = fetch_news()
    print(f"Noticias relevantes encontradas: {len(all_news)}")
    
    # Actualizar la portada con solo las últimas noticias
    update_home(all_news)

    # Crear página de archivo con todas las noticias por año
    create_news_page(all_news)
    print(f"✓ news.html creado con {len(all_news)} noticias agrupadas por año")
