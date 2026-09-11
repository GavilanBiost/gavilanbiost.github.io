"""Nube de temas de la portada.

Antes era una lista fija dentro del bundle de React, así que solo reflejaba lo
que alguien hubiera escrito a mano. Ahora se calcula contando cuántos contenidos
de TODA la web (posts, tutoriales, publicaciones y noticias) hablan de cada tema,
y se guarda en data/topics.json para que la portada lo lea sin recompilar.

El vocabulario es necesario porque el sitio es bilingüe: las publicaciones están
en inglés y el resto en español. Cada tema tiene una etiqueta en español y un
patrón que reconoce ambas formas, de modo que "Mediterranean diet" y "dieta
mediterránea" suman al mismo tema.

Un tema con `fijo=True` se muestra aunque no aparezca en el contenido indexado:
son temas de los proyectos, que se mantienen a mano en el proyecto React y por
tanto no llegan hasta aquí.
"""

import json
import re
from pathlib import Path

TOPICS_PATH = Path("data/topics.json")
SEARCH_INDEX_PATH = Path("data/search-index.json")

# Cuántos temas se muestran en grande.
MAX_DESTACADOS = 7

# (etiqueta, patrón, fijo). El orden es el de la nube: se respeta tal cual para
# que parezca una nube y no un ranking.
VOCABULARIO = [
    ("machine learning", r"machine learning|aprendizaje autom", True),
    ("nutrición", r"nutric|nutrition|dietary|\bdiet\b|dieta|intake|food", False),
    ("PREDIMED", r"predimed", False),
    ("R", r"(?:^|[\s/·,])r(?:$|[\s/·,])", False),
    ("metabolómica", r"metabolom", False),
    ("Python", r"\bpython\b", False),
    ("dieta mediterránea", r"mediterran|mediterrán", False),
    ("microbiota", r"microbiot|\bgut\b", False),
    ("HIDRIX", r"hidrix", True),
    ("obesidad", r"obesi|overweight|sobrepeso", False),
    ("mujeres", r"\bmujeres\b|\bwomen\b|\bfemale", False),
    ("supervivencia", r"superviven|survival|\bcox\b|hazard", False),
    ("metabolitos", r"metabolit", False),
    ("cardiovascular", r"cardiovascular|cardiometabolic|\bheart\b", False),
    ("ómicas", r"ómic|omics|proteom|genom|transcriptom", False),
    ("diabetes", r"diabet", False),
    ("envejecimiento", r"older adults|aging|ageing|envejec|cognitive", False),
    ("visualización", r"visualiza", False),
    ("síndrome metabólico", r"metabolic syndrome|síndrome metabólico", False),
    ("actividad física", r"physical activity|actividad física|exercise|sedentary", False),
    ("dimensionalidad", r"dimensional|t-sne|\bpca\b", False),
    ("deep learning", r"deep learning", False),
    ("inflamación", r"inflamm|inflamac", False),
    ("mortalidad", r"mortalit|mortalidad", False),
    ("regresión", r"regres", False),
    ("IA", r"\bia\b|inteligencia artificial|artificial intelligence", True),
    ("publicaciones", r"publicacion|publication", True),
]


def _documentos():
    """Un texto por cada contenido de la web, a partir del índice de búsqueda."""
    if not SEARCH_INDEX_PATH.exists():
        return []
    try:
        index = json.loads(SEARCH_INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    docs = []
    for cards in index.values():
        for card in cards:
            partes = [card.get("title", ""), card.get("meta", ""), card.get("description", "")]
            partes.extend(card.get("tags", []))
            docs.append(" ".join(partes).lower())
    return docs


def calcular_temas():
    """Cuenta en cuántos contenidos aparece cada tema y decide cuáles destacan."""
    docs = _documentos()

    conteos = []
    for etiqueta, patron, fijo in VOCABULARIO:
        rx = re.compile(patron)
        n = sum(1 for doc in docs if rx.search(doc))
        if n or fijo:
            conteos.append((etiqueta, n))

    destacados = {
        etiqueta for etiqueta, _ in sorted(conteos, key=lambda x: -x[1])[:MAX_DESTACADOS]
    }
    # Se conserva el orden del vocabulario: el tamaño ya transmite la importancia.
    return [[etiqueta, 1 if etiqueta in destacados and n else 0] for etiqueta, n in conteos]


def update_topics():
    """Reescribe data/topics.json. Devuelve cuántos temas quedaron."""
    temas = calcular_temas()
    TOPICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOPICS_PATH.write_text(
        json.dumps(temas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return len(temas)
