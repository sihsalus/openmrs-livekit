"""
Variety Engine v4 — Sistema de personalidad parametrizable.

Motor anti-repetición con personalidad configurable.
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
from src.prompt_flavor import evolve_hype
from src.prompts_builder import (
    build_fact_prompt,
    build_riddle_prompt,
    build_story_prompt,
    build_trivia_prompt,
)

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
    - fact_categories_used  maxlen=10: ~2 rotaciones completas
    - styles_used           maxlen=4:  fuerza alternancia
    - trivia_categories_used maxlen=8: cubre mayoría antes de reciclar
    - story_themes_used     maxlen=8:  ídem trivia
    - catchphrases_used     maxlen=4:  por slot (pre/post)
    - pattern_history       maxlen=6:  arquetipos narrativos
    - agent_responses       maxlen=5:  output real del LLM (~80 chars c/u)

    Deques con maxlen fijo:
    - facts_told    maxlen=15:  balance costo de contexto LLM vs. cobertura
    - riddles_told  maxlen=10:  ventana suficiente para adivinanzas
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
    agent_responses: deque = field(default_factory=lambda: deque(maxlen=5))

    # Anti-repetition deques (maxlen auto-evicts oldest)
    facts_told: deque = field(default_factory=lambda: deque(maxlen=15))
    riddles_told: deque = field(default_factory=lambda: deque(maxlen=10))

    def record_fact(self, summary: str):
        self.facts_told.append(summary)

    def record_riddle(self, summary: str):
        self.riddles_told.append(summary)

    def record_agent_response(self, text: str):
        """Record what the LLM actually said (first ~80 chars) for anti-repetition."""
        condensed = text.strip()[:80]
        if condensed:
            self.agent_responses.append(condensed)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎯 VARIETY ENGINE v4 — Motor parametrizable
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class VarietyEngine:
    """
    Motor de variedad y personalidad parametrizable v4.

    Más que un anti-repetición: es el sistema nervioso del personaje.
    El contenido cultural viene del PersonalityProfile.

    Prompts delegados a src.prompts_builder.
    Lógica cultural delegada a src.culture.

    Patches integrados:
    1. Persona Anchor — re-anclaje periódico de identidad
    2. Narrative Pattern Dedup — anti-repetición semántica
    3. Sliding Summary — compresión temporal con memoria de estilo
    4. Imperfecciones Orgánicas — humanizar al personaje
    5. FSM Mood Lite — transiciones reactivas al input del niño
    """

    # ── Profile (fuente de todo el contenido cultural) ────────────────
    profile: PersonalityProfile | None = field(default=None, repr=False)
    agent_name: str = "Nebu"

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
        """Detect child engagement signals to adapt mood.

        Uses prefix matching with word boundaries to catch conjugations
        (e.g. "aburr" matches "aburrido", "aburrí", "aburrida").
        """
        msg = f" {child_message.lower()} "  # pad for boundary matching

        def _has(phrases):
            """Check if any phrase appears with left word boundary."""
            return any(f" {w}" in msg for w in phrases)

        # Order matters: more specific patterns first
        if _has(["no sé", "aburr", "otra cosa", "ya no", "ya me", "ya basta"]):
            return "disengaged"
        if _has(["cuéntame", "y qué más", "sigue", "otro más"]) or " más " in msg:
            return "hooked"
        if _has(["por qué", "cómo funciona", "cómo es"]):
            return "curious"
        if _has(["jaja", "jeje", "gracioso", "chistoso", "qué risa"]):
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
    # 📚 FACTS + CONTENT SELECTION
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
        # Build set of already-used topics for this category (exact match)
        prefix = f"[{category_id}] sobre "
        used_topics = {
            s[len(prefix):].lower() for s in self.memory.facts_told if s.startswith(prefix)
        }
        available = [s for s in specific_options if s.lower() not in used_topics]
        if not available:
            available = specific_options
        return random.choice(available)

    def pick_trivia_category(self) -> str:
        return self._pick_unique(self.profile.trivia_categories, self.memory.trivia_categories_used)

    def pick_story_theme(self) -> str:
        return self._pick_unique(self.profile.story_themes, self.memory.story_themes_used)

    def record_riddle(self, summary: str):
        self.memory.record_riddle(summary)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📝 PROMPT BUILDERS — delegados a src.prompts_builder
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def prepare_fact_turn(self, topic: str = "") -> dict:
        """Mutate engine state for a fact turn. Returns context dict for rendering."""
        category = self.pick_fact_category()
        style = self.pick_delivery_style()
        specific = self._pick_specific_topic(category["id"])

        if self.turn_count > 0 and self.turn_count % random.randint(3, 4) == 0:
            self.evolve_mood()

        self.culture_hype = evolve_hype(self.culture_hype, self.profile, category["id"])

        self.memory.record_fact(f"[{category['id']}] sobre {specific or category['label']}")
        self._last_category_label = category["label"]
        self._last_specific_topic = specific

        return {"category": category, "style": style, "specific": specific, "topic": topic}

    def prepare_story_turn(self, custom_theme: str = "") -> dict:
        """Mutate engine state for a story turn. Returns context dict."""
        theme = custom_theme or self.pick_story_theme()
        if self.profile.story_moods:
            self._mood_value = random.choice(self.profile.story_moods)
        return {"theme": theme}

    def prepare_riddle_turn(self) -> dict:
        """Mutate engine state for a riddle turn. Returns context dict."""
        if self.profile.riddle_moods:
            self._mood_value = random.choice(self.profile.riddle_moods)
        return {}

    def build_fact_prompt(self, topic: str = "", hour: int | None = None) -> str:
        ctx = self.prepare_fact_turn(topic)
        return build_fact_prompt(self, ctx, hour)

    def build_trivia_prompt(self) -> str:
        return build_trivia_prompt(self)

    def build_story_prompt(self, custom_theme: str = "") -> str:
        ctx = self.prepare_story_turn(custom_theme)
        return build_story_prompt(self, ctx)

    def build_riddle_prompt(self) -> str:
        self.prepare_riddle_turn()
        return build_riddle_prompt(self)

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
            "turnCount": self.turn_count,
            "mood": self._mood_value,
            "rapport": self.rapport_value,
            "factsTold": len(self.memory.facts_told),
            "riddlesTold": len(self.memory.riddles_told),
            "favoriteCategory": self.favorite_category,
            "sessionMinutes": round(self.session_minutes, 2),
            "consecutiveFacts": self._consecutive_facts,
            "cultureHype": round(self.culture_hype, 2),
            "profileId": self.profile.id,
        }
