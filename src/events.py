"""
events.py — Event listeners de la AgentSession.

Registra:
- user_input_transcribed: filler sound + data channel publish
- conversation_item_added: latencia LLM + data channel publish
- speech_created: cancela filler + latencia de turno
- participant_disconnected: transcript al cerrar
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Coroutine

from livekit import rtc
from livekit.agents import AgentSession, SpeechCreatedEvent

from src.config import Settings
from src.data_channel import publish_transcript
from src.logger import AgentLogger
from src.metrics import (
    LLM_LATENCY,
    TURN_LATENCY,
    TURNS_TOTAL,
)
from src.session import TranscriptFlag, TurnContext
from src.transcript import save_transcript

AGENT_ROOM_PREFIX = "iot-device-"

_bg_tasks: set[asyncio.Task[None]] = set()
_logger = logging.getLogger("nebu.events")


def _fire_and_forget(coro: Coroutine[Any, Any, Any]) -> asyncio.Task[None]:
    task = asyncio.create_task(coro)
    _bg_tasks.add(task)
    task.add_done_callback(_on_task_done)
    return task


def _on_task_done(task: asyncio.Task[None]) -> None:
    _bg_tasks.discard(task)
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        _logger.error("Background task failed: %s", exc, exc_info=exc)


def setup_event_listeners(
    session: AgentSession[Any],
    room: rtc.Room,
    room_name: str,
    settings: Settings,
    turn_context: TurnContext,
    job_logger: AgentLogger,
    transcript_sent: TranscriptFlag,
) -> None:
    """Registra listeners: user_input_transcribed, conversation_item_added, speech_created."""
    _state: dict[str, object] = {"turn_start": None, "filler_task": None}

    def on_user_transcribed(ev: Any) -> None:
        if not ev.is_final:
            return

        _state["turn_start"] = time.time()
        text = ev.transcript.strip()
        if len(text) < 4 or not any(c.isalpha() for c in text):
            job_logger.debug("Transcription discarded (noise)", extra={"text": text})
            return

        job_logger.info(
            "Turno iniciado",
            extra={"turn_id": turn_context.turn_id, "transcript_len": len(text)},
        )

        _fire_and_forget(publish_transcript(room, role="doctor", language="auto", text=text))

        TURNS_TOTAL.labels(personality="clinical").inc()

        if settings.filler_sound_enabled:
            filler_task = _state.get("filler_task")
            if isinstance(filler_task, asyncio.Task) and not filler_task.done():
                filler_task.cancel()

            async def _maybe_filler() -> None:
                await asyncio.sleep(settings.filler_delay)
                try:
                    await session.say(settings.filler_sound_text)
                except asyncio.CancelledError:
                    pass
                except Exception as exc:
                    job_logger.warning("Filler sound failed", extra={"error": str(exc)})

            _state["filler_task"] = asyncio.create_task(_maybe_filler())

    def on_conversation_item(ev: Any) -> None:
        """Latencia LLM + publish assistant response."""
        item = ev.item
        if not hasattr(item, "role") or item.role != "assistant":
            return
        turn_start = _state.get("turn_start")
        if isinstance(turn_start, float):
            LLM_LATENCY.labels(personality="clinical").observe(time.time() - turn_start)
        text = item.text_content
        if text:
            _fire_and_forget(publish_transcript(room, role="assistant", language="auto", text=text))

    def on_speech_created(ev: SpeechCreatedEvent) -> None:
        """Cancela el filler si el LLM respondió a tiempo; registra latencia de turno."""
        filler_task = _state.get("filler_task")
        if isinstance(filler_task, asyncio.Task) and not filler_task.done():
            filler_task.cancel()
            _state["filler_task"] = None
        turn_start = _state.get("turn_start")
        if isinstance(turn_start, float):
            TURN_LATENCY.labels(personality="clinical", tts_provider=settings.tts_provider).observe(
                ev.created_at - turn_start
            )
            _state["turn_start"] = None

    session.on("user_input_transcribed", on_user_transcribed)
    session.on("conversation_item_added", on_conversation_item)
    session.on("speech_created", on_speech_created)

    @room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant) -> None:
        job_logger.info(
            "Participante desconectado, guardando transcript",
            extra={"participant": participant.identity},
        )
        if not transcript_sent.done:
            transcript_sent.done = True
            _fire_and_forget(save_transcript(session, room_name, settings, job_logger))
