"""
transcript.py — Persistencia del transcript de sesión al backend.
"""

import aiohttp
from livekit.agents import AgentSession

from src.config import Settings
from src.logger import get_logger
from src.metrics import ERRORS_TOTAL

logger = get_logger("nebu.transcript")


async def save_transcript(
    session: AgentSession,
    room_name: str,
    settings: Settings,
    job_logger,
) -> None:
    """Envía el transcript completo al backend en un único HTTP call al cierre de sesión."""
    if not settings.agent_backend_url or not settings.agent_internal_secret:
        return

    try:
        messages = session.history.items
    except Exception as exc:
        job_logger.warning("No se pudo acceder a history", extra={"error": str(exc)})
        return

    lines = []
    for msg in messages:
        role = getattr(msg, "role", None)
        text = getattr(msg, "text_content", None) or ""
        if role == "system":
            continue
        label = "Niño" if role == "user" else session.userdata.get("agent_name", "Nebu")
        if text.strip():
            lines.append(f"[{label}]: {text.strip()}")

    if not lines:
        return

    transcript = "\n".join(lines)
    message_count = len(lines)
    url = f"{settings.agent_backend_url.rstrip('/')}/voice/sessions/transcript"

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as http:
            resp = await http.post(
                url,
                json={
                    "roomName": room_name,
                    "transcript": transcript,
                    "messageCount": message_count,
                },
                headers={"x-agent-secret": settings.agent_internal_secret},
            )
            if resp.status == 200:
                job_logger.info("Transcript guardado", extra={"messages": message_count})
            else:
                body = await resp.text()
                job_logger.warning(
                    "Backend rechazó transcript",
                    extra={"status": resp.status, "body": body[:200]},
                )
    except Exception as exc:
        ERRORS_TOTAL.labels(type="transcript").inc()
        job_logger.warning("Error guardando transcript", extra={"error": str(exc)})
