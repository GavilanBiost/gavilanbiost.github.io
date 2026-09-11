"""Contenido dinámico de la portada.

La portada es una aplicación React compilada (assets/home.js), así que no puede
editarse con búsquedas de texto como el resto de páginas. En su lugar lee este
JSON al cargarse: los scripts de actualización solo tienen que reescribirlo, sin
necesidad de Node ni de recompilar nada (importante porque los workflows de
GitHub Actions solo instalan Python).

Las secciones que no aparezcan en el JSON usan el contenido incluido en el
bundle, de modo que 'proyectos' se sigue manteniendo a mano desde el proyecto
React.
"""

import json
from pathlib import Path

HOME_DATA_PATH = Path("data/home-content.json")
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


def read_home_data():
    if not HOME_DATA_PATH.exists():
        return {}
    try:
        return json.loads(HOME_DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def update_section(section_id, cards):
    """Guarda las últimas tarjetas de una sección en el JSON de la portada."""
    data = read_home_data()
    data[section_id] = list(cards)[:MAX_HOME_CARDS]

    HOME_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    HOME_DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(data[section_id])
