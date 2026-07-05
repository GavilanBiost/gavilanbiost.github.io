import datetime
import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

# Parametros de busqueda en PubMed
SEARCH_TERM = "garcia-gavilan j"
EMAIL = "gargavilan@gmail.com"

INDEX_PATH = "index.html"
ARCHIVE_PATH = "publicaciones.html"


def fetch_publications():
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": SEARCH_TERM,
        "sort": "date",
        "retmax": 10000,
        "email": EMAIL,
    }

    print("Lanzando ESearch...")
    with urlopen(f"{search_url}?{urlencode(search_params)}", timeout=30) as response:
        response_content = response.read()

    root = ET.fromstring(response_content)
    pmids = [id_elem.text for id_elem in root.findall(".//Id") if id_elem.text]
    print(f"ESearch encontro {len(pmids)} PMIDs")

    if not pmids:
        return []

    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "medline",
        "retmode": "xml",
        "email": EMAIL,
    }

    print("Lanzando EFetch...")
    with urlopen(f"{fetch_url}?{urlencode(fetch_params)}", timeout=60) as fetch_response:
        fetch_content = fetch_response.read()

    fetch_root = ET.fromstring(fetch_content)
    cards = []

    for article in fetch_root.findall(".//PubmedArticle"):
        try:
            title_elem = article.find(".//ArticleTitle")
            title = "Título no disponible"
            if title_elem is not None:
                title = "".join(title_elem.itertext()).strip() or title

            authors = []
            for author in article.findall(".//Author"):
                collective = author.find("CollectiveName")
                if collective is not None and collective.text:
                    authors.append(collective.text)
                    continue

                last = author.find("LastName")
                fore = author.find("ForeName")
                name_parts = []
                if fore is not None and fore.text:
                    name_parts.append(fore.text)
                if last is not None and last.text:
                    name_parts.append(last.text)
                if name_parts:
                    authors.append(" ".join(name_parts))

            if len(authors) > 4:
                authors_str = ", ".join(authors[:4]) + ", ..."
            else:
                authors_str = ", ".join(authors) if authors else "Autores no disponibles"

            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None and journal_elem.text else "Revista no disponible"

            year = "Fecha no disponible"
            year_elem = article.find(".//PubDate/Year")
            if year_elem is None:
                year_elem = article.find(".//ArticleDate/Year")
            if year_elem is not None and year_elem.text:
                year = year_elem.text
            else:
                medline_date = article.find(".//PubDate/MedlineDate")
                if medline_date is not None and medline_date.text and medline_date.text[:4].isdigit():
                    year = medline_date.text[:4]

            doi_elem = article.find('.//ArticleId[@IdType="doi"]')
            doi = doi_elem.text if doi_elem is not None and doi_elem.text else ""

            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None and pmid_elem.text else ""

            if not pmid:
                continue

            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            title_safe = html.escape(title)
            authors_safe = html.escape(authors_str)
            journal_safe = html.escape(journal.upper())

            card = []
            card.append('<div class="card">')
            card.append(f"    <div class=\"pub-meta\">{journal_safe} · {year}</div>")
            card.append(f"    <a href=\"{link}\" class=\"pub-title\" target=\"_blank\">{title_safe}</a>")
            card.append(f"    <p class=\"text-small\">{authors_safe}</p>")
            card.append('    <div class="pub-links">')
            if doi:
                card.append(
                    f"        <a href=\"https://doi.org/{doi}\" class=\"btn-outline\" target=\"_blank\"><i class=\"fa-regular fa-file-pdf\"></i> DOI</a>"
                )
            card.append(
                f"        <a href=\"{link}\" class=\"btn-outline\" target=\"_blank\"><i class=\"fa-solid fa-link\"></i> PubMed</a>"
            )
            card.append("    </div>")
            card.append("</div>")

            cards.append("\n".join(card))
        except Exception as exc:
            print(f"Error procesando articulo: {exc}")

    return cards


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


def update_index(cards, timestamp):
    with open(INDEX_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    latest_three = cards[:3]
    content = replace_div_content(content, "publicaciones-content", "\n".join(latest_three))
    content = replace_last_updated_line(content, "publicaciones-last-updated", f"Última actualización: {timestamp} UTC")

    with open(INDEX_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"✓ Se actualizaron {len(latest_three)} publicaciones en {INDEX_PATH} (últimas 3)")


def update_archive(cards, timestamp):
    with open(ARCHIVE_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    content = replace_div_content(content, "publicaciones-archive-content", "\n".join(cards))
    content = replace_last_updated_line(
        content,
        "publicaciones-archive-last-updated",
        f"Última actualización: {timestamp} UTC",
    )

    with open(ARCHIVE_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"✓ Se actualizaron {len(cards)} publicaciones en {ARCHIVE_PATH}")


def main():
    try:
        cards = fetch_publications()
        if not cards:
            print("No se encontraron publicaciones para la búsqueda")
            raise SystemExit(0)

        timestamp = datetime.datetime.now(datetime.UTC).strftime("%d/%m/%Y %H:%M")
        update_index(cards, timestamp)
        update_archive(cards, timestamp)
    except Exception as exc:
        print(f"Error al actualizar publicaciones: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
