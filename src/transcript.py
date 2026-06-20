"""
transcript.py — Persistencia del transcript de sesión al backend.
"""

from livekit.agents import AgentSession

from src.backend_client import backend_request, is_backend_configured
from src.config import Settings
from src.deidentification import deidentify_text
from src.logger import get_logger
from src.metrics import ERRORS_TOTAL, TRANSCRIPT_SAVE_RESULT

logger = get_logger("nebu.transcript")


async def save_transcript(
    session: AgentSession,
    room_name: str,
    settings: Settings,
    job_logger,
) -> None:
    """Envía el transcript completo al backend en un único HTTP call al cierre de sesión."""
    if not settings.enable_transcript_save:
        TRANSCRIPT_SAVE_RESULT.labels(result="disabled").inc()
        job_logger.info("Transcript save disabled by configuration")
        return

    if not is_backend_configured(settings):
        TRANSCRIPT_SAVE_RESULT.labels(result="no_backend").inc()
        return

    try:
        messages = session.history.items
    except Exception as exc:
        job_logger.warning("Failed to access history", extra={"error": str(exc)})
        TRANSCRIPT_SAVE_RESULT.labels(result="exception").inc()
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
        TRANSCRIPT_SAVE_RESULT.labels(result="empty").inc()
        return

    transcript = "\n".join(lines)
    redaction_count = 0
    if settings.transcript_redaction_enabled and not settings.transcript_raw_storage_allowed:
        result = deidentify_text(transcript)
        transcript = result.text
        redaction_count = result.redaction_count

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
            "redacted": settings.transcript_redaction_enabled
            and not settings.transcript_raw_storage_allowed,
            "redactionCount": redaction_count,
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
            TRANSCRIPT_SAVE_RESULT.labels(result="ok").inc()
            job_logger.info("Transcript saved", extra={"messages": message_count})
        else:
            TRANSCRIPT_SAVE_RESULT.labels(result="http_error").inc()
    except Exception as exc:
        ERRORS_TOTAL.labels(type="transcript").inc()
        TRANSCRIPT_SAVE_RESULT.labels(result="exception").inc()
        job_logger.warning("Failed to save transcript", extra={"error": str(exc)})
