"""
personality_loader — Load PersonalityProfile from YAML + defaults.

Usage:
    from src.personality_loader import load_profile, discover_profiles

    profile = load_profile("peruvian")  # loads src/personalities/peruvian.yaml
    ids = discover_profiles()           # ["peruvian", "mexican", "kpop", "roblox"]
"""

import random
from pathlib import Path

import yaml

from src.knowledge_loader import build_knowledge_injection
from src.personality import PersonalityProfile

_PERSONALITIES_DIR = Path(__file__).parent / "personalities"
_defaults_cache: dict | None = None
_profile_cache: dict[str, PersonalityProfile] = {}


def _load_defaults() -> dict:
    """Load and cache defaults.yaml."""
    global _defaults_cache
    if _defaults_cache is None:
        with open(_PERSONALITIES_DIR / "defaults.yaml") as f:
            _defaults_cache = yaml.safe_load(f) or {}
    return _defaults_cache


def _deep_merge(base: dict, override: dict) -> dict:
    """
    Deep-merge override into base. Returns new dict.

    - Scalars: override wins
    - Lists: override REPLACES entire list (no append)
    - Dicts: recursive merge (override keys win)
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _build_knowledge_injector(
    module_name: str,
    special_category: str,
    default_chance: float = 0.12,
    special_chance: float = 0.25,
):
    """
    Build a knowledge_injector callable from YAML config.

    Uses knowledge_loader to load the YAML knowledge module and
    wraps it with chance-based logic.
    """
    def injector(category_id: str) -> str:
        chance = special_chance if category_id == special_category else default_chance
        if random.random() > chance:
            return ""
        return f"\n📚 {build_knowledge_injection(module_name)}"

    return injector


def load_profile(personality_id: str) -> PersonalityProfile:
    """
    Load a PersonalityProfile from YAML with defaults deep-merged.

    1. Load defaults.yaml
    2. Load {personality_id}.yaml
    3. Deep-merge (personality overrides defaults)
    4. Wire knowledge_injector callable
    5. Fix milestone keys (YAML int keys)
    6. Construct PersonalityProfile
    """
    if personality_id in _profile_cache:
        return _profile_cache[personality_id]

    defaults = _load_defaults()

    yaml_path = _PERSONALITIES_DIR / f"{personality_id}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"No YAML profile found: {yaml_path}")

    with open(yaml_path) as f:
        personality_data = yaml.safe_load(f)

    merged = _deep_merge(defaults, personality_data)

    # Pop YAML-only knowledge config keys (not PersonalityProfile fields)
    knowledge_module = merged.pop("knowledge_module", None)
    merged.pop("knowledge_function", None)  # legacy, no longer used
    knowledge_special_category = merged.pop("knowledge_special_category", None)
    default_chance = merged.pop("knowledge_default_chance", 0.12)
    special_chance = merged.pop("knowledge_special_chance", 0.25)

    knowledge_injector = None
    if knowledge_module and knowledge_special_category:
        knowledge_injector = _build_knowledge_injector(
            module_name=knowledge_module,
            special_category=knowledge_special_category,
            default_chance=default_chance,
            special_chance=special_chance,
        )

    # Fix YAML milestone keys: ensure int
    if "catchphrases" in merged and "milestone" in merged.get("catchphrases", {}):
        milestones = merged["catchphrases"]["milestone"]
        merged["catchphrases"]["milestone"] = {int(k): v for k, v in milestones.items()}

    # Remove any leftover key not in PersonalityProfile
    merged.pop("knowledge_injector", None)

    profile = PersonalityProfile(knowledge_injector=knowledge_injector, **merged)
    _profile_cache[personality_id] = profile
    return profile


def discover_profiles() -> list[str]:
    """Return personality IDs found as YAML files (excluding defaults/TEMPLATE)."""
    return sorted(
        p.stem
        for p in _PERSONALITIES_DIR.glob("*.yaml")
        if p.stem not in ("defaults", "TEMPLATE")
    )
