"""
backend_client.py — Shared HTTP client for agent→backend communication.

Centralizes the repeated pattern of:
1. Check backend URL + secret
2. Build aiohttp session with timeout
3. Send request with x-agent-secret header
4. Handle errors gracefully

Used by: transcript.py, memory.py, custom_personality.py
"""

from typing import Any

import aiohttp

from src.config import Settings
from src.logger import get_logger

logger = get_logger("nebu.backend_client")


def is_backend_configured(settings: Settings) -> bool:
    """Check if backend URL and internal secret are configured."""
    return bool(settings.agent_backend_url and settings.agent_internal_secret)


async def backend_request(
    settings: Settings,
    method: str,
    path: str,
    job_logger,
    *,
    json: dict | None = None,
    timeout_seconds: float = 10,
    label: str = "backend request",
) -> dict | None:
    """
    Make an authenticated request to the backend API.

    Returns the parsed JSON response on success, or None on failure.
    All errors are logged and swallowed (fault-tolerant by design).
    """
    if not is_backend_configured(settings):
        job_logger.debug(f"Backend not configured, skipping {label}")
        return None

    url = f"{settings.agent_backend_url.rstrip('/')}/{path.lstrip('/')}"

    try:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as http:
            request_method = getattr(http, method.lower())
            kwargs: dict[str, Any] = {
                "headers": {"x-agent-secret": settings.agent_internal_secret},
            }
            if json is not None:
                kwargs["json"] = json

            resp = await request_method(url, **kwargs)

            if resp.status == 200:
                return await resp.json()

            body = await resp.text()
            job_logger.warning(
                f"{label} rejected by backend",
                extra={"status": resp.status, "body": body[:200]},
            )
            return None

    except TimeoutError:
        job_logger.warning(f"{label} timed out (>{timeout_seconds}s)")
        return None
    except Exception as exc:
        job_logger.warning(f"Error in {label}", extra={"error": str(exc)})
        return None
