# Crear un módulo de Knowledge para Nebu

## Qué es

Cada personalidad tiene un módulo de conocimiento profundo: datos reales, académicos y verificables sobre la cultura. El `knowledge_injector` del perfil de personalidad llama a `build_*_knowledge_injection()` para inyectar bloques de conocimiento en el prompt durante la conversación.

## Estructura común

Todos los módulos siguen el mismo patrón. Hay **6 secciones de datos** + **helpers** + **builder**.

```
src/knowledge/
├── andean.py     ← Cosmovisión andina (peruvian.py)
├── mexican.py    ← Cosmovisión mesoamericana (mexican.py)
├── kpop.py       ← Cultura coreana (kpop.py)
└── roblox.py     ← Gaming y tech (roblox.py)
```

---

## Las 6 secciones de datos

Cada módulo tiene **5-7 listas/dicts** de datos organizados por tema. El esquema de cada entrada varía pero siempre incluye:

- Una versión académica (`descripcion`)
- Una versión para niños (`para_ninos`) — **esta es la que usa Nebu**
- Un dato extra (`dato_extra`) para enriquecer

### Comparación entre módulos

| # | andean.py | kpop.py | mexican.py | roblox.py |
|---|-----------|---------|------------|-----------|
| 1 | Tres Pachas (cosmología) | Historia Coreana | Cosmovisión Mesoamericana | Historia del Gaming |
| 2 | Principios Andinos (filosofía) | Filosofía Coreana | Filosofía Mesoamericana | Filosofía Gamer |
| 3 | Panteón Andino (deidades) | Figuras Culturales | Panteón Mesoamericano | Figuras del Gaming |
| 4 | Sistemas Sociales + Conceptos | Innovaciones Coreanas | Ciencia Mesoamericana | Innovaciones Tech |
| 5 | Ciencia Andina (logros) | Tradiciones Coreanas | Tradiciones Mesoamericanas | Tradiciones Gaming |
| 6 | Manuscrito de Huarochirí (mitos) | — | Códices y Mitos | — |
| 7 | Vocabulario Quechua | Vocabulario Coreano | Vocabulario Náhuatl | Vocabulario Gamer |

### Formato típico de una entrada

```python
{
    "nombre": "Nombre del concepto",
    "campo": "Categoría",                    # o "periodo", "titulo", "hangul", etc.
    "descripcion": "Texto académico...",      # Versión completa
    "para_ninos": "Texto para niños...",      # ← Lo que Nebu realmente dice
    "dato_extra": "Dato adicional...",        # Bonus fact
}
```

Los campos exactos varían según la sección (ver ejemplos existentes), pero `para_ninos` y `dato_extra` siempre están.

---

## Helpers (funciones `get_random_*`)

Cada sección tiene un helper simple:

```python
def get_random_pacha_wisdom() -> dict:
    """Retorna una entrada aleatoria de TRES_PACHAS."""
    return random.choice(TRES_PACHAS)
```

Un helper por cada lista de datos. Naming: `get_random_<seccion>()`.

---

## Builder (función principal)

La función `build_*_knowledge_injection() -> str` es el punto de entrada. Patrón:

```python
def build_MICULTURA_knowledge_injection() -> str:
    blocks = []

    # 1. Elegir aleatoriamente UNA sección como fuente
    source = random.choice(["historia", "filosofia", "figura", ...])

    # 2. Formatear el bloque según la fuente
    if source == "historia":
        item = get_random_history()
        blocks.append(f"CONOCIMIENTO ({item['nombre']}): {item['para_ninos']} ...")
    elif source == "filosofia":
        ...

    # 3. Bonus: 40% de chance de agregar una palabra del vocabulario
    if random.random() < 0.4:
        word = get_random_word()
        blocks.append(f"PALABRA: '{word['palabra']}' = {word['significado']}. ...")

    return "\n".join(blocks)
```

---

## Conexión con la personalidad

En tu archivo de personalidad (`personalities/mi_personalidad.py`):

```python
from src.knowledge.mi_conocimiento import build_mi_knowledge_injection

def _knowledge_injector(category_id: str) -> str:
    chance = 0.25 if category_id == "mi_categoria_especial" else 0.12
    if random.random() > chance:
        return ""
    return f"\n📚 {build_mi_knowledge_injection()}"

profile = PersonalityProfile(
    ...
    knowledge_injector=_knowledge_injector,
    ...
)
```

---

## Requisitos de calidad

- **Datos REALES y verificables**. Citar fuentes académicas en el docstring del módulo.
- **`para_ninos`**: Lenguaje simple, entusiasta, máximo 3-4 oraciones. Nebu habla a niños de 6-12 años.
- **`dato_extra`**: Un bonus fact que sorprenda. No repetir lo de `para_ninos`.
- **Vocabulario**: 8-15 palabras con `palabra`, `significado`, y `uso` (contexto de cómo usarla).
- **Cantidad**: 3-5 entradas por sección mínimo para tener variedad.

## Checklist

- [ ] Docstring con fuentes académicas
- [ ] 5-7 secciones de datos con `para_ninos` y `dato_extra`
- [ ] Sección de vocabulario (8-15 palabras)
- [ ] Un `get_random_*()` por cada sección
- [ ] Función `build_*_knowledge_injection()` que cubre todas las secciones
- [ ] Import funciona desde `src/knowledge/mi_modulo`
- [ ] Conectado en la personalidad via `knowledge_injector`
