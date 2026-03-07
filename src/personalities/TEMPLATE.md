# Crear una nueva personalidad de Nebu

## Arquitectura

```
src/
├── personality.py              ← Contrato (PersonalityProfile dataclass)
├── personality_loader.py       ← Carga YAML → PersonalityProfile (deep merge con defaults)
├── personalities/
│   ├── __init__.py             ← Registry: auto-discovery de YAML profiles
│   ├── defaults.yaml           ← Valores compartidos (herencia automática)
│   ├── peruvian.yaml           ← Ejemplo: Nebu Etnocacerista
│   ├── mexican.yaml            ← Ejemplo: Nebu Azteca
│   ├── kpop.yaml               ← Ejemplo: Nebu K-pop Warrior
│   ├── roblox.yaml             ← Ejemplo: Nebu Gamer
│   └── TEMPLATE.yaml           ← Esqueleto para nueva personalidad
└── knowledge/
    ├── andean.py               ← Conocimiento profundo: cosmovisión andina
    ├── mexican.py              ← Conocimiento profundo: mesoamericano
    ├── kpop.py                 ← Conocimiento profundo: cultura coreana
    └── roblox.py               ← Conocimiento profundo: gaming/tech
```

**Flujo:** El `VarietyEngine` (variety.py) lee del `PersonalityProfile` para generar prompts. El módulo de knowledge se inyecta probabilísticamente durante la conversación.

**Herencia:** Cada YAML solo contiene lo que DIFIERE de `defaults.yaml`. El loader hace deep-merge automático: scalars se sobreescriben, listas se reemplazan completas, dicts se mezclan recursivamente.

---

## Paso a paso

### 1. Usa el script de scaffold

```bash
python scripts/new_personality.py
```

Esto crea:
- `src/personalities/<id>.yaml` — desde TEMPLATE.yaml con placeholders rellenos
- `src/knowledge/<id>.py` — esqueleto del módulo de conocimiento

No necesitas tocar `__init__.py` — auto-discovery encuentra todos los YAML.

### 2. Adapta el contenido

Abre tu YAML y reemplaza los placeholders sección por sección. Ve los ejemplos existentes (peruvian.yaml, mexican.yaml) como referencia.

**Importante:** Solo incluye campos que DIFIEREN de `defaults.yaml`. Los valores heredados no necesitan repetirse.

---

## Campos del PersonalityProfile

### Identidad

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `str` | Identificador único, snake_case. Ej: `"peruvian"`, `"kpop"` |
| `display_name` | `str` | Nombre para mostrar. Ej: `"Nebu Etnocacerista"` |
| `description` | `str` | Una línea descriptiva de la personalidad |

### Knowledge config (YAML-only, no son campos de PersonalityProfile)

| Campo YAML | Descripción |
|-------------|-------------|
| `knowledge_module` | Nombre del archivo en `src/knowledge/` (sin .py) |
| `knowledge_function` | Función que retorna `str` con conocimiento |
| `knowledge_special_category` | ID de la categoría con chance 0.25 (el resto usa 0.12) |

### Moods (estados de ánimo)

Lista de dicts. Recomendado **6-8 moods**: 5 base + 2-3 temáticos.

```yaml
moods:
  - name: CURIOSO
    value: curioso
    tone: >-
      Instrucción para el LLM de cómo hablar en este mood...
```

- **name**: Display en MAYÚSCULAS
- **value**: Identificador snake_case (usado en mood_transitions)
- **tone**: Instrucción detallada para el LLM. Usa `>-` para texto multilínea.

**Moods base** (presentes en todas): `curioso`, `emocionado`, `misterioso`, `juguetón`, `asombrado`

**Moods temáticos** (únicos por cultura):
- Peruvian: `modo_inca`, `sabio_andino`, `modo_ceviche`
- Mexican: `modo_mariachi`, `sabio_maya`, `modo_taco`
- K-pop: `modo_idol`, `modo_army`
- Roblox: `modo_noob`, `modo_pro`, `modo_boss`

| Campo relacionado | Tipo | Descripción |
|-------------------|------|-------------|
| `default_mood` | `str` | Heredado de defaults: `"curioso"` |
| `mood_transitions` | `dict` | FSM: desde cada mood, a cuáles puede ir |

### Rapport (niveles de relación)

Lista de 4 dicts. Progresión basada en turnos de conversación.

```yaml
rapport_levels:
  - level: chasqui
    flavor: >-
      Instrucción para el LLM sobre cómo tratar al niño...
```

### Culture Brain (conexiones culturales espontáneas)

| Campo | Tipo | Cantidad | Hereda default? |
|-------|------|----------|-----------------|
| `culture_connections` | `list[dict]` | 6-8 | No |
| `bonus_facts` | `list[str]` | 20 | No |
| `culture_rants` | `list[str]` | 3-5 | No |
| `slang_phrases` | `list[str]` | 10-12 | No |
| `culture_brain_chance` | `float` | — | Sí (0.20) |

### Catchphrases (frases recurrentes)

```yaml
catchphrases:
  pre_fact: [...]      # 10+ frases antes de dar un dato
  post_fact: [...]     # 10+ frases después de dar un dato
  chaining: [...]      # 5+ transiciones entre datos
  wildcard: [...]      # 5+ momentos especiales
  milestone:           # Celebraciones por cantidad de datos
    5: "¡5 datos!"
    10: "¡10 datos!"
```

### Categorías de datos

**`fact_categories`**: Lista de 15-18 categorías.

```yaml
fact_categories:
  - id: animals
    label: Animales
    hint: "dato sobre animales"
    nebu_intro: "[intro cultural]"
    culture_angle: "[ángulo cultural]"
```

**`category_specifics`**: Dict con fun_intros, reactions, transitions por categoría.

### Delivery & Narrative

| Campo | Hereda default? | Descripción |
|-------|-----------------|-------------|
| `delivery_styles` | No | 12 formas de presentar un dato |
| `narrative_patterns` | Sí | 8 IDs de patrones narrativos |
| `pattern_instructions` | Parcial | 6 heredan, 2 culturales van en tu YAML |
| `imperfections` | Sí | 6 vacilaciones que humanizan a Nebu |

Solo necesitas agregar 2 pattern_instructions culturales en tu YAML:
```yaml
pattern_instructions:
  conexion_cultura_primero: "[Instrucción para tu cultura]"
  reflexion_cultural_profunda: "[Instrucción para tu cultura]"
```

### Hype system

| Campo | Hereda default? | Descripción |
|-------|-----------------|-------------|
| `hype_field_name` | No | Label del campo |
| `hype_boost_categories` | No | IDs de categorías que suben hype extra |
| `hype_bias_mood` | No | Mood que se activa cuando hype es alto |
| `hype_initial` | Sí (0.10) | Hype inicial |
| `hype_cap` | Sí (0.70) | Hype máximo |

### Labels culturales

Todos van en tu YAML (no heredan valores útiles):
`culture_angle_label`, `chain_label`, `combo_flavor`, `favorite_mention`, `personality_label`, `flavor_label`, `trivia_culture_hint`, `story_culture_hint`, `riddle_culture_hint`, `debug_version_label`

---

## YAML tips

- Strings con `:` necesitan comillas: `"el chocolate fue inventado en México: los aztecas..."`
- Texto multilínea: usa `>-` (folds + strip trailing newline) o `|-` (literal + strip)
- `persona_anchor_template` usa `|-` con línea vacía para el `\n` inicial
- Milestone keys son enteros: `5:`, `10:`, `25:` (el loader los convierte automáticamente)

---

## Checklist

- [ ] YAML de personalidad creado en `src/personalities/`
- [ ] Módulo de knowledge creado en `src/knowledge/` (ver `knowledge/TEMPLATE.md`)
- [ ] `id` único, no colisiona con los existentes
- [ ] Todos los moods de `moods` aparecen en `mood_transitions`
- [ ] Todos los moods de `signal_mood_map` existen en `moods`
- [ ] `hype_bias_mood` existe en `moods`
- [ ] `hype_boost_categories` solo contiene IDs de `fact_categories`
- [ ] `knowledge_module` apunta a tu módulo de knowledge
- [ ] Tests pasan: `PYTHONPATH=. python -m pytest tests/`
