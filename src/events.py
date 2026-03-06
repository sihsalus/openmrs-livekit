"""
events.py — Event listeners de la AgentSession y manejo de walkie-talkie.

Registra:
- user_input_transcribed: filler sound + FSM VarietyEngine
- conversation_item_added: latencia LLM + anti-repetición
- speech_created: cancela filler + latencia de turno
- participant_connected/disconnected: walkie-talkie + transcript al cerrar
"""

import asyncio
import time

from livekit import rtc
from livekit.agents import AgentSession, SpeechCreatedEvent

from src.config import Settings
from src.session import TurnContext
from src.metrics import (
    CHILD_SIGNALS_TOTAL,
    LLM_LATENCY,
    TURN_LATENCY,
    TURNS_TOTAL,
)
from src.transcript import save_transcript

# ── Room & participant naming contracts ────────────────────────────────────────
# Must match livekit-client.service.ts (generateVoiceAgentToken, generateParentToken)
# and any frontend/IoT code that creates rooms or identities.
AGENT_ROOM_PREFIX = "iot-device-"
PARENT_IDENTITY_PREFIX = "user-parent-"

# Keeps strong references to fire-and-forget tasks so the GC doesn't destroy them.
_bg_tasks: set[asyncio.Task] = set()


def _fire_and_forget(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
    return task


def setup_walkie_talkie(ctx, session: AgentSession, settings: Settings, job_logger):
    """Registra handlers de walkie-talkie. Retorna _has_parent_in_room o None si está deshabilitado."""
    if not settings.enable_walkie_talkie:
        job_logger.info("Walkie-talkie mode disabled")
        return None

    def _is_parent(participant: rtc.RemoteParticipant) -> bool:
        return participant.identity.startswith(PARENT_IDENTITY_PREFIX)

    def _has_parent_in_room() -> bool:
        return any(_is_parent(p) for p in ctx.room.remote_participants.values())

    async def _pause_for_walkie_talkie():
        session.interrupt()
        session.input.set_audio_enabled(False)
        session.output.set_audio_enabled(False)
        job_logger.info("AI pausado - modo walkie-talkie activo")

    async def _resume_from_walkie_talkie():
        session.input.set_audio_enabled(True)
        session.output.set_audio_enabled(True)
        job_logger.info("AI reanudado - modo walkie-talkie finalizado")

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        job_logger.info("Nuevo participante", extra={"participant": participant.identity})
        if _is_parent(participant):
            job_logger.info(
                "Padre conectado - pausando AI para walkie-talkie",
                extra={"parent_identity": participant.identity},
            )
            _fire_and_forget(_pause_for_walkie_talkie())

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        job_logger.info("Participante desconectado", extra={"participant": participant.identity})
        if _is_parent(participant) and not _has_parent_in_room():
            job_logger.info(
                "Padre desconectado - reanudando AI",
                extra={"parent_identity": participant.identity},
            )
            _fire_and_forget(_resume_from_walkie_talkie())

    job_logger.info("Walkie-talkie mode enabled")
    return _has_parent_in_room


def setup_event_listeners(
    session: AgentSession,
    room: rtc.Room,
    room_name: str,
    settings: Settings,
    turn_context: TurnContext,
    profile,
    job_logger,
    transcript_sent: dict,
) -> None:
    """Registra listeners: user_input_transcribed, conversation_item_added, speech_created."""
    _state: dict = {"turn_start": None, "filler_task": None}

    def on_user_transcribed(ev):
        """Filler sound + FSM Mood Lite + Persona Anchor/Sliding Summary."""
        if not ev.is_final:
            return

        _state["turn_start"] = time.time()
        text = ev.transcript.strip()
        if len(text) < 4 or not any(c.isalpha() for c in text):
            job_logger.debug("Transcripción descartada (ruido)", extra={"text": text})
            return

        job_logger.info(
            "Turno iniciado",
            extra={"turn_id": turn_context.turn_id, "transcript_len": len(text)},
        )

        if settings.filler_sound_enabled:
            if _state["filler_task"] and not _state["filler_task"].done():
                _state["filler_task"].cancel()

            async def _maybe_filler():
                await asyncio.sleep(settings.filler_delay)
                try:
                    await session.say(settings.filler_sound_text)
                except asyncio.CancelledError:
                    pass
                except Exception as exc:
                    job_logger.warning(
                        "Filler sound falló",
                        extra={"error": str(exc)},
                    )

            _state["filler_task"] = asyncio.create_task(_maybe_filler())

        variety = session.userdata.get("variety")
        if not variety:
            return

        child_signal = variety.detect_child_signal(ev.transcript)
        variety.react_to_signal(child_signal)
        CHILD_SIGNALS_TOTAL.labels(signal=child_signal).inc()

        variety.tick()
        TURNS_TOTAL.labels(personality=profile.id).inc()
        anchor = variety.build_persona_anchor()
        summary = variety.build_sliding_summary()
        if anchor or summary:
            base = session.userdata.get("base_instructions", "")
            extra = ("\n" + anchor if anchor else "") + ("\n" + summary if summary else "")
            _fire_and_forget(session.current_agent.update_instructions(base + extra))

    def on_conversation_item(ev):
        """Latencia LLM + anti-repetición (si VarietyEngine activo)."""
        item = ev.item
        if not hasattr(item, "role") or item.role != "assistant":
            return
        if _state["turn_start"] is not None:
            LLM_LATENCY.labels(personality=profile.id).observe(time.time() - _state["turn_start"])
        text = item.text_content
        if text:
            variety = session.userdata.get("variety")
            if variety:
                variety.record_agent_response(text)

    def on_speech_created(ev: SpeechCreatedEvent):
        """Cancela el filler si el LLM respondió a tiempo; registra latencia de turno."""
        if _state["filler_task"] and not _state["filler_task"].done():
            _state["filler_task"].cancel()
            _state["filler_task"] = None
        if _state["turn_start"] is not None:
            TURN_LATENCY.labels(personality=profile.id, tts_provider=settings.tts_provider).observe(
                ev.created_at - _state["turn_start"]
            )
            _state["turn_start"] = None

    session.on("user_input_transcribed", on_user_transcribed)
    session.on("conversation_item_added", on_conversation_item)
    session.on("speech_created", on_speech_created)

    @room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        if participant.identity.startswith(PARENT_IDENTITY_PREFIX):
            return  # padre saliendo no termina la sesión del niño
        job_logger.info(
            "Participante desconectado, guardando transcript",
            extra={"participant": participant.identity},
        )
        if not transcript_sent["done"]:
            transcript_sent["done"] = True
            _fire_and_forget(save_transcript(session, room_name, settings, job_logger))
