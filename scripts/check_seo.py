"""Audit the static site and its sitemap using Python's standard library.

Run from the repository root: python scripts/check_seo.py
Checks the equivalents of Yoast's on-page basics, not a Yoast score or rankings.
"""
import datetime
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

BASE = "https://gavilanbiost.com"
ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.meta = {}
        self.canonicals = []
        self.images = []
        self.resources = []
        self.links = []
        self.ids = set()
        self.h1_count = 0
        self.title = ""
        self.lang = ""
        self.schemas = []
        self.in_title = False
        self.in_schema = False
        self.schema_text = ""
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "html":
            self.lang = attrs.get("lang", "")
        if tag == "h1":
            self.h1_count += 1
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            key = attrs.get("name", attrs.get("property", ""))
            if key and key in self.meta and key not in {"article:tag"}:
                raise ValueError(f"duplicate meta: {key}")
            if key:
                self.meta[key] = attrs.get("content", "")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href", ""))
        if tag == "img":
            self.images.append(attrs)
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag in {"img", "script", "source"} and attrs.get("src"):
            self.resources.append(attrs["src"])
        if tag == "link" and attrs.get("rel") in {"stylesheet", "icon", "apple-touch-icon"}:
            self.resources.append(attrs.get("href", ""))
        if attrs.get("srcset"):
            self.resources.extend(item.strip().split()[0] for item in attrs["srcset"].split(","))
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_schema = True
            self.schema_text = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_schema:
            self.schemas.append(json.loads(self.schema_text))
            self.in_schema = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_schema:
            self.schema_text += data

    @property
    def url(self):
        relative = self.path.relative_to(ROOT).as_posix()
        return BASE + ("/" if relative == "index.html" else "/" + relative)

    @property
    def indexable(self):
        return "noindex" not in self.meta.get("robots", "").lower()


def local_path(url):
    parsed = urlsplit(url)
    if parsed.netloc != urlsplit(BASE).netloc or parsed.scheme not in {"https", "http"}:
        return None
    return ROOT / unquote(parsed.path.lstrip("/") or "index.html")


def schema_urls(value):
    if isinstance(value, dict):
        if value.get("@type") == "ImageObject":
            yield value.get("url", value.get("contentUrl", ""))
        for child in value.values():
            yield from schema_urls(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_urls(child)


def audit():
    errors = []
    warnings = []
    pages = {}
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        try:
            pages[path] = Page(path)
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    for path, page in pages.items():
        relative = path.relative_to(ROOT).as_posix()
        def fail(message):
            errors.append(f"{relative}: {message}")
        if path.name.endswith("template.html"):
            if page.indexable:
                fail("template must have noindex")
            continue
        if page.lang != "es" or page.h1_count != 1:
            fail(f"lang={page.lang!r}; H1 count={page.h1_count}")
        expected = page.url
        if not relative.startswith("preview/") and page.canonicals != [expected]:
            fail(f"canonical must be {expected}")
        if not page.schemas:
            fail("missing structured data")
        if not page.title or not page.meta.get("description"):
            fail("missing title or description")
        if page.indexable and not 30 <= len(page.title) <= 65:
            warnings.append(f"{relative}: title has {len(page.title)} characters; assess displayed width")
        if page.indexable and not 120 <= len(page.meta.get("description", "")) <= 160:
            warnings.append(f"{relative}: description length outside editorial target")
        for field in ["url", "title", "description", "image"]:
            og, twitter = page.meta.get("og:" + field), page.meta.get("twitter:" + field)
            if not og or og != twitter:
                fail(f"Open Graph/Twitter mismatch: {field}")
        if page.meta.get("og:description") != page.meta.get("description"):
            fail("description differs from social snippet")
        for key in ["og:image:alt", "twitter:image:alt", "og:image:width", "og:image:height"]:
            if not page.meta.get(key):
                fail(f"missing {key}")
        for key in ["og:image:alt", "twitter:image:alt"]:
            if not 10 <= len(page.meta.get(key, "")) <= 200:
                fail(f"{key} length outside descriptive range")
        image_refs = [page.meta.get(key, "") for key in ["og:image", "twitter:image", "post-image"]]
        image_refs += list(schema_urls(page.schemas))
        for ref in set(page.resources + image_refs):
            target = local_path(urljoin(page.url, ref)) if ref else None
            if target and not target.is_file():
                fail(f"missing resource: {ref}")
        for ref in page.links:
            url = urljoin(page.url, ref)
            target = local_path(url)
            if target is None:
                continue
            if not target.is_file():
                fail(f"broken internal link: {ref}")
            elif urlsplit(url).fragment and target in pages:
                if unquote(urlsplit(url).fragment) not in pages[target].ids:
                    fail(f"missing anchor: {ref}")
        alt_values = []
        for image in page.images:
            if not image.get("width", "").isdigit() or not image.get("height", "").isdigit():
                fail(f"missing image dimensions: {image.get('src')}")
            alt = image.get("alt")
            decorative = image.get("src") == "/img/jfg-logo.png" and alt == ""
            if not decorative and (alt is None or not 10 <= len(alt) <= 200):
                fail(f"image alt must describe the visual in 10–200 characters: {image.get('src')}")
            if alt:
                alt_values.append(alt)
        for alt, count in Counter(alt_values).items():
            if count > 1:
                fail(f"repeated image alt: {alt}")
        if page.meta.get("post-date", "") > today and page.indexable:
            fail("future post must remain noindex until its publication date")
    for field in ["title", "description"]:
        values = Counter((p.title if field == "title" else p.meta.get(field)) for p in pages.values() if p.indexable)
        for value, count in values.items():
            if count > 1:
                errors.append(f"duplicate {field}: {value}")
    namespaces = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "i": "http://www.google.com/schemas/sitemap-image/1.1"}
    sitemap = ET.parse(ROOT / "sitemap.xml")
    locations = [el.text for el in sitemap.findall("s:url/s:loc", namespaces)]
    expected = {page.url for page in pages.values() if page.indexable}
    if set(locations) != expected or len(locations) != len(set(locations)):
        errors.append(f"sitemap mismatch: missing={expected - set(locations)}; extra={set(locations) - expected}")
    for el in sitemap.findall("s:url/i:image/i:loc", namespaces):
        target = local_path(el.text)
        if target and not target.is_file():
            errors.append(f"missing sitemap image: {el.text}")
    for el in sitemap.findall("s:url/s:lastmod", namespaces):
        if el.text > today:
            errors.append(f"future lastmod: {el.text}")
    if f"Sitemap: {BASE}/sitemap.xml" not in (ROOT / "robots.txt").read_text():
        errors.append("robots.txt must reference the sitemap")
    for message in errors:
        print("ERROR", message)
    for message in warnings:
        print("REVIEW", message)
    print(f"Checked {len(pages)} HTML files, {len(expected)} indexable URLs, {sum(len(p.images) for p in pages.values())} img elements; {len(errors)} errors, {len(warnings)} editorial notices.")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(audit())
