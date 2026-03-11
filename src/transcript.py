"""
transcript.py — Persistencia del transcript de sesión al backend.
"""

from livekit.agents import AgentSession

from src.backend_client import backend_request, is_backend_configured
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
    if not is_backend_configured(settings):
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

    engagement_stats = None
    variety = session.userdata.get("variety")
    if variety is not None:
        try:
            engagement_stats = variety.get_session_stats()
        except Exception:
            job_logger.warning("Failed to collect engagement stats")

    try:
        payload: dict = {
            "roomName": room_name,
            "transcript": transcript,
            "messageCount": message_count,
        }
        if engagement_stats:
            payload["engagementStats"] = engagement_stats

        result = await backend_request(
            settings,
            "POST",
            "voice/sessions/transcript",
            job_logger,
            json=payload,
            label="save transcript",
        )
        if result is not None:
            job_logger.info("Transcript guardado", extra={"messages": message_count})
    except Exception as exc:
        ERRORS_TOTAL.labels(type="transcript").inc()
        job_logger.warning("Error guardando transcript", extra={"error": str(exc)})
