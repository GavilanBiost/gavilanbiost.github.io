import datetime
import html
import re
from pathlib import Path

INDEX_PATH = Path("index.html")
ARCHIVE_PATH = Path("posts.html")
POSTS_DIR = Path("posts")
MAX_INDEX_POSTS = 3
EXCLUDED_FILES = {"post-template.html"}
DEFAULT_CATEGORY = "BLOG"


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
    match = re.search(r'<article[^>]*id="post-body"[^>]*>\s*<p>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    return strip_tags(match.group(1)) if match else ""


def parse_date(date_text):
    if not date_text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(date_text.strip(), fmt)
        except ValueError:
            continue
    return None


def load_posts():
    posts = []

    for path in sorted(POSTS_DIR.glob("*.html")):
        if path.name in EXCLUDED_FILES:
            continue

        content = path.read_text(encoding="utf-8")

        title = extract_h1(content) or path.stem.replace("-", " ").title()
        description = extract_meta(content, "description") or extract_first_paragraph(content)
        category = extract_meta(content, "post-category") or DEFAULT_CATEGORY
        raw_date = extract_meta(content, "post-date")
        post_dt = parse_date(raw_date) or datetime.datetime.min
        pub_date = post_dt.strftime("%d/%m/%Y") if post_dt != datetime.datetime.min else "Fecha no disponible"

        posts.append(
            {
                "title": title,
                "description": description,
                "category": category,
                "post_url": f"posts/{path.name}",
                "pub_date": pub_date,
                "sort_dt": post_dt,
            }
        )

    posts.sort(key=lambda item: (item["sort_dt"], item["title"].lower()), reverse=True)
    return posts


def build_card(post):
    title = html.escape(post["title"])
    description = html.escape(post["description"])
    category = html.escape(post["category"])
    pub_date = html.escape(post["pub_date"])
    post_url = html.escape(post["post_url"], quote=True)

    card = []
    card.append('<div class="card">')
    card.append(f'    <div class="pub-meta">{category} · {pub_date}</div>')
    card.append(f'    <a href="{post_url}" class="pub-title">{title}</a>')
    if description:
        card.append(f'    <p class="text-small">{description}</p>')
    card.append('    <div class="pub-links">')
    card.append(
        f'        <a href="{post_url}" class="btn-outline"><i class="fa-solid fa-arrow-up-right-from-square"></i> Leer post</a>'
    )
    card.append('    </div>')
    card.append('</div>')
    return "\n".join(card)


def update_index(posts, timestamp):
    content = INDEX_PATH.read_text(encoding="utf-8")
    cards_html = "\n".join(build_card(post) for post in posts[:MAX_INDEX_POSTS])
    content = replace_div_content(content, "posts-content", cards_html)
    content = replace_last_updated_line(content, "posts-last-updated", f"Ultima actualizacion: {timestamp} UTC")
    INDEX_PATH.write_text(content, encoding="utf-8")


def update_archive(posts, timestamp):
    content = ARCHIVE_PATH.read_text(encoding="utf-8")
    cards_html = "\n".join(build_card(post) for post in posts)
    content = replace_div_content(content, "posts-archive-content", cards_html)
    content = replace_last_updated_line(
        content,
        "posts-archive-last-updated",
        f"Última actualización: {timestamp} UTC",
    )
    ARCHIVE_PATH.write_text(content, encoding="utf-8")


def main():
    posts = load_posts()
    if not posts:
        print("No se encontraron posts para actualizar")
        raise SystemExit(0)

    timestamp = datetime.datetime.now(datetime.UTC).strftime("%d/%m/%Y %H:%M")
    update_index(posts, timestamp)
    update_archive(posts, timestamp)
    print(f"✓ Se actualizaron {min(len(posts), MAX_INDEX_POSTS)} posts en index.html")
    print(f"✓ Se actualizaron {len(posts)} posts en posts.html")


if __name__ == "__main__":
    main()
