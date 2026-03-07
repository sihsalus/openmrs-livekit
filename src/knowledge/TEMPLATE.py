"""
TEMPLATE — Esqueleto para crear un módulo de conocimiento de Nebu.

Instrucciones:
1. Copia este archivo → `mi_conocimiento.py`
2. Rellena cada sección con datos REALES y verificables
3. Cita tus fuentes académicas en el docstring de arriba
4. Conecta con tu personalidad via `knowledge_injector` (ver personalities/TEMPLATE.md)

Ejemplos existentes:
- andean.py   → Cosmovisión andina (peruvian.yaml)
- mexican.py  → Cosmovisión mesoamericana (mexican.yaml)
- kpop.py     → Cultura coreana (kpop.yaml)
- roblox.py   → Gaming y tech (roblox.yaml)

Cada entrada DEBE tener:
- Versión académica (`descripcion`)
- Versión para niños (`para_ninos`) ← lo que Nebu realmente dice
- Dato extra (`dato_extra`) para enriquecer

Base de datos de cultura REAL, basada en fuentes verificables:
- [AGREGAR FUENTES ACADÉMICAS AQUÍ]
"""

import random


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HISTORIA — Momentos clave
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HISTORIA = [
    {
        "nombre": "Evento histórico 1",
        "periodo": "Siglo X — Siglo Y",
        "descripcion": (
            "Descripción académica detallada del evento. "
            "Contexto histórico, causas y consecuencias."
        ),
        "para_ninos": (
            "Versión para niños: lenguaje simple, entusiasta, "
            "máximo 3-4 oraciones. ¡Que enganche!"
        ),
        "dato_extra": (
            "Dato adicional sorprendente que no repita lo de para_ninos."
        ),
    },
    # Agregar 3-5 entradas más
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILOSOFÍA / CONCEPTOS — Ideas culturales profundas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FILOSOFIA = [
    {
        "nombre": "Concepto 1",
        "termino_original": "Palabra en idioma original",
        "descripcion": (
            "Descripción académica del concepto filosófico o cultural."
        ),
        "para_ninos": (
            "Versión para niños del concepto."
        ),
    },
    # Agregar 3-5 entradas más
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIGURAS CULTURALES — Históricas y contemporáneas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FIGURAS = [
    {
        "nombre": "Persona famosa",
        "titulo": "Descripción corta (ej: 'El inventor del X')",
        "descripcion": (
            "Descripción académica de la figura."
        ),
        "para_ninos": (
            "Versión para niños."
        ),
        "dato_extra": (
            "Dato adicional sorprendente."
        ),
    },
    # Agregar 3-5 entradas más
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INNOVACIONES / LOGROS — Verificables
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INNOVACIONES = [
    {
        "nombre": "Innovación 1",
        "campo": "Área (ej: Tecnología, Agricultura, Arte)",
        "descripcion": (
            "Descripción académica de la innovación."
        ),
        "para_ninos": (
            "Versión para niños."
        ),
        "dato_extra": (
            "Dato adicional."
        ),
    },
    # Agregar 3-5 entradas más
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRADICIONES — Festividades y costumbres
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRADICIONES = [
    {
        "titulo": "Tradición 1",
        "descripcion": (
            "Descripción académica de la tradición."
        ),
        "para_ninos": (
            "Versión para niños."
        ),
        "dato_extra": (
            "Dato adicional."
        ),
    },
    # Agregar 3-5 entradas más
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VOCABULARIO — 8-15 palabras del idioma/jerga de tu cultura
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VOCABULARIO = [
    {
        "palabra": "Palabra en idioma original",
        "significado": "Traducción / significado",
        "uso": "Contexto de uso para Nebu (cuándo y cómo usarla)",
    },
    # Agregar 8-15 entradas
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNCIONES HELPER — Un getter aleatorio por sección
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def get_random_history() -> dict:
    """Retorna una entrada aleatoria de HISTORIA."""
    return random.choice(HISTORIA)


def get_random_philosophy() -> dict:
    """Retorna una entrada aleatoria de FILOSOFIA."""
    return random.choice(FILOSOFIA)


def get_random_figure() -> dict:
    """Retorna una entrada aleatoria de FIGURAS."""
    return random.choice(FIGURAS)


def get_random_innovation() -> dict:
    """Retorna una entrada aleatoria de INNOVACIONES."""
    return random.choice(INNOVACIONES)


def get_random_tradition() -> dict:
    """Retorna una entrada aleatoria de TRADICIONES."""
    return random.choice(TRADICIONES)


def get_random_word() -> dict:
    """Retorna una entrada aleatoria de VOCABULARIO."""
    return random.choice(VOCABULARIO)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUILDER — Punto de entrada, llamado por el knowledge_injector de la personalidad
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Renombra esta función a: build_<tu_id>_knowledge_injection()
# Ej: build_japanese_knowledge_injection, build_colombian_knowledge_injection
#


def build_REPLACE_ME_knowledge_injection() -> str:
    """
    Construye una inyección de conocimiento para el prompt.
    Elige aleatoriamente UNA sección y formatea el bloque.
    """
    blocks = []

    # 1. Elegir fuente aleatoria
    source = random.choice(
        ["historia", "filosofia", "figura", "innovacion", "tradicion"]
    )

    # 2. Formatear según la fuente
    if source == "historia":
        item = get_random_history()
        blocks.append(
            f"CONOCIMIENTO ({item['nombre']}, {item['periodo']}): "
            f"{item['para_ninos']} Dato extra: {item['dato_extra']}"
        )
    elif source == "filosofia":
        item = get_random_philosophy()
        blocks.append(
            f"FILOSOFÍA — {item['nombre']} ({item['termino_original']}): "
            f"{item['para_ninos']}"
        )
    elif source == "figura":
        item = get_random_figure()
        blocks.append(
            f"FIGURA CULTURAL — {item['nombre']}, {item['titulo']}: "
            f"{item['para_ninos']}"
        )
    elif source == "innovacion":
        item = get_random_innovation()
        blocks.append(
            f"INNOVACIÓN — {item['nombre']} ({item['campo']}): "
            f"{item['para_ninos']}"
        )
    elif source == "tradicion":
        item = get_random_tradition()
        blocks.append(
            f"TRADICIÓN — {item['titulo']}: {item['para_ninos']}"
        )

    # 3. Bonus: 40% de chance de agregar una palabra del vocabulario
    if random.random() < 0.4:
        word = get_random_word()
        blocks.append(
            f"PALABRA: '{word['palabra']}' = {word['significado']}. "
            f"¡Enséñasela al niño si encaja!"
        )

    return "\n".join(blocks)
