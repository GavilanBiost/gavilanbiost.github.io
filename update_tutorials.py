import datetime
import html
import re
from pathlib import Path

import home_data
import layout
from update_sitemap import generate_sitemap

ARCHIVE_PATH = Path("tutoriales.html")
TUTORIALS_DIR = Path("tutoriales")
EXCLUDED_FILES = {"tutorial-template.html"}
DEFAULT_CATEGORY = "R / TUTORIAL"


def find_div_bounds(content, div_id):
    open_tag_pattern = re.compile(rf'<div\s+id="{re.escape(div_id)}"[^>]*>', re.IGNORECASE)
    open_match = open_tag_pattern.search(content)
    if not open_match:
        raise ValueError(f"No se encontro el div con id={div_id}")

    open_tag_start = open_match.start()
    open_tag_end = open_match.end()

    tag_pattern = re.compile(r"<div\b[^>]*>|</div>", re.IGNORECASE)
    depth = 1
    for match in tag_pattern.finditer(content, open_tag_end):
        token = match.group(0).lower()
        if token.startswith("<div"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                close_tag_start = match.start()
                close_tag_end = match.end()
                return open_tag_start, open_tag_end, close_tag_start, close_tag_end

    raise ValueError(f"No se pudo cerrar el div con id={div_id}")


def replace_div_content(content, div_id, inner_html):
    _, open_end, close_start, _ = find_div_bounds(content, div_id)
    normalized_inner = "\n" + inner_html.strip() + "\n"
    return content[:open_end] + normalized_inner + content[close_start:]


def replace_last_updated_line(content, element_id, new_value):
    pattern = re.compile(
        rf'(<p[^>]*id="{re.escape(element_id)}"[^>]*>)(.*?)(</p>)',
        re.IGNORECASE | re.DOTALL,
    )
    if not pattern.search(content):
        return content
    return pattern.sub(rf"\1{new_value}\3", content)


def extract_meta(content, name):
    pattern = re.compile(
        rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"\s*/?>',
        re.IGNORECASE,
    )
    match = pattern.search(content)
    return html.unescape(match.group(1).strip()) if match else ""


def strip_tags(value):
    text = re.sub(r"<[^>]+>", "", value)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def extract_h1(content):
    match = re.search(r"<h1>(.*?)</h1>", content, re.IGNORECASE | re.DOTALL)
    return strip_tags(match.group(1)) if match else ""


def extract_first_paragraph(content):
    match = re.search(r'<p class="text-small"[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    return strip_tags(match.group(1)) if match else ""


def extract_repo_link(content):
    match = re.search(r'href="(https://github\.com/[^"]+)"', content, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def parse_date(date_text):
    if not date_text:
        return None

    try:
        normalized = date_text.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(normalized)
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.UTC).replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def normalize_href_key(href):
    clean = href.strip().split("#", 1)[0].split("?", 1)[0]
    return Path(clean).name.lower()


def parse_legacy_cards():
    if not ARCHIVE_PATH.exists():
        return {}

    content = ARCHIVE_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<article class="card content-card"[^>]*>\s*'
        r'<div class="pub-meta">(.*?)</div>\s*'
        r'<a href="([^"]+)" class="pub-title"[^>]*>(.*?)</a>\s*'
        r'<p class="text-small">(.*?)</p>\s*'
        r'<div class="pub-links">(.*?)</div>\s*'
        r'</article>',
        re.IGNORECASE | re.DOTALL,
    )

    cards = {}
    for meta, href, title, description, links_block in pattern.findall(content):
        repo_match = re.search(r'href="(https://github\.com/[^"]+)"', links_block, re.IGNORECASE)
        key = normalize_href_key(href)
        cards[key] = {
            "category": strip_tags(meta),
            "title": strip_tags(title),
            "description": strip_tags(description),
            "repo_url": repo_match.group(1).strip() if repo_match else "",
        }

    return cards


def load_tutorials():
    legacy = parse_legacy_cards()
    tutorials = []

    for path in sorted(TUTORIALS_DIR.glob("*.html")):
        if path.name in EXCLUDED_FILES:
            continue

        content = path.read_text(encoding="utf-8")
        key = path.name.lower()
        legacy_entry = legacy.get(key, {})

        title = extract_h1(content) or legacy_entry.get("title") or path.stem.replace("-", " ").title()
        description = extract_meta(content, "description") or legacy_entry.get("description") or extract_first_paragraph(content)
        category = extract_meta(content, "tutorial-category") or legacy_entry.get("category") or DEFAULT_CATEGORY
        repo_url = extract_meta(content, "tutorial-repository") or extract_repo_link(content) or legacy_entry.get("repo_url") or ""
        # El orden sale solo del contenido del archivo. Antes se recurría a la
        # fecha del último commit, pero esa depende del entorno: daba un orden
        # distinto en local y en GitHub Actions, y la lista entera se reescribía
        # provocando conflictos al subir.
        sort_dt = parse_date(extract_meta(content, "tutorial-date"))
        if sort_dt is None:
            print(f"⚠ {path.name} no tiene tutorial-date (AAAA-MM-DD); se ordenará el último")
            sort_dt = datetime.datetime.min


        tutorials.append(
            {
                "title": title,
                "description": description,
                "category": category,
                "repo_url": repo_url,
                "tutorial_url": f"tutoriales/{path.name}",
                "sort_dt": sort_dt,
            }
        )

    tutorials.sort(key=lambda item: (item["sort_dt"], item["title"].lower()), reverse=True)
    return tutorials


def tutorial_links(tutorial):
    links = []
    if tutorial["repo_url"]:
        links.append(("Ver repositorio", tutorial["repo_url"], True))
    links.append(("Abrir tutorial", f"/{tutorial['tutorial_url']}", False))
    return links


def tutorial_year(tutorial):
    return tutorial["sort_dt"].strftime("%Y") if tutorial["sort_dt"] != datetime.datetime.min else ""


def build_card(tutorial):
    return layout.card(
        title=tutorial["title"],
        url=f"/{tutorial['tutorial_url']}",
        meta=tutorial["category"],
        description=tutorial["description"],
        links=tutorial_links(tutorial),
        year=tutorial_year(tutorial),
    )


def update_home(tutorials):
    cards = [
        home_data.card_entry(
            title=tutorial["title"],
            url=f"/{tutorial['tutorial_url']}",
            meta=tutorial["category"],
            description=tutorial["description"],
            links=[(label, url) for label, url, _ in tutorial_links(tutorial)],
            year=tutorial_year(tutorial),
            tags=[part.strip().lower() for part in re.split(r"[/·]", tutorial["category"]) if part.strip()],
        )
        for tutorial in tutorials
    ]
    return home_data.update_section("tutoriales", cards)


def update_archive(tutorials, timestamp):
    content = ARCHIVE_PATH.read_text(encoding="utf-8")
    cards_html = "\n".join(build_card(tutorial) for tutorial in tutorials)
    content = replace_div_content(content, "tutoriales-archive-content", cards_html)
    content = replace_last_updated_line(
        content,
        "tutoriales-archive-last-updated",
        f"Última actualización: {timestamp} UTC",
    )
    ARCHIVE_PATH.write_text(content, encoding="utf-8")


def main():
    tutorials = load_tutorials()
    if not tutorials:
        print("No se encontraron tutoriales para actualizar")
        raise SystemExit(0)

    timestamp = datetime.datetime.now(datetime.UTC).strftime("%d/%m/%Y %H:%M")
    home_count = update_home(tutorials)
    update_archive(tutorials, timestamp)
    generate_sitemap()
    print(f"✓ Se actualizaron {home_count} tutoriales en la portada")
    print(f"✓ Se actualizaron {len(tutorials)} tutoriales en tutoriales.html")


if __name__ == "__main__":
    main()