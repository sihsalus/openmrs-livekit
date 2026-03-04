"""
PersonalityProfile — Contrato de datos para personalidades del VarietyEngine.

Cada personalidad (peruana, mexicana, k-pop, roblox, etc.) es una instancia
de PersonalityProfile con todo el contenido cultural parametrizado.
El engine (variety.py) lee de self.profile en vez de constantes hardcodeadas.
"""

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class PersonalityProfile:
    """Todos los datos culturales para una personalidad del VarietyEngine."""

    # ── Identidad ───────────────────────────────────────────────────────
    id: str                           # "peruvian", "mexican", "kpop", "roblox"
    display_name: str                 # "Nebu Etnocacerista"
    description: str                  # Una línea descriptiva

    # ── Moods ───────────────────────────────────────────────────────────
    # Lista de dicts: {"name": "MODO_INCA", "value": "modo_inca", "tone": "..."}
    moods: list[dict] = field(default_factory=list)
    default_mood: str = "curioso"     # valor del mood inicial
    mood_transitions: dict[str, list[str]] = field(default_factory=dict)

    # ── Rapport ─────────────────────────────────────────────────────────
    # Lista de dicts: {"name": "CHASQUI", "value": "chasqui", "threshold": 0, "flavor": "..."}
    rapport_levels: list[dict] = field(default_factory=list)

    # ── Culture Brain ───────────────────────────────────────────────────
    culture_brain_chance: float = 0.20
    culture_connections: list[str] = field(default_factory=list)
    bonus_facts: list[str] = field(default_factory=list)
    culture_rants: list[str] = field(default_factory=list)
    slang_phrases: list[str] = field(default_factory=list)

    # ── Catchphrases ────────────────────────────────────────────────────
    # Misma estructura: {"pre_fact": [...], "post_fact": [...], "chaining": [...],
    #  "wildcard": [...], "milestone": {5: "...", 10: "...", ...}}
    catchphrases: dict = field(default_factory=dict)

    # ── Categorías de datos ─────────────────────────────────────────────
    fact_categories: list[dict] = field(default_factory=list)
    category_specifics: dict[str, list[str]] = field(default_factory=dict)

    # ── Delivery & Narrative ────────────────────────────────────────────
    delivery_styles: list[str] = field(default_factory=list)
    narrative_patterns: list[str] = field(default_factory=list)
    pattern_instructions: dict[str, str] = field(default_factory=dict)
    imperfections: list[str] = field(default_factory=list)

    # ── Content ─────────────────────────────────────────────────────────
    trivia_categories: list[str] = field(default_factory=list)
    story_themes: list[str] = field(default_factory=list)
    wildcard_events: list[dict] = field(default_factory=list)

    # ── Time flavors ────────────────────────────────────────────────────
    # {"morning": "...", "afternoon": "...", "evening": "...", "late_night": "..."}
    time_flavors: dict[str, str] = field(default_factory=dict)

    # ── Persona anchor ──────────────────────────────────────────────────
    # Template con placeholders: {hype_pct}, {mood}, {rapport}
    persona_anchor_template: str = ""

    # ── Hype system ─────────────────────────────────────────────────────
    hype_field_name: str = "Culture Hype"
    hype_initial: float = 0.10
    hype_cap: float = 0.70
    hype_growth: float = 0.01
    hype_boost_growth: float = 0.03
    hype_boost_categories: list[str] = field(default_factory=list)
    hype_bias_mood: str | None = None  # mood value to bias toward when hype is high

    # ── Chances ─────────────────────────────────────────────────────────
    rant_chance: float = 0.08
    slang_chance: float = 0.25
    knowledge_injector: Callable[[str], str] | None = field(default=None, repr=False)

    # ── FSM signal-to-mood mapping ──────────────────────────────────────
    # señal -> [mood values] o None (mantener actual)
    signal_mood_map: dict[str, list[str] | None] = field(default_factory=dict)

    # ── Story/Riddle mood preferences ───────────────────────────────────
    story_moods: list[str] = field(default_factory=list)
    riddle_moods: list[str] = field(default_factory=list)

    # ── Labels para prompts ─────────────────────────────────────────────
    culture_angle_label: str = "ÁNGULO CULTURAL"
    chain_label: str = "CONEXIÓN TEMÁTICA"
    combo_flavor: str = "racha increíble"
    favorite_mention: str = "'¡Ya vi que te encantan!'"
    personality_label: str = "peluche divertido, cálido, juguetón"
    flavor_label: str = "sabor único"

    # ── Trivia/Story/Riddle prompt extras ───────────────────────────────
    trivia_culture_hint: str = ""     # "Si puedes incluir algo de Perú, ¡mejor!"
    story_culture_hint: str = ""      # "Ambiente andino/peruano si el tema lo permite"
    riddle_culture_hint: str = ""     # "Dale un toque peruano/andino"
    riddle_challenge: str = "'¡A ver si me ganas esta!'"

    # ── Extra banned facts ──────────────────────────────────────────────
    extra_banned_facts: list[str] = field(default_factory=list)

    # ── Debug ───────────────────────────────────────────────────────────
    debug_version_label: str = "v4 Parametrizable"

    # ── Helpers ──────────────────────────────────────────────────────────

    def get_mood_tone(self, mood_value: str) -> str:
        """Look up tone instruction for a mood value."""
        for m in self.moods:
            if m["value"] == mood_value:
                return m["tone"]
        return ""

    def get_mood_values(self) -> list[str]:
        """Return all mood value strings."""
        return [m["value"] for m in self.moods]

    def get_rapport_by_turns(self, turns: int) -> dict:
        """Get the rapport level dict for a given turn count."""
        result = self.rapport_levels[0] if self.rapport_levels else {}
        for level in self.rapport_levels:
            if turns >= level["threshold"]:
                result = level
        return result
