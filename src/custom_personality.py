"""
custom_personality.py — Fetch custom personality profiles from the backend.

When a toy has a user-created custom personality (custom_personality_id in room metadata),
this module fetches it from the backend API and converts it into a PersonalityProfile.

Follows the same pattern as memory.py (aiohttp, agent-secret auth, fault-tolerant).
"""

import aiohttp

from src.config import Settings
from src.logger import get_logger
from src.personality import PersonalityProfile
from src.personality_loader import _deep_merge, _load_defaults

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
    if not settings.agent_backend_url or not settings.agent_internal_secret:
        job_logger.debug("Backend not configured, skipping custom personality fetch")
        return None

    url = f"{settings.agent_backend_url.rstrip('/')}/personalities/agent/{personality_id}"

    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as http:
            resp = await http.get(
                url,
                headers={"x-agent-secret": settings.agent_internal_secret},
            )
            if resp.status != 200:
                body = await resp.text()
                job_logger.warning(
                    "Failed to fetch custom personality",
                    extra={"status": resp.status, "body": body[:200], "id": personality_id},
                )
                return None

            data = await resp.json()
            content = data.get("content", {})

    except Exception as exc:
        job_logger.warning(
            "Error fetching custom personality",
            extra={"error": str(exc), "id": personality_id},
        )
        return None

    return _build_profile_from_content(content, job_logger)


def _build_profile_from_content(
    content: dict,
    job_logger,
) -> PersonalityProfile | None:
    """Build a PersonalityProfile from backend JSON content, merged with defaults."""
    try:
        defaults = _load_defaults()
        merged = _deep_merge(defaults, content)

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
