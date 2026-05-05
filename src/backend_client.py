"""
backend_client.py — Shared HTTP client for agent→backend communication.

Centralizes the repeated pattern of:
1. Check backend URL + secret
2. Reuse a persistent aiohttp session (connection pooling)
3. Send request with x-agent-secret header
4. Handle errors gracefully

Used by: transcript.py, memory.py, custom_personality.py
"""

from typing import Any

import aiohttp

from src.config import Settings
from src.logger import get_logger

logger = get_logger("nebu.backend_client")

# ── Persistent session (connection pool) ─────────────────────────────
_session: aiohttp.ClientSession | None = None


def _get_session(settings: Settings) -> aiohttp.ClientSession:
    """Return (or lazily create) a long-lived ClientSession with keep-alive.

    No usamos `base_url=`: aiohttp descarta el path del base_url y sólo
    respeta scheme://host:port, lo que rompía silenciosamente cualquier URL
    con prefix tipo `/api/v1`. La URL completa se construye en cada request.
    """
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            headers={"x-agent-secret": settings.agent_internal_secret},
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=20, keepalive_timeout=60),
        )
    return _session


def _build_url(settings: Settings, path: str) -> str:
    base = settings.agent_backend_url.rstrip("/")
    return f"{base}/{path.lstrip('/')}"


async def close_session() -> None:
    """Gracefully close the shared session (call on agent shutdown)."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None


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
    Reuses a persistent aiohttp session for connection pooling.
    """
    if not is_backend_configured(settings):
        job_logger.debug(f"Backend not configured, skipping {label}")
        return None

    try:
        http = _get_session(settings)
        request_method = getattr(http, method.lower())
        kwargs: dict[str, Any] = {}
        if json is not None:
            kwargs["json"] = json
        if timeout_seconds != 10:
            kwargs["timeout"] = aiohttp.ClientTimeout(total=timeout_seconds)

        resp = await request_method(_build_url(settings, path), **kwargs)

        if resp.status == 200:
            return await resp.json()

        body = await resp.text()
        job_logger.warning(
            f"{label} rejected: HTTP {resp.status} — {body[:200]}",
        )
        return None

    except TimeoutError:
        job_logger.warning(f"{label} timed out (>{timeout_seconds}s)")
        return None
    except Exception as exc:
        job_logger.warning(f"{label} failed: {exc}")
        return None
