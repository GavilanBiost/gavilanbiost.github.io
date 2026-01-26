import requests
import xml.etree.ElementTree as ET

# Parámetros de búsqueda en PubMed
search_term = 'garcia-gavilan j'  # ajusta el término si quieres filtrar más (p.ej., añadiendo afiliación o rango de fechas)
email = 'gargavilan@gmail.com'

# Paso 1: Buscar artículos usando ESearch
search_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
search_params = {
    'db': 'pubmed',
    'term': search_term,
    'sort': 'date',
    'retmax': 10000,
    'email': email
}

print('Lanzando ESearch...')
response = requests.get(search_url, params=search_params)

if response.status_code != 200:
    print(f'Error en la búsqueda: {response.status_code}')
    raise SystemExit(1)

root = ET.fromstring(response.content)
pmids = [id_elem.text for id_elem in root.findall('.//Id')]
print(f'ESearch encontró {len(pmids)} PMIDs')

if not pmids:
    print('No se encontraron resultados para la búsqueda')
    raise SystemExit(0)

# Paso 2: Obtener detalles de los artículos usando EFetch
fetch_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
fetch_params = {
    'db': 'pubmed',
    'id': ','.join(pmids),
    'rettype': 'medline',
    'retmode': 'xml',
    'email': email
}

print('Lanzando EFetch...')
fetch_response = requests.get(fetch_url, params=fetch_params)

if fetch_response.status_code != 200:
    print(f'Error al obtener detalles: {fetch_response.status_code}')
    raise SystemExit(1)

fetch_root = ET.fromstring(fetch_response.content)
publications = []

for article in fetch_root.findall('.//PubmedArticle'):
    try:
        title_elem = article.find('.//ArticleTitle')
        title = title_elem.text if title_elem is not None else 'Título no disponible'

        authors = []
        for author in article.findall('.//Author'):
            collective = author.find('CollectiveName')
            if collective is not None and collective.text:
                authors.append(collective.text)
                continue

            last = author.find('LastName')
            fore = author.find('ForeName')
            name_parts = []
            if fore is not None and fore.text:
                name_parts.append(fore.text)
            if last is not None and last.text:
                name_parts.append(last.text)
            if name_parts:
                authors.append(' '.join(name_parts))

        authors_str = ', '.join(authors) if authors else 'Autores no disponibles'

        journal_elem = article.find('.//Journal/Title')
        journal = journal_elem.text if journal_elem is not None else 'Revista no disponible'

        year = 'Fecha no disponible'
        year_elem = article.find('.//PubDate/Year') or article.find('.//ArticleDate/Year')
        if year_elem is not None and year_elem.text:
            year = year_elem.text
        else:
            medline_date = article.find('.//PubDate/MedlineDate')
            if medline_date is not None and medline_date.text and medline_date.text[:4].isdigit():
                year = medline_date.text[:4]

        doi_elem = article.find('.//ArticleId[@IdType="doi"]')
        doi = doi_elem.text if doi_elem is not None else ''

        pmid_elem = article.find('.//PMID')
        pmid = pmid_elem.text if pmid_elem is not None else ''

        if pmid:
            link = f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'
            doi_display = f'<a href="https://doi.org/{doi}" target="_blank">{doi}</a>' if doi else 'DOI no disponible'
            publications.append(
                f'<li>'
                f'<strong>{title}</strong><br>'
                f'Autores: {authors_str}<br>'
                f'Revista: {journal} ({year})<br>'
                f'DOI: {doi_display}<br>'
                f'PMID: {pmid} - <a href="{link}" target="_blank">Ver en PubMed</a>'
                f'</li>'
            )
    except Exception as e:
        print(f'Error procesando artículo: {e}')

if not publications:
    print('No se encontraron publicaciones en EFetch')
    raise SystemExit(0)

# Actualizar el archivo index.html
try:
    with open('index.html', 'r', encoding='utf-8') as file:
        content = file.read()

    # Buscar la sección de publicaciones (acepta publicaciones o publications)
    start_marker = None
    for marker in ['<ul id="publicaciones">', '<ul id="publications">']:
        idx = content.find(marker)
        if idx != -1:
            start_marker = marker
            start_index = idx + len(marker)
            break

    end_marker = '</ul>'

    if start_marker:
        end_index = content.find(end_marker, start_index)

        if end_index != -1:
            new_content = '\n'.join(publications)
            updated_content = content[:start_index] + '\n' + new_content + '\n' + content[end_index:]

            with open('index.html', 'w', encoding='utf-8') as file:
                file.write(updated_content)
            print(f'Se escribieron {len(publications)} publicaciones en index.html')
        else:
            print('Error: No se encontró la etiqueta de cierre </ul>')
    else:
        print('No se encontró lista; se creará una nueva sección de publicaciones al final del body')
        new_list = (
            '\n<section class="content-section" id="publicaciones">\n'
            '  <div class="section-header">\n'
            '    <h2><span class="mono-text"></span> Publicaciones</h2>\n'
            '  </div>\n'
            '  <ul id="publicaciones" class="publication-list">\n'
            f'    {'\n    '.join(publications)}\n'
            '  </ul>\n'
            '</section>\n'
        )

        body_end = content.rfind('</body>')
        if body_end == -1:
            body_end = len(content)

        updated_content = content[:body_end] + new_list + content[body_end:]

        with open('index.html', 'w', encoding='utf-8') as file:
            file.write(updated_content)
        print(f'Se creó sección y se escribieron {len(publications)} publicaciones en index.html')
except Exception as e:
    print(f'Error al actualizar index.html: {e}')
