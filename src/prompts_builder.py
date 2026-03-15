"""
prompts_builder.py — Construcción de prompts para facts, trivia, stories y riddles.

Extraído de VarietyEngine para aislar la lógica de composición de prompts
del motor de estado (mood, memory, hype).

Cada función recibe el engine como parámetro y compone el prompt final
usando su API pública.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.prompt_flavor import (
    build_culture_injection,
    maybe_culture_rant,
    maybe_knowledge,
    maybe_slang,
)
from src.prompts import BANNED_FACTS

if TYPE_CHECKING:
    from src.variety import VarietyEngine


def build_fact_prompt(
    engine: VarietyEngine,
    ctx: dict,
    hour: int | None = None,
) -> str:
    """
    Render the fact prompt from pre-computed context.
    All state mutation happens in VarietyEngine.prepare_fact_turn().
    """
    category = ctx["category"]
    style = ctx["style"]
    specific = ctx["specific"]
    topic = ctx["topic"]

    lines = []

    # PATCH 1: Persona Anchor
    anchor = engine.build_persona_anchor()
    if anchor:
        lines.append(anchor)

    # PATCH 3: Sliding Summary
    summary = engine.build_sliding_summary()
    if summary:
        lines.append(summary)

    # 1) Personalidad base
    lines.append("## PERSONALIDAD")
    lines.append(engine.get_mood_instruction())
    lines.append(engine.get_rapport_instruction())
    lines.append(engine.get_time_flavor(hour))

    # PATCH 4: Imperfección orgánica
    imperfection = engine._maybe_imperfection()
    if imperfection:
        lines.append(imperfection)

    # 2) Catchphrase + jerga
    pre = engine.pick_catchphrase("pre_fact")
    if pre:
        lines.append(f"APERTURA: {pre}")
    slang = maybe_slang(engine.profile)
    if slang:
        lines.append(slang)

    # PATCH 2: Narrative Pattern Dedup
    lines.append(engine._build_pattern_instruction())

    # 3) El dato en sí
    lines.append("## DATO CURIOSO")
    if topic:
        lines.append(f"Tema pedido por el niño: {topic}")
        lines.append("Cuenta un dato REAL y poco conocido sobre este tema.")
        lines.append(f"Estilo de entrega: {style}")
    else:
        lines.append(
            f"Categoría: {category['label']} {category['emoji']} — {category.get('nebu_intro', '')}"
        )
        culture_angle = category.get("culture_angle", "")
        if culture_angle:
            lines.append(f"{engine.profile.culture_angle_label}: {culture_angle}")
        if specific:
            lines.append(f"Tema específico: cuenta algo sobre {specific}")
            lines.append("Busca un dato REAL, VERIFICABLE y que suene casi inventado.")
        else:
            lines.append(f"Pista: {category['hint']}")
        lines.append(f"Estilo de entrega: {style}")

    # 4) Culture Brain injection
    culture_brain = build_culture_injection(engine.profile, engine.culture_hype, category["id"])
    if culture_brain:
        lines.append(culture_brain)

    # Culture rant
    rant = maybe_culture_rant(engine.profile)
    if rant:
        lines.append(rant)

    # Knowledge injection
    knowledge = maybe_knowledge(engine.profile, category["id"])
    if knowledge:
        lines.append(knowledge)

    # 5) Wildcard
    wildcard = engine.roll_wildcard()
    if wildcard:
        lines.append(f"\n🎲 {wildcard}")

    # 6) Topic chaining
    chain = engine._build_chain_prompt()
    if chain:
        lines.append(chain)

    # 7) Combo tracker
    combo = engine._build_combo_text()
    if combo:
        lines.append(combo)

    # 8) Favorite hint
    fav_hint = engine._build_favorite_hint()
    if fav_hint:
        lines.append(fav_hint)

    # 9) Milestone check
    milestone = engine.check_milestone()
    if milestone:
        lines.append(f"\n🏆 CELEBRACIÓN: {milestone}")

    # 10) Datos PROHIBIDOS
    all_banned = BANNED_FACTS + engine.profile.extra_banned_facts
    lines.append("")
    lines.append("## PROHIBIDOS (datos quemados, JAMÁS usarlos)")
    lines.append(", ".join(all_banned))

    # 11) Historial anti-repetición
    if engine.memory.facts_told:
        lines.append("")
        lines.append("## NO REPETIR (ya contados)")
        lines.append(", ".join(list(engine.memory.facts_told)[-8:]))

    # 11b) Feedback loop: lo que realmente dijiste
    if engine.memory.agent_responses:
        lines.append("")
        lines.append("## YA DIJISTE (no repitas)")
        lines.append(" | ".join(f'"{r}"' for r in engine.memory.agent_responses))

    # 12) Reglas finales
    lines.append("")
    lines.append(
        f"## REGLAS: Dato REAL, VERIFICABLE, máx 2-3 oraciones. "
        f"NUNCA repitas prohibidos ni ya contados. Sin chistes de redes sociales. "
        f"Habla como {engine.agent_name}: {engine.profile.personality_label}, "
        f"lenguaje simple con {engine.profile.flavor_label}."
    )

    return "\n".join(lines)


def build_trivia_prompt(engine: VarietyEngine) -> str:
    category = engine.pick_trivia_category()
    lines = [
        "## PERSONALIDAD",
        engine.get_mood_instruction(),
        engine.get_rapport_instruction(),
        f"## TRIVIA — {category}",
        "UNA pregunta con 3 opciones (A/B/C), interesante, para niños (6-10 años).",
        f"{engine.agent_name} suena entusiasmado al plantear el desafío.",
    ]
    if engine.profile.trivia_culture_hint:
        lines.append(engine.profile.trivia_culture_hint)
    return "\n".join(lines)


def build_story_prompt(engine: VarietyEngine, ctx: dict) -> str:
    """Render story prompt. State mutation in VarietyEngine.prepare_story_turn()."""
    theme = ctx["theme"]

    lines = [
        "## PERSONALIDAD",
        engine.get_mood_instruction(),
        engine.get_rapport_instruction(),
        engine.get_time_flavor(),
        f"## CUENTO — Tema: {theme}",
        "Cuento corto (8-12 oraciones): inicio que enganche, problema/aventura, final sorprendente, mensaje positivo sutil.",
    ]
    if engine.profile.story_culture_hint:
        lines.append(engine.profile.story_culture_hint)
    lines.append(f"{engine.agent_name} narra y puede meter comentarios.")

    if engine.memory.story_themes_used:
        lines.append("Temas ya usados: " + ", ".join(list(engine.memory.story_themes_used)[-5:]))

    return "\n".join(lines)


def build_riddle_prompt(engine: VarietyEngine) -> str:
    """Render riddle prompt. State mutation in VarietyEngine.prepare_riddle_turn()."""
    lines = [
        "## PERSONALIDAD",
        engine.get_mood_instruction(),
        engine.get_rapport_instruction(),
        "## ADIVINANZA",
        "Inventa una adivinanza original, divertida, para niños.",
    ]
    if engine.profile.riddle_culture_hint:
        lines.append(engine.profile.riddle_culture_hint)
    lines.append(
        f"{engine.agent_name} la presenta con entusiasmo: {engine.profile.riddle_challenge}"
    )
    if engine.memory.riddles_told:
        lines.append("Ya contadas: " + ", ".join(list(engine.memory.riddles_told)[-6:]))
    return "\n".join(lines)
