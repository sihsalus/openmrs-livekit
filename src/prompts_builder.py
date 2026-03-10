"""
prompts_builder.py — Construcción de prompts para facts, trivia, stories y riddles.

Extraído de VarietyEngine para aislar la lógica de composición de prompts
del motor de estado (mood, memory, hype).

Cada función recibe el engine como parámetro y compone el prompt final
usando su API pública.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.culture import (
    build_culture_injection,
    evolve_hype,
    maybe_culture_rant,
    maybe_knowledge,
    maybe_slang,
)
from src.variety import BANNED_FACTS

if TYPE_CHECKING:
    from src.variety import VarietyEngine


def build_fact_prompt(
    engine: VarietyEngine,
    topic: str = "",
    hour: int | None = None,
) -> str:
    """
    Construye el prompt completo para generar un dato curioso.
    v4: Parametrizable + patches + personalidad configurable.
    """
    category = engine.pick_fact_category()
    style = engine.pick_delivery_style()
    specific = engine._pick_specific_topic(category["id"])

    # Evolucionar mood cada 3-4 turnos
    if engine.turn_count > 0 and engine.turn_count % random.randint(3, 4) == 0:
        engine.evolve_mood()

    # Evolucionar hype
    engine.culture_hype = evolve_hype(
        engine.culture_hype, engine.profile, category["id"]
    )

    lines = []

    # PATCH 1: Persona Anchor
    anchor = engine.build_persona_anchor()
    if anchor:
        lines.append(anchor)
        lines.append("")

    # PATCH 3: Sliding Summary
    summary = engine.build_sliding_summary()
    if summary:
        lines.append(summary)
        lines.append("")

    # 1) Personalidad base
    lines.append("═══ PERSONALIDAD DE NEBU ═══")
    lines.append(engine.get_mood_instruction())
    lines.append(engine.get_rapport_instruction())
    lines.append(engine.get_time_flavor(hour))
    lines.append("")

    # PATCH 4: Imperfección orgánica
    imperfection = engine._maybe_imperfection()
    if imperfection:
        lines.append(imperfection)

    # 2) Catchphrase + jerga
    pre = engine.pick_catchphrase("pre_fact")
    if pre:
        lines.append(f"FRASE DE APERTURA (úsala o adáptala): {pre}")
    slang = maybe_slang(engine.profile)
    if slang:
        lines.append(slang)
    lines.append("")

    # PATCH 2: Narrative Pattern Dedup
    lines.append(engine._build_pattern_instruction())

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
            lines.append(f"{engine.profile.culture_angle_label}: {culture_angle}")
        if specific:
            lines.append(f"Tema específico: cuenta algo sobre {specific}")
            lines.append("Busca un dato REAL, VERIFICABLE y que suene casi inventado.")
        else:
            lines.append(f"Pista: {category['hint']}")
        lines.append(f"Estilo de entrega: {style}")
    lines.append("")

    # 4) Culture Brain injection
    culture_brain = build_culture_injection(
        engine.profile, engine.culture_hype, category["id"]
    )
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
    lines.append("═══ 🚫 DATOS PROHIBIDOS — NUNCA digas estos ═══")
    lines.append("Estos datos están SUPER quemados. JAMÁS los uses:")
    for banned in all_banned:
        lines.append(f"  ✗ {banned}")

    # 11) Historial anti-repetición
    if engine.memory.facts_told:
        lines.append("")
        lines.append("═══ NO REPETIR — DATOS YA CONTADOS EN ESTA SESIÓN ═══")
        for i, fact in enumerate(list(engine.memory.facts_told)[-12:], 1):
            lines.append(f"  {i}. {fact}")

    # 11b) Feedback loop: lo que realmente dijiste
    if engine.memory.agent_responses:
        lines.append("")
        lines.append("═══ LO QUE YA DIJISTE TEXTUALMENTE (no repitas) ═══")
        for i, resp in enumerate(engine.memory.agent_responses, 1):
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
    lines.append(f"• Habla como {engine.agent_name}: {engine.profile.personality_label}.")
    lines.append(f"• Usa lenguaje simple pero con {engine.profile.flavor_label}.")

    # Registrar para tracking
    engine.memory.record_fact(f"[{category['id']}] sobre {specific or category['label']}")
    engine._last_category_label = category["label"]
    engine._last_specific_topic = specific

    return "\n".join(lines)


def build_trivia_prompt(engine: VarietyEngine) -> str:
    category = engine.pick_trivia_category()
    lines = [
        "═══ PERSONALIDAD ═══",
        engine.get_mood_instruction(),
        engine.get_rapport_instruction(),
        "",
        "═══ TRIVIA ═══",
        f"Categoría: {category}",
        "",
        "Genera UNA pregunta de trivia con 3 opciones (A, B, C).",
        "La pregunta debe ser interesante y para niños (6-10 años).",
        f"{engine.agent_name} debe sonar entusiasmado al plantear el desafío.",
    ]
    if engine.profile.trivia_culture_hint:
        lines.append(engine.profile.trivia_culture_hint)
    return "\n".join(lines)


def build_story_prompt(engine: VarietyEngine, custom_theme: str = "") -> str:
    theme = custom_theme or engine.pick_story_theme()
    if engine.profile.story_moods:
        engine._mood_value = random.choice(engine.profile.story_moods)

    lines = [
        "═══ PERSONALIDAD ═══",
        engine.get_mood_instruction(),
        engine.get_rapport_instruction(),
        engine.get_time_flavor(),
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
    if engine.profile.story_culture_hint:
        lines.append(f"• {engine.profile.story_culture_hint}")
    lines.append("")
    lines.append(f"{engine.agent_name} es el narrador. Puede meter comentarios entre la historia.")

    if engine.memory.story_themes_used:
        lines.append("")
        lines.append("TEMAS YA USADOS (cuenta algo diferente):")
        for t in list(engine.memory.story_themes_used)[-5:]:
            lines.append(f"  - {t}")

    return "\n".join(lines)


def build_riddle_prompt(engine: VarietyEngine) -> str:
    if engine.profile.riddle_moods:
        engine._mood_value = random.choice(engine.profile.riddle_moods)
    lines = [
        "═══ PERSONALIDAD ═══",
        engine.get_mood_instruction(),
        engine.get_rapport_instruction(),
        "",
        "═══ ADIVINANZA ═══",
        "Inventa una adivinanza original, divertida y para niños.",
    ]
    if engine.profile.riddle_culture_hint:
        lines.append(engine.profile.riddle_culture_hint)
    lines.append("")
    lines.append(f"{engine.agent_name} la presenta con entusiasmo: {engine.profile.riddle_challenge}")
    if engine.memory.riddles_told:
        lines.append("")
        lines.append("ADIVINANZAS YA CONTADAS (inventa algo diferente):")
        for i, r in enumerate(list(engine.memory.riddles_told)[-8:], 1):
            lines.append(f"  {i}. {r}")
    return "\n".join(lines)
