import datetime
import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

import home_data
import layout

# Parametros de busqueda en PubMed
SEARCH_TERM = "garcia-gavilan j"
EMAIL = "gavilanbiost@gmail.com"

ARCHIVE_PATH = "publicaciones.html"


def extract_publication_year(article):
    date_patterns = [
        ".//PubDate/Year",
        ".//ArticleDate/Year",
        ".//PubDate/MedlineDate",
        ".//ArticleDate/MedlineDate",
        ".//History/PubMedPubDate/Year",
        ".//History/PubMedPubDate/MedlineDate",
        ".//PubDate/Month",
        ".//ArticleDate/Month",
    ]

    for pattern in date_patterns:
        for elem in article.findall(pattern):
            if elem is None or elem.text is None:
                continue
            value = elem.text.strip()
            if not value:
                continue
            match = re.search(r"(\d{4})", value)
            if match:
                return match.group(1)

    return None


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

            year = extract_publication_year(article)

            doi_elem = article.find('.//ArticleId[@IdType="doi"]')
            doi = doi_elem.text if doi_elem is not None and doi_elem.text else ""

            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None and pmid_elem.text else ""

            if not pmid:
                continue

            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            cards.append(
                {
                    "title": title,
                    "authors": authors_str,
                    "journal": journal.upper(),
                    "year": year or "",
                    "doi": doi,
                    "link": link,
                }
            )
        except Exception as exc:
            print(f"Error procesando articulo: {exc}")

    return cards


def publication_meta(publication):
    parts = [publication["journal"]]
    if publication["year"]:
        parts.append(publication["year"])
    return " · ".join(parts)


def publication_links(publication):
    links = []
    if publication["doi"]:
        links.append(("DOI", f"https://doi.org/{publication['doi']}", True))
    links.append(("PubMed", publication["link"], True))
    return links


def build_card(publication):
    return layout.card(
        title=publication["title"],
        url=publication["link"],
        meta=publication_meta(publication),
        description=publication["authors"],
        links=publication_links(publication),
        year=publication["year"],
        external=True,
        journal=publication["journal"],
    )


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


def update_home(publications):
    cards = [
        home_data.card_entry(
            title=publication["title"],
            url=publication["link"],
            meta=publication_meta(publication),
            description=publication["authors"],
            links=[(label, url) for label, url, _ in publication_links(publication)],
            year=publication["year"],
        )
        for publication in publications
    ]
    count = home_data.update_section("publicaciones", cards)
    print(f"✓ Se actualizaron {count} publicaciones en la portada")


def update_archive(publications, timestamp):
    with open(ARCHIVE_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    cards_html = "\n".join(build_card(publication) for publication in publications)
    content = replace_div_content(content, "publicaciones-archive-content", cards_html)

    years = sorted({p["year"] for p in publications if p["year"]}, reverse=True)
    journals = sorted({p["journal"] for p in publications if p["journal"]})
    content = replace_div_content(
        content,
        "publicaciones-archive-filters",
        # Sin sangría: el contenido regenerado de esta página va a columna cero.
        layout.archive_filter_controls("Título, autor o revista", years, journals, indent=""),
    )
    content = replace_last_updated_line(
        content,
        "publicaciones-archive-last-updated",
        f"Última actualización: {timestamp} UTC",
    )

    with open(ARCHIVE_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"✓ Se actualizaron {len(publications)} publicaciones en {ARCHIVE_PATH}")


def sync_publication_pages(publications, timestamp):
    update_home(publications)
    update_archive(publications, timestamp)


def main():
    try:
        cards = fetch_publications()
        if not cards:
            print("No se encontraron publicaciones para la búsqueda")
            raise SystemExit(0)

        timestamp = datetime.datetime.now(datetime.UTC).strftime("%d/%m/%Y %H:%M")
        sync_publication_pages(cards, timestamp)
    except Exception as exc:
        print(f"Error al actualizar publicaciones: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
