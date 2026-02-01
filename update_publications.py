import requests
import xml.etree.ElementTree as ET
import re

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
        
        # Mostrar solo los primeros 4 autores
        if len(authors) > 4:
            authors_str = ', '.join(authors[:4]) + ', ...'
        else:
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
            
            # Generar HTML en formato card
            pub_html = f'<div class="card">\n'
            pub_html += f'    <div class="pub-meta">{journal.upper()} · {year}</div>\n'
            pub_html += f'    <a href="{link}" class="pub-title" target="_blank">{title}</a>\n'
            pub_html += f'    <p class="text-small">{authors_str}</p>\n'
            pub_html += f'    <div class="pub-links">\n'
            if doi:
                pub_html += f'        <a href="https://doi.org/{doi}" class="btn-outline" target="_blank"><i class="fa-regular fa-file-pdf"></i> DOI</a>\n'
            pub_html += f'        <a href="{link}" class="btn-outline" target="_blank"><i class="fa-solid fa-link"></i> PubMed</a>\n'
            pub_html += f'    </div>\n'
            pub_html += f'</div>'
            
            publications.append(pub_html)
    except Exception as e:
        print(f'Error procesando artículo: {e}')

if not publications:
    print('No se encontraron publicaciones en EFetch')
    raise SystemExit(0)

# Actualizar el archivo index.html
try:
    with open('index.html', 'r', encoding='utf-8') as file:
        content = file.read()

    # Buscar el contenedor de publicaciones usando regex
    # El patrón busca: <div id="publicaciones-content"> ... contenido ... </div>
    # hasta el div que cierra justo antes del botón "ver-mas-publicaciones"
    
    pattern = r'(<div id="publicaciones-content">)(.*?)(</div>\s*<div style="text-align: center[^>]*>\s*<button id="ver-mas-publicaciones")'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # Reemplazar solo el contenido entre las etiquetas
        new_content = '\n' + '\n'.join(publications) + '\n'
        updated_content = content[:match.start(2)] + new_content + content[match.end(2):]
        
        with open('index.html', 'w', encoding='utf-8') as file:
            file.write(updated_content)
        print(f'✓ Se actualizaron {len(publications)} publicaciones en index.html')
    else:
        print('⚠ No se encontró la sección de publicaciones con el formato esperado')
        print('Buscando estructura alternativa...')
        
        # Intentar con un patrón más simple
        simple_pattern = r'(<div id="publicaciones-content">)(.*?)(</div>)'
        simple_match = re.search(simple_pattern, content, re.DOTALL)
        
        if simple_match:
            # Verificar que el cierre esté antes de la sección de proyectos
            next_section_idx = content.find('<section class="content-section" id="proyectos">', simple_match.end())
            button_idx = content.find('id="ver-mas-publicaciones"', simple_match.end())
            
            if button_idx != -1 and button_idx < next_section_idx:
                # Buscar el </div> que cierra publicaciones-content (está justo antes del botón)
                end_search_start = button_idx
                # Buscar hacia atrás el </div> más cercano
                close_div_idx = content.rfind('</div>', simple_match.start(2), button_idx)
                
                if close_div_idx > simple_match.start(2):
                    new_content = '\n' + '\n'.join(publications) + '\n'
                    updated_content = content[:simple_match.start(2)] + new_content + content[close_div_idx:]
                    
                    with open('index.html', 'w', encoding='utf-8') as file:
                        file.write(updated_content)
                    print(f'✓ Se actualizaron {len(publications)} publicaciones en index.html')
                else:
                    print('✗ Error: No se pudo determinar el cierre correcto del contenedor')
            else:
                print('✗ Error: No se encontró el botón ver-mas-publicaciones o la estructura es incorrecta')
        else:
            print('✗ No se encontró la sección de publicaciones; creando una nueva...')
            pub_items = '\n'.join(publications)
            new_list = (
                '\n<section class="content-section" id="publicaciones">\n'
                '    <div class="section-header">\n'
                '        <h2><span class="mono-text"></span> Publicaciones</h2>\n'
                '    </div>\n'
                '    <!-- Lista auto-generada por update_publications.py -->\n'
                '    <div id="publicaciones-content">\n'
                f'{pub_items}\n'
                '    </div>\n'
                '    <div style="text-align: center; margin-top: 20px;">\n'
                '        <button id="ver-mas-publicaciones" class="btn-outline" style="cursor: pointer; padding: 12px 24px; font-size: 1rem;">\n'
                '            <i class="fa-solid fa-plus"></i> Ver más publicaciones\n'
                '        </button>\n'
                '    </div>\n'
                '</section>\n\n'
            )

            # Buscar dónde insertar (antes de la sección de proyectos si existe, o antes de </main>)
            proyectos_idx = content.find('<section class="content-section" id="proyectos">')
            if proyectos_idx != -1:
                insert_idx = proyectos_idx
            else:
                main_end = content.find('</main>')
                insert_idx = main_end if main_end != -1 else content.rfind('</body>')

            updated_content = content[:insert_idx] + new_list + content[insert_idx:]

            with open('index.html', 'w', encoding='utf-8') as file:
                file.write(updated_content)
            print(f'✓ Se creó la sección y se escribieron {len(publications)} publicaciones en index.html')
            
except Exception as e:
    print(f'✗ Error al actualizar index.html: {e}')
    import traceback
    traceback.print_exc()
