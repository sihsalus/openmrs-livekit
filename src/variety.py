"""
Variety Engine v4 — Sistema de personalidad parametrizable.

Motor anti-repetición con personalidad configurable para Nebu.
La mecánica del engine (anti-repetición, patches, FSM) es universal.
El contenido cultural viene del PersonalityProfile.

Patches de investigación integrados:
- Persona Anchor (anti attention-decay)
- Narrative Pattern Dedup (anti-repetición semántica)
- Sliding Summary (compresión temporal)
- Imperfecciones Orgánicas (pasar el Turing test)
- FSM Mood Lite (transiciones reactivas al input del niño)

El LLM genera todo el contenido (los datos son reales).
El engine lo guía para que no se repita Y para que tenga personalidad.
"""

import random
import time
from collections import deque
from dataclasses import dataclass, field

from src.personality import PersonalityProfile

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚫 DATOS PROHIBIDOS — Universales, no dependen del perfil
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BANNED_FACTS = [
    "los pájaros no tienen Twitter / redes sociales",
    "los flamencos son rosados por los camarones",
    "los delfines duermen con un ojo abierto",
    "los gatos tienen 9 vidas",
    "la Gran Muralla China se ve desde el espacio",
    "los perros ven en blanco y negro",
    "el corazón de un camarón está en su cabeza",
    "las vacas tienen mejores amigos",
    "los pulpos tienen 3 corazones",
    "los humanos usan solo el 10% del cerebro",
    "los diamantes son carbón comprimido",
    "la miel no se echa a perder / nunca caduca",
    "el plátano es una baya / la fresa no es una baya",
    "los bebés tienen más huesos que los adultos",
    "la lengua es el músculo más fuerte",
    "los koalas duermen 22 horas",
    "los goldfish tienen 3 segundos de memoria",
    "Cleopatra está más cerca de nosotros que de las pirámides",
    "el Everest no es la montaña más alta desde la base",
    "los rayos son más calientes que el sol",
]

WILDCARD_CHANCE = 0.12
IMPERFECTION_CHANCE = 0.18


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧠 MEMORY TRACKER — Estado anti-repetición de la sesión
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class MemoryTracker:
    """
    Estado anti-repetición para una sesión de conversación.

    Separado de VarietyEngine para que FSM/mood/cultura no mezclen
    responsabilidades con el tracking de lo ya dicho.

    Maxlens justificados:
    - fact_categories_used  maxlen=10: ~2 rotaciones completas antes del reset;
                                       suficiente para evitar clustering de temas
    - styles_used           maxlen=4:  ~mitad de los estilos disponibles;
                                       fuerza alternancia sin sobre-restringir
    - trivia_categories_used maxlen=8: cubre la mayoría de categorías de trivia
                                       antes de reciclar
    - story_themes_used     maxlen=8:  ídem trivia
    - catchphrases_used     maxlen=4:  por slot (pre/post); ventana pequeña
                                       para que las frases se sientan frescas
    - pattern_history       maxlen=6:  cubre los arquetipos narrativos comunes
                                       antes de ciclar (Patch 2)
    - agent_responses       maxlen=8:  ~8 turnos de output real del LLM
                                       realimentados para dedup textual

    Deques con maxlen fijo:
    - facts_told    maxlen=25:  balance costo de contexto LLM vs. cobertura
    - riddles_told  maxlen=15:  las adivinanzas tienen menos variedad;
                                ventana más pequeña es suficiente
    """

    # Rotating deques — Python evicts oldest entries automatically at maxlen
    fact_categories_used: deque = field(default_factory=lambda: deque(maxlen=10))
    styles_used: deque = field(default_factory=lambda: deque(maxlen=4))
    trivia_categories_used: deque = field(default_factory=lambda: deque(maxlen=8))
    story_themes_used: deque = field(default_factory=lambda: deque(maxlen=8))
    catchphrases_used: dict = field(
        default_factory=lambda: {
            "pre_fact": deque(maxlen=4),
            "post_fact": deque(maxlen=4),
        }
    )
    pattern_history: deque = field(default_factory=lambda: deque(maxlen=6))
    agent_responses: deque = field(default_factory=lambda: deque(maxlen=8))

    # Anti-repetition deques (maxlen auto-evicts oldest)
    facts_told: deque = field(default_factory=lambda: deque(maxlen=25))
    riddles_told: deque = field(default_factory=lambda: deque(maxlen=15))

    def record_fact(self, summary: str):
        self.facts_told.append(summary)

    def record_riddle(self, summary: str):
        self.riddles_told.append(summary)

    def record_agent_response(self, text: str):
        """Record what the LLM actually said (first ~150 chars) for anti-repetition."""
        condensed = text.strip()[:150]
        if condensed:
            self.agent_responses.append(condensed)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎯 VARIETY ENGINE v4 — Motor parametrizable
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class VarietyEngine:
    """
    Motor de variedad y personalidad parametrizable para Nebu v4.

    Más que un anti-repetición: es el sistema nervioso del personaje.
    El contenido cultural viene del PersonalityProfile.

    Patches integrados:
    1. Persona Anchor — re-anclaje periódico de identidad
    2. Narrative Pattern Dedup — anti-repetición semántica
    3. Sliding Summary — compresión temporal con memoria de estilo
    4. Imperfecciones Orgánicas — humanizar al personaje
    5. FSM Mood Lite — transiciones reactivas al input del niño
    """

    # ── Profile (fuente de todo el contenido cultural) ────────────────
    profile: PersonalityProfile | None = field(default=None, repr=False)

    # ── Anti-repetición memory ──────────────────────────────────────────
    memory: MemoryTracker = field(default_factory=MemoryTracker)

    # ── Personalidad ────────────────────────────────────────────────────
    _mood_value: str = ""
    _mood_history: deque = field(default_factory=lambda: deque(maxlen=5))
    turn_count: int = 0
    _session_start: float = field(default_factory=time.time)

    # ── Topic chaining ──────────────────────────────────────────────────
    _last_category_label: str = ""
    _last_specific_topic: str = ""
    _topic_chain_count: int = 0

    # ── Engagement tracking ─────────────────────────────────────────────
    _consecutive_facts: int = 0
    _favorite_categories: dict = field(default_factory=dict)

    # ── Culture Hype ────────────────────────────────────────────────────
    culture_hype: float = 0.0

    # ── Patch 4: Imperfection tracking ──────────────────────────────────
    _last_imperfection: bool = False

    def __post_init__(self):
        if self.profile is None:
            from src.personalities import get_profile

            self.profile = get_profile()
        if not self._mood_value:
            self._mood_value = self.profile.default_mood
        if self.culture_hype == 0.0:
            self.culture_hype = self.profile.hype_initial

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎭 MOOD MANAGEMENT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def evolve_mood(self) -> str:
        """Evoluciona el mood con sesgo hacia hype_bias_mood cuando hay hype."""
        possible = self.profile.mood_transitions.get(
            self._mood_value, self.profile.get_mood_values()
        )
        if self._mood_history:
            possible = [m for m in possible if m != self._mood_history[-1]] or possible

        bias_mood = self.profile.hype_bias_mood
        if bias_mood and random.random() < self.culture_hype and bias_mood in possible:
            new_mood = bias_mood
        else:
            new_mood = random.choice(possible)

        self._mood_history.append(self._mood_value)
        self._mood_value = new_mood
        return new_mood

    def get_mood_instruction(self) -> str:
        return self.profile.get_mood_tone(self._mood_value)

    @property
    def rapport(self) -> dict:
        return self.profile.get_rapport_by_turns(self.turn_count)

    @property
    def rapport_value(self) -> str:
        return self.rapport.get("value", "")

    def get_rapport_instruction(self) -> str:
        return self.rapport.get("flavor", "")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PATCH 5: FSM Mood Lite — Transiciones reactivas
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def detect_child_signal(self, child_message: str) -> str:
        """Detectar señales del input del niño para adaptar mood."""
        msg = child_message.lower()
        if any(w in msg for w in ["no sé", "aburrido", "otra cosa", "ya"]):
            return "disengaged"
        if any(w in msg for w in ["más", "cuéntame", "y qué más", "sigue", "otro"]):
            return "hooked"
        if any(w in msg for w in ["por qué", "cómo", "pero"]):
            return "curious"
        if any(w in msg for w in ["jaja", "jeje", "gracioso", "chistoso"]):
            return "amused"
        if "?" in msg:
            return "questioning"
        return "neutral"

    def react_to_signal(self, signal: str):
        """Ajusta mood basado en la señal detectada del niño."""
        options = self.profile.signal_mood_map.get(signal)
        if options:
            self._mood_history.append(self._mood_value)
            self._mood_value = random.choice(options)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎤 CATCHPHRASES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def pick_catchphrase(self, kind: str) -> str:
        options = self.profile.catchphrases.get(kind, [])
        if not options:
            return ""
        if kind in self.memory.catchphrases_used:
            used = self.memory.catchphrases_used[kind]
            available = [c for c in options if c not in used]
            if not available:
                used.clear()
                available = options
            chosen = random.choice(available)
            used.append(chosen)
        else:
            chosen = random.choice(options)
        if "{prev_topic}" in chosen and self._last_category_label:
            chosen = chosen.replace("{prev_topic}", self._last_category_label)
        return chosen

    def check_milestone(self) -> str | None:
        milestones = self.profile.catchphrases.get("milestone", {})
        return milestones.get(self.turn_count)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎲 WILDCARDS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def roll_wildcard(self) -> str | None:
        if self.profile.wildcard_events and random.random() < WILDCARD_CHANCE:
            event = random.choice(self.profile.wildcard_events)
            return event["inject"]
        return None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🔗 TOPIC CHAINING + COMBOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _build_chain_prompt(self) -> str:
        if not self._last_category_label:
            return ""
        if random.random() > 0.30:
            return ""
        chain_phrase = self.pick_catchphrase("chaining")
        return (
            f"\n{self.profile.chain_label}: Conecta brevemente con el tema "
            f"anterior ({self._last_category_label}). Usa: "
            f"'{chain_phrase}' pero solo si la conexión es natural."
        )

    def _build_combo_text(self) -> str:
        self._consecutive_facts += 1
        if self._consecutive_facts >= 3:
            combo = self._consecutive_facts
            return (
                f"\n¡COMBO x{combo}! Llevan {combo} datos seguidos. "
                f"'¡Vamos por el dato número {combo}!' "
                f"o '¡{combo} seguidos, estamos en {self.profile.combo_flavor}!'"
            )
        return ""

    def reset_combo(self):
        self._consecutive_facts = 0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🧠 CULTURE BRAIN — Inyección cultural
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _build_culture_brain_injection(self, category_id: str) -> str:
        """Inyecta conexión cultural si toca."""
        if category_id in self.profile.hype_boost_categories:
            return ""

        if not self.profile.culture_connections:
            return ""

        chance = self.profile.culture_brain_chance + (self.culture_hype * 0.3)
        if random.random() > chance:
            return ""

        connection = random.choice(self.profile.culture_connections)
        if self.profile.bonus_facts:
            fact = random.choice(self.profile.bonus_facts)
            connection = connection.replace("{culture_fact}", fact)

        return f"\n🧠 CULTURE BRAIN: {connection}"

    def _maybe_culture_rant(self) -> str:
        if not self.profile.culture_rants:
            return ""
        if random.random() > self.profile.rant_chance:
            return ""
        return f"\n🎭 RANT (úsalo antes del dato): {random.choice(self.profile.culture_rants)}"

    def _maybe_slang(self) -> str:
        if not self.profile.slang_phrases:
            return ""
        if random.random() > self.profile.slang_chance:
            return ""
        return (
            f"\nJERGA: Mete un '{random.choice(self.profile.slang_phrases)}' natural "
            f"en tu respuesta."
        )

    def _maybe_knowledge(self, category_id: str) -> str:
        if self.profile.knowledge_injector is None:
            return ""
        return self.profile.knowledge_injector(category_id)

    def _evolve_hype(self, category_id: str):
        """Sube el hype cultural con el tiempo y con temas afines."""
        self.culture_hype = min(
            self.profile.hype_cap,
            self.culture_hype + self.profile.hype_growth,
        )
        if category_id in self.profile.hype_boost_categories:
            self.culture_hype = min(
                self.profile.hype_cap,
                self.culture_hype + self.profile.hype_boost_growth,
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📊 ENGAGEMENT TRACKING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _track_category(self, category_id: str):
        self._favorite_categories[category_id] = self._favorite_categories.get(category_id, 0) + 1

    @property
    def favorite_category(self) -> str | None:
        if not self._favorite_categories:
            return None
        max_cat = max(self._favorite_categories, key=self._favorite_categories.get)
        if self._favorite_categories[max_cat] >= 3:
            return max_cat
        return None

    def _build_favorite_hint(self) -> str:
        fav = self.favorite_category
        if not fav or random.random() > 0.2:
            return ""
        cat_label = next((c["label"] for c in self.profile.fact_categories if c["id"] == fav), fav)
        return (
            f"\nNOTA: Al niño le gustan los datos de {cat_label}. "
            f"Menciona algo como {self.profile.favorite_mention}"
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PATCH 1: Persona Anchor — Re-anclaje periódico
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def build_persona_anchor(self) -> str:
        """Cada 5 turnos, reinyectar identidad condensada."""
        if self.turn_count == 0 or self.turn_count % 5 != 0:
            return ""
        return self.profile.persona_anchor_template.format(
            hype_pct=int(self.culture_hype * 100),
            mood=self._mood_value,
            rapport=self.rapport_value,
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PATCH 2: Narrative Pattern Dedup
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _pick_narrative_pattern(self) -> str:
        """Elige un patrón narrativo no usado recientemente."""
        patterns = self.profile.narrative_patterns
        if not patterns:
            return ""
        return self._pick_unique(patterns, self.memory.pattern_history)

    def _build_pattern_instruction(self) -> str:
        """Genera instrucción de patrón narrativo para variedad semántica."""
        pattern = self._pick_narrative_pattern()
        if not pattern:
            return ""
        instruction = self.profile.pattern_instructions.get(pattern, "Cuéntalo de forma original.")
        return f"\nPATRÓN NARRATIVO (varía la forma): {instruction}"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PATCH 3: Sliding Summary
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def build_sliding_summary(self) -> str:
        """Cada 10 turnos, comprimir el historial en un resumen."""
        if self.turn_count < 10 or self.turn_count % 10 != 0:
            return ""
        recent_cats = list(self.memory.fact_categories_used)[-5:]
        recent_patterns = list(self.memory.pattern_history)[-5:]
        engagement = "enganchado" if self._consecutive_facts > 2 else "explorando"
        return (
            f"\n[RESUMEN turnos {self.turn_count - 10}-{self.turn_count}]: "
            f"Temas cubiertos: {', '.join(recent_cats)}. "
            f"Patrones usados: {', '.join(recent_patterns)}. "
            f"El niño parece {engagement}. Mood: {self._mood_value}. "
            f"VARIAR: usar categorías y patrones DIFERENTES a los del resumen."
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PATCH 4: Imperfecciones Orgánicas
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _maybe_imperfection(self) -> str:
        """Chance de imperfección deliberada, nunca dos seguidas."""
        if not self.profile.imperfections:
            return ""
        if self._last_imperfection:
            self._last_imperfection = False
            return ""
        if random.random() > IMPERFECTION_CHANCE:
            self._last_imperfection = False
            return ""
        self._last_imperfection = True
        return f"\nIMPERFECCIÓN (hazla natural): '{random.choice(self.profile.imperfections)}'"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🌙 TIME-AWARE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_time_flavor(self, hour: int | None = None) -> str:
        if hour is None:
            hour = time.localtime().tm_hour
        flavors = self.profile.time_flavors
        if 6 <= hour < 12:
            return flavors.get("morning", "")
        elif 12 <= hour < 18:
            return flavors.get("afternoon", "")
        elif 18 <= hour < 21:
            return flavors.get("evening", "")
        else:
            return flavors.get("late_night", "")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📚 FACTS — El plato fuerte
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _pick_unique(self, options: list, used: deque):
        """Elige un elemento de options evitando repetir los de used."""
        available = [x for x in options if x not in used]
        if not available:
            used.clear()
            available = options
        chosen = random.choice(available)
        used.append(chosen)
        return chosen

    def pick_fact_category(self) -> dict:
        categories = self.profile.fact_categories
        available = [c for c in categories if c["id"] not in self.memory.fact_categories_used]
        if not available:
            self.memory.fact_categories_used.clear()
            available = categories
        chosen = random.choice(available)
        self.memory.fact_categories_used.append(chosen["id"])
        self._track_category(chosen["id"])
        return chosen

    def pick_delivery_style(self) -> str:
        return self._pick_unique(self.profile.delivery_styles, self.memory.styles_used)

    def record_fact(self, summary: str):
        self.memory.record_fact(summary)

    def record_agent_response(self, text: str):
        self.memory.record_agent_response(text)

    def _pick_specific_topic(self, category_id: str) -> str:
        specific_options = self.profile.category_specifics.get(category_id, [])
        if not specific_options:
            return ""
        used_in_cat = [s for s in self.memory.facts_told if f"[{category_id}]" in s]
        available = [
            s for s in specific_options if not any(s.lower() in u.lower() for u in used_in_cat)
        ]
        if not available:
            available = specific_options
        return random.choice(available)

    def build_fact_prompt(self, topic: str = "", hour: int | None = None) -> str:
        """
        Construye el prompt completo para generar un dato curioso.
        v4: Parametrizable + patches + personalidad configurable.
        """
        category = self.pick_fact_category()
        style = self.pick_delivery_style()
        specific = self._pick_specific_topic(category["id"])

        # Evolucionar mood cada 3-4 turnos
        if self.turn_count > 0 and self.turn_count % random.randint(3, 4) == 0:
            self.evolve_mood()

        # Evolucionar hype
        self._evolve_hype(category["id"])

        lines = []

        # PATCH 1: Persona Anchor
        anchor = self.build_persona_anchor()
        if anchor:
            lines.append(anchor)
            lines.append("")

        # PATCH 3: Sliding Summary
        summary = self.build_sliding_summary()
        if summary:
            lines.append(summary)
            lines.append("")

        # 1) Personalidad base
        lines.append("═══ PERSONALIDAD DE NEBU ═══")
        lines.append(self.get_mood_instruction())
        lines.append(self.get_rapport_instruction())
        lines.append(self.get_time_flavor(hour))
        lines.append("")

        # PATCH 4: Imperfección orgánica
        imperfection = self._maybe_imperfection()
        if imperfection:
            lines.append(imperfection)

        # 2) Catchphrase + jerga
        pre = self.pick_catchphrase("pre_fact")
        if pre:
            lines.append(f"FRASE DE APERTURA (úsala o adáptala): {pre}")
        slang = self._maybe_slang()
        if slang:
            lines.append(slang)
        lines.append("")

        # PATCH 2: Narrative Pattern Dedup
        lines.append(self._build_pattern_instruction())

        # 3) El dato en sí
        lines.append("")
        lines.append("═══ DATO CURIOSO ═══")
        if topic:
            lines.append(f"Tema pedido por el niño: {topic}")
            lines.append("Cuenta un dato REAL y poco conocido sobre este tema.")
            lines.append(f"Estilo de entrega: {style}")
        else:
            lines.append(
                f"Categoría: {category['label']} {category['emoji']} "
                f"— {category.get('nebu_intro', '')}"
            )
            culture_angle = category.get("culture_angle", "")
            if culture_angle:
                lines.append(f"{self.profile.culture_angle_label}: {culture_angle}")
            if specific:
                lines.append(f"Tema específico: cuenta algo sobre {specific}")
                lines.append("Busca un dato REAL, VERIFICABLE y que suene casi inventado.")
            else:
                lines.append(f"Pista: {category['hint']}")
            lines.append(f"Estilo de entrega: {style}")
        lines.append("")

        # 4) Culture Brain injection
        culture_brain = self._build_culture_brain_injection(category["id"])
        if culture_brain:
            lines.append(culture_brain)

        # Culture rant
        rant = self._maybe_culture_rant()
        if rant:
            lines.append(rant)

        # Knowledge injection
        knowledge = self._maybe_knowledge(category["id"])
        if knowledge:
            lines.append(knowledge)

        # 5) Wildcard
        wildcard = self.roll_wildcard()
        if wildcard:
            lines.append(f"\n🎲 {wildcard}")

        # 6) Topic chaining
        chain = self._build_chain_prompt()
        if chain:
            lines.append(chain)

        # 7) Combo tracker
        combo = self._build_combo_text()
        if combo:
            lines.append(combo)

        # 8) Favorite hint
        fav_hint = self._build_favorite_hint()
        if fav_hint:
            lines.append(fav_hint)

        # 9) Milestone check
        milestone = self.check_milestone()
        if milestone:
            lines.append(f"\n🏆 CELEBRACIÓN: {milestone}")

        # 10) Datos PROHIBIDOS
        all_banned = BANNED_FACTS + self.profile.extra_banned_facts
        lines.append("")
        lines.append("═══ 🚫 DATOS PROHIBIDOS — NUNCA digas estos ═══")
        lines.append("Estos datos están SUPER quemados. JAMÁS los uses:")
        for banned in all_banned:
            lines.append(f"  ✗ {banned}")

        # 11) Historial anti-repetición
        if self.memory.facts_told:
            lines.append("")
            lines.append("═══ NO REPETIR — DATOS YA CONTADOS EN ESTA SESIÓN ═══")
            for i, fact in enumerate(list(self.memory.facts_told)[-12:], 1):
                lines.append(f"  {i}. {fact}")

        # 11b) Feedback loop: lo que realmente dijiste
        if self.memory.agent_responses:
            lines.append("")
            lines.append("═══ LO QUE YA DIJISTE TEXTUALMENTE (no repitas) ═══")
            for i, resp in enumerate(self.memory.agent_responses, 1):
                lines.append(f'  {i}. "{resp}"')

        # 12) Reglas finales
        lines.append("")
        lines.append("═══ REGLAS ESTRICTAS ═══")
        lines.append("• PROHIBIDO repetir los datos de la lista prohibida.")
        lines.append("• NO repitas NADA ya contado en esta sesión.")
        lines.append("• Cuenta algo que un niño JAMÁS haya escuchado.")
        lines.append("• Nada de chistes sobre redes sociales.")
        lines.append("• Datos REALES, VERIFICABLES y ASOMBROSOS.")
        lines.append("• Máximo 2-3 oraciones para el dato.")
        lines.append(f"• Habla como Nebu: {self.profile.personality_label}.")
        lines.append(f"• Usa lenguaje simple pero con {self.profile.flavor_label}.")

        # Registrar para tracking
        self.memory.record_fact(f"[{category['id']}] sobre {specific or category['label']}")
        self._last_category_label = category["label"]
        self._last_specific_topic = specific

        return "\n".join(lines)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🧩 TRIVIA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def pick_trivia_category(self) -> str:
        return self._pick_unique(self.profile.trivia_categories, self.memory.trivia_categories_used)

    def build_trivia_prompt(self) -> str:
        category = self.pick_trivia_category()
        lines = [
            "═══ PERSONALIDAD ═══",
            self.get_mood_instruction(),
            self.get_rapport_instruction(),
            "",
            "═══ TRIVIA ═══",
            f"Categoría: {category}",
            "",
            "Genera UNA pregunta de trivia con 3 opciones (A, B, C).",
            "La pregunta debe ser interesante y para niños (6-10 años).",
            "Nebu debe sonar entusiasmado al plantear el desafío.",
        ]
        if self.profile.trivia_culture_hint:
            lines.append(self.profile.trivia_culture_hint)
        return "\n".join(lines)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📖 CUENTOS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def pick_story_theme(self) -> str:
        return self._pick_unique(self.profile.story_themes, self.memory.story_themes_used)

    def build_story_prompt(self, custom_theme: str = "") -> str:
        theme = custom_theme or self.pick_story_theme()
        if self.profile.story_moods:
            self._mood_value = random.choice(self.profile.story_moods)

        lines = [
            "═══ PERSONALIDAD ═══",
            self.get_mood_instruction(),
            self.get_rapport_instruction(),
            self.get_time_flavor(),
            "",
            "═══ CUENTO ═══",
            f"Tema: {theme}",
            "",
            "Cuenta un cuento corto (8-12 oraciones) sobre este tema.",
            "El cuento debe tener:",
            "• Un inicio que enganche",
            "• Un problema o aventura en el medio",
            "• Un final feliz o sorprendente",
            "• Un mensaje positivo sutil",
        ]
        if self.profile.story_culture_hint:
            lines.append(f"• {self.profile.story_culture_hint}")
        lines.append("")
        lines.append("Nebu es el narrador. Puede meter comentarios entre la historia.")

        if self.memory.story_themes_used:
            lines.append("")
            lines.append("TEMAS YA USADOS (cuenta algo diferente):")
            for t in list(self.memory.story_themes_used)[-5:]:
                lines.append(f"  - {t}")

        return "\n".join(lines)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🤔 ADIVINANZAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def record_riddle(self, summary: str):
        self.memory.record_riddle(summary)

    def build_riddle_prompt(self) -> str:
        if self.profile.riddle_moods:
            self._mood_value = random.choice(self.profile.riddle_moods)
        lines = [
            "═══ PERSONALIDAD ═══",
            self.get_mood_instruction(),
            self.get_rapport_instruction(),
            "",
            "═══ ADIVINANZA ═══",
            "Inventa una adivinanza original, divertida y para niños.",
        ]
        if self.profile.riddle_culture_hint:
            lines.append(self.profile.riddle_culture_hint)
        lines.append("")
        lines.append(f"Nebu la presenta con entusiasmo: {self.profile.riddle_challenge}")
        if self.memory.riddles_told:
            lines.append("")
            lines.append("ADIVINANZAS YA CONTADAS (inventa algo diferente):")
            for i, r in enumerate(list(self.memory.riddles_told)[-8:], 1):
                lines.append(f"  {i}. {r}")
        return "\n".join(lines)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🛠️ UTILIDADES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def last_fact_category(self) -> str:
        return (
            self.memory.fact_categories_used[-1] if self.memory.fact_categories_used else "general"
        )

    @property
    def session_minutes(self) -> float:
        return (time.time() - self._session_start) / 60

    def tick(self):
        self.turn_count += 1

    def get_session_stats(self) -> dict:
        return {
            "turns": self.turn_count,
            "mood": self._mood_value,
            "rapport": self.rapport_value,
            "facts_told": len(self.memory.facts_told),
            "riddles_told": len(self.memory.riddles_told),
            "favorite_category": self.favorite_category,
            "session_minutes": round(self.session_minutes, 1),
            "consecutive_facts": self._consecutive_facts,
            "culture_hype": round(self.culture_hype, 2),
            "profile": self.profile.id,
        }

    def debug_status(self) -> str:
        stats = self.get_session_stats()
        return (
            f"🎭 Nebu Status ({self.profile.debug_version_label})\n"
            f"├─ Profile: {self.profile.id}\n"
            f"├─ Mood: {self._mood_value}\n"
            f"├─ Rapport: {self.rapport_value}\n"
            f"├─ Turnos: {stats['turns']}\n"
            f"├─ Facts contados: {stats['facts_told']}\n"
            f"├─ Combo actual: x{stats['consecutive_facts']}\n"
            f"├─ {self.profile.hype_field_name}: {stats['culture_hype']}\n"
            f"├─ Cat favorita: {stats['favorite_category'] or '(aún no)'}\n"
            f"└─ Sesión: {stats['session_minutes']} min"
        )
