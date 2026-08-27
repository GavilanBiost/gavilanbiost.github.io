import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_URL = "https://gavilanbiost.com"
SITEMAP_PATH = Path("sitemap.xml")
TUTORIALES_DIR = Path("tutoriales")
POST_DIR = Path("post")

EXCLUDED_TUTORIAL_FILES = {"tutorial-template.html"}
EXCLUDED_POST_FILES = {"post-template.html"}

NS_SITEMAP = "http://www.sitemaps.org/schemas/sitemap/0.9"
NS_IMAGE = "http://www.google.com/schemas/sitemap-image/1.1"


def to_lastmod(path: Path) -> str:
    modified = datetime.datetime.fromtimestamp(path.stat().st_mtime, tz=datetime.UTC)
    return modified.date().isoformat()


def build_entry(url_path: str, file_path: Path, changefreq: str, priority: str, image_url: str = "") -> dict:
    return {
        "loc": f"{BASE_URL}{url_path}",
        "lastmod": to_lastmod(file_path),
        "changefreq": changefreq,
        "priority": priority,
        "image": image_url,
    }


def collect_entries() -> list[dict]:
    entries = []

    static_pages = [
        ("/", Path("index.html"), "weekly", "1.0", f"{BASE_URL}/img/IMG_9589.jpg"),
        ("/biolink.html", Path("biolink.html"), "monthly", "0.8", ""),
        ("/posts.html", Path("posts.html"), "weekly", "0.9", ""),
        ("/tutoriales.html", Path("tutoriales.html"), "weekly", "0.9", ""),
        ("/publicaciones.html", Path("publicaciones.html"), "weekly", "0.9", ""),
        ("/news.html", Path("news.html"), "weekly", "0.8", ""),
    ]

    for url_path, file_path, changefreq, priority, image_url in static_pages:
        if file_path.exists():
            entries.append(build_entry(url_path, file_path, changefreq, priority, image_url))

    if TUTORIALES_DIR.exists():
        tutorial_files = sorted(
            path
            for path in TUTORIALES_DIR.glob("*.html")
            if path.name not in EXCLUDED_TUTORIAL_FILES
        )
        for path in tutorial_files:
            entries.append(
                build_entry(
                    f"/tutoriales/{path.name}",
                    path,
                    "monthly",
                    "0.8",
                )
            )

    if POST_DIR.exists():
        post_files = sorted(
            path
            for path in POST_DIR.glob("*.html")
            if path.name not in EXCLUDED_POST_FILES
        )
        for path in post_files:
            entries.append(
                build_entry(
                    f"/post/{path.name}",
                    path,
                    "monthly",
                    "0.8",
                )
            )

    return entries


def write_sitemap(entries: list[dict]) -> None:
    ET.register_namespace("", NS_SITEMAP)
    ET.register_namespace("image", NS_IMAGE)

    urlset = ET.Element(f"{{{NS_SITEMAP}}}urlset")

    for entry in entries:
        url_node = ET.SubElement(urlset, f"{{{NS_SITEMAP}}}url")
        ET.SubElement(url_node, f"{{{NS_SITEMAP}}}loc").text = entry["loc"]
        ET.SubElement(url_node, f"{{{NS_SITEMAP}}}lastmod").text = entry["lastmod"]
        ET.SubElement(url_node, f"{{{NS_SITEMAP}}}changefreq").text = entry["changefreq"]
        ET.SubElement(url_node, f"{{{NS_SITEMAP}}}priority").text = entry["priority"]

        image_url = entry.get("image", "")
        if image_url:
            image_node = ET.SubElement(url_node, f"{{{NS_IMAGE}}}image")
            ET.SubElement(image_node, f"{{{NS_IMAGE}}}loc").text = image_url
            ET.SubElement(image_node, f"{{{NS_IMAGE}}}title").text = "Jesús F García Gavilán"

    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    tree.write(SITEMAP_PATH, encoding="utf-8", xml_declaration=True)


def generate_sitemap() -> None:
    entries = collect_entries()
    write_sitemap(entries)
    print(f"✓ Sitemap regenerado con {len(entries)} URLs")


def main() -> None:
    generate_sitemap()


if __name__ == "__main__":
    main()