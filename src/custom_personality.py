"""
custom_personality.py — Fetch custom personality profiles from the backend.

When a toy has a user-created custom personality (custom_personality_id in room metadata),
this module fetches it from the backend API and converts it into a PersonalityProfile.
"""

from src.backend_client import backend_request
from src.config import Settings
from src.logger import get_logger
from src.personality import PersonalityProfile
from src.personality_loader import deep_merge, load_defaults

logger = get_logger("nebu.custom_personality")


async def fetch_custom_personality(
    personality_id: str,
    settings: Settings,
    job_logger,
) -> PersonalityProfile | None:
    """
    Fetch a custom personality from the backend and convert to PersonalityProfile.

    Returns a PersonalityProfile on success, or None on failure (graceful fallback).
    The fetched content is deep-merged with defaults.yaml so missing fields get sensible values.
    """
    data = await backend_request(
        settings,
        "GET",
        f"personalities/agent/{personality_id}",
        job_logger,
        timeout_seconds=5,
        label="custom personality fetch",
    )

    if data is None:
        return None

    content = data.get("content", {})
    return _build_profile_from_content(content, job_logger)


def _build_profile_from_content(
    content: dict,
    job_logger,
) -> PersonalityProfile | None:
    """Build a PersonalityProfile from backend JSON content, merged with defaults."""
    try:
        defaults = load_defaults()
        merged = deep_merge(defaults, content)

        # Remove YAML-only keys that aren't PersonalityProfile fields
        for key in (
            "knowledge_module",
            "knowledge_function",
            "knowledge_special_category",
            "knowledge_default_chance",
            "knowledge_special_chance",
            "knowledge_injector",
        ):
            merged.pop(key, None)

        # Fix milestone keys: ensure int
        if "catchphrases" in merged and "milestone" in merged.get("catchphrases", {}):
            milestones = merged["catchphrases"]["milestone"]
            merged["catchphrases"]["milestone"] = {int(k): v for k, v in milestones.items()}

        profile = PersonalityProfile(**merged)
        job_logger.info(
            "Custom personality profile built",
            extra={"id": profile.id, "display_name": profile.display_name},
        )
        return profile

    except Exception as exc:
        job_logger.error(
            "Failed to build PersonalityProfile from custom content",
            extra={"error": str(exc)},
            exc_info=True,
        )
        return None
