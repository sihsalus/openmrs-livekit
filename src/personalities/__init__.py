"""
Personality profile registry.

Usage:
    from src.personalities import get_profile, REGISTRY

    profile = get_profile("peruvian")  # returns PersonalityProfile
    profile = get_profile("mexican")
    profile = get_profile()            # returns default (peruvian)
"""

from src.personality import PersonalityProfile

REGISTRY: dict[str, PersonalityProfile] = {}
DEFAULT_PROFILE_ID = "peruvian"


def register(profile: PersonalityProfile):
    """Register a personality profile."""
    REGISTRY[profile.id] = profile


def get_profile(profile_id: str | None = None) -> PersonalityProfile:
    """Get a profile by ID, or the default if None."""
    pid = profile_id or DEFAULT_PROFILE_ID
    if pid not in REGISTRY:
        raise ValueError(
            f"Unknown personality profile: {pid!r}. "
            f"Available: {list(REGISTRY.keys())}"
        )
    return REGISTRY[pid]


# Auto-register built-in profiles on import
from src.personalities.peruvian import profile as _peruvian  # noqa: E402

register(_peruvian)

from src.personalities.mexican import profile as _mexican  # noqa: E402

register(_mexican)

from src.personalities.kpop import profile as _kpop  # noqa: E402

register(_kpop)

from src.personalities.roblox import profile as _roblox  # noqa: E402

register(_roblox)
