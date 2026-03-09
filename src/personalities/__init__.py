"""
Personality profile registry.

Usage:
    from src.personalities import get_profile, REGISTRY

    profile = get_profile("neutral")   # returns PersonalityProfile
    profile = get_profile("mexican")
    profile = get_profile()            # returns default (neutral)
"""

from src.personality import PersonalityProfile
from src.personality_loader import discover_profiles, load_profile

REGISTRY: dict[str, PersonalityProfile] = {}
DEFAULT_PROFILE_ID = "neutral"


def register(profile: PersonalityProfile):
    """Register a personality profile."""
    REGISTRY[profile.id] = profile


def get_profile(profile_id: str | None = None) -> PersonalityProfile:
    """Get a profile by ID, or the default if None."""
    pid = profile_id or DEFAULT_PROFILE_ID
    if pid not in REGISTRY:
        raise ValueError(
            f"Unknown personality profile: {pid!r}. Available: {list(REGISTRY.keys())}"
        )
    return REGISTRY[pid]


# Auto-register all YAML profiles on import
for _pid in discover_profiles():
    register(load_profile(_pid))
