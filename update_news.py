import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests

MAX_NEWS = 20
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
    '"Garcia Gavilan"',
    '"Garcia-Gavilan"',
    '"Garcia Gavilan"',
    '"García Gavilán"',
    '"García-Gavilán"',
    '"Gavilan"',
    '"Gavilán"',
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

    # Explicitly accept any Gavilan mention as requested.
    if has_gavilan:
        return True

    patterns = [
        r"\bjesus\s+f(?:rancisco)?\s+garcia\s+gavilan\b",
        r"\bjesus\s+garcia\s+gavilan\b",
        r"\bj\s*f\s+garcia\s+gavilan\b",
        r"\bgarcia\s+gavilan\b",
        r"\bjesus\s+f\s+garcia\b",
    ]

    if (has_garcia and has_jesus) or (has_garcia and has_initials):
        return True

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


def build_news_cards(news_items: list[dict]) -> str:
    cards = []

    for item in news_items:
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
    with open("index.html", "r", encoding="utf-8") as file:
        content = file.read()

    pattern = (
        r'(<div id="noticias-content">)'
        r'(.*?)'
        r'(</div>\s*<div style="text-align: center; margin-top: 20px;">\s*<button id="ver-mas-noticias")'
    )

    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise RuntimeError("No se encontro la seccion de noticias en index.html")

    replacement = "\n" + news_html + "\n"
    updated = content[: match.start(2)] + replacement + content[match.end(2) :]

    with open("index.html", "w", encoding="utf-8") as file:
        file.write(updated)


if __name__ == "__main__":
    print("Buscando noticias...")
    news = fetch_news()
    print(f"Noticias relevantes encontradas: {len(news)}")
    html_cards = build_news_cards(news)
    update_index_html(html_cards)
    print("index.html actualizado con la seccion de noticias")
