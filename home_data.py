"""Contenido dinámico de la portada y del buscador.

La portada es una aplicación React compilada (assets/home.js), así que no puede
editarse con búsquedas de texto como el resto de páginas. En su lugar lee estos
JSON al cargarse: los scripts de actualización solo tienen que reescribirlos, sin
necesidad de Node ni de recompilar nada (importante porque los workflows de
GitHub Actions solo instalan Python).

Se escriben dos archivos con la misma forma de tarjeta:

- data/home-content.json: las MAX_HOME_CARDS tarjetas más recientes por sección,
  que son las que la portada muestra como destacados.
- data/search-index.json: el archivo completo de cada sección, que el buscador
  descarga bajo demanda para poder encontrar todo el contenido de la web y no
  solo lo que cabe en la portada.
- data/content-counts.json: cuántos elementos tiene cada sección. Es diminuto, así
  que la portada sí lo carga de entrada para enseñar cifras reales (por ejemplo el
  total de publicaciones en el apartado "Sobre mí").

Las secciones que no aparezcan usan el contenido incluido en el bundle, de modo
que 'proyectos' se sigue manteniendo a mano desde el proyecto React.
"""

import json
from pathlib import Path

HOME_DATA_PATH = Path("data/home-content.json")
SEARCH_INDEX_PATH = Path("data/search-index.json")
COUNTS_PATH = Path("data/content-counts.json")
MAX_HOME_CARDS = 3


def card_entry(title, url, meta="", description="", links=(), year="", tags=(), original_title=None):
    """Tarjeta con la forma que espera la portada."""
    return {
        "title": title,
        "url": url,
        "meta": meta,
        "description": description,
        "links": [{"label": label, "url": link_url} for label, link_url in links],
        "originalTitle": original_title if original_title is not None else title,
        "year": year,
        "tags": list(tags),
    }


def _read_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_home_data():
    return _read_json(HOME_DATA_PATH)


def read_search_index():
    return _read_json(SEARCH_INDEX_PATH)


def read_counts():
    return _read_json(COUNTS_PATH)


def update_section(section_id, cards):
    """Guarda las tarjetas de una sección en la portada y en el buscador.

    Recibe el archivo completo de la sección: la portada se queda con las
    MAX_HOME_CARDS primeras, el índice de búsqueda con todas y el contador con el
    total. Devuelve cuántas tarjetas quedan visibles en la portada.
    """
    cards = list(cards)

    home = read_home_data()
    home[section_id] = cards[:MAX_HOME_CARDS]
    _write_json(HOME_DATA_PATH, home)

    index = read_search_index()
    index[section_id] = cards
    _write_json(SEARCH_INDEX_PATH, index)

    counts = read_counts()
    counts[section_id] = len(cards)
    _write_json(COUNTS_PATH, counts)

    return len(home[section_id])
