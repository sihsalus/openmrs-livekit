"""
prompt_flavor.py — Flavor injections for personality-driven prompts.

Enriches base prompts with cultural connections, rants, slang,
knowledge injection, and hype evolution. Extracted from VarietyEngine.
"""

import random

from src.personality import PersonalityProfile


def build_culture_injection(
    profile: PersonalityProfile,
    culture_hype: float,
    category_id: str,
) -> str:
    """Inyecta conexión cultural si toca."""
    if category_id in profile.hype_boost_categories:
        return ""

    if not profile.culture_connections:
        return ""

    chance = profile.culture_brain_chance + (culture_hype * 0.3)
    if random.random() > chance:
        return ""

    connection = random.choice(profile.culture_connections)
    if profile.bonus_facts:
        fact = random.choice(profile.bonus_facts)
        connection = connection.replace("{culture_fact}", fact)

    return f"\n🧠 CULTURE BRAIN: {connection}"


def maybe_culture_rant(profile: PersonalityProfile) -> str:
    if not profile.culture_rants:
        return ""
    if random.random() > profile.rant_chance:
        return ""
    return f"\n🎭 RANT (úsalo antes del dato): {random.choice(profile.culture_rants)}"


def maybe_slang(profile: PersonalityProfile) -> str:
    if not profile.slang_phrases:
        return ""
    if random.random() > profile.slang_chance:
        return ""
    return (
        f"\nJERGA: Mete un '{random.choice(profile.slang_phrases)}' natural "
        f"en tu respuesta."
    )


def maybe_knowledge(profile: PersonalityProfile, category_id: str) -> str:
    if profile.knowledge_injector is None:
        return ""
    return profile.knowledge_injector(category_id)


def evolve_hype(
    current_hype: float,
    profile: PersonalityProfile,
    category_id: str,
) -> float:
    """Sube el hype cultural con el tiempo y con temas afines. Returns new hype value."""
    new_hype = min(profile.hype_cap, current_hype + profile.hype_growth)
    if category_id in profile.hype_boost_categories:
        new_hype = min(profile.hype_cap, new_hype + profile.hype_boost_growth)
    return new_hype
