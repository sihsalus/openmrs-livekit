"""
session.py — Setup y lifecycle de AgentSession.

Incluye:
- NebuAgent: clase que construye la AgentSession con STT/LLM/TTS y métricas.
- Helpers de construcción de instrucciones a partir de room metadata.
- Setup de VarietyEngine y envío del saludo inicial.
"""

import asyncio
import json
import time
from types import SimpleNamespace

from livekit import agents
from livekit.agents import Agent, AgentSession
from livekit.agents.metrics import EOUMetrics, LLMMetrics, STTMetrics, TTSMetrics
from livekit.plugins import silero

from src.config import Settings
from src.logger import get_logger
from src.metrics import (
    EOU_DELAY,
    ERRORS_TOTAL,
    STT_DURATION,
    TTS_AUDIO_DURATION,
    TTS_TTFB,
)
from src.prompts import CAPABILITIES_BLOCK, get_greeting, get_system_prompt
from src.providers import build_llm, build_stt, build_tts

logger = get_logger("nebu.session")


class NebuAgent:
    """Agente Nebu — construye y configura la AgentSession."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session: AgentSession | None = None

    async def create_session(
        self, instructions: str, job_logger=None, turn_detection_model=None, turn_context=None
    ) -> AgentSession:
        """Crea una sesión de agente con la configuración actual."""
        stt = build_stt(self.settings)
        llm = build_llm(self.settings)
        tts = build_tts(self.settings)

        def _tid() -> str | None:
            return turn_context["turn_id"] if turn_context else None

        def llm_metrics_wrapper(metrics: LLMMetrics):
            if job_logger:
                job_logger.info(
                    f"🧠 LLM: TTFT={metrics.ttft:.3f}s, tokens/s={metrics.tokens_per_second:.1f}, "
                    f"prompt_tok={metrics.prompt_tokens}, completion_tok={metrics.completion_tokens}",
                    extra={"turn_id": _tid()},
                )

        def stt_metrics_wrapper(metrics: STTMetrics):
            if job_logger:
                job_logger.info(
                    f"🎤 STT: duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}",
                    extra={"turn_id": _tid()},
                )
            STT_DURATION.labels(stt_provider=self.settings.stt_provider).observe(metrics.duration)

        def eou_metrics_wrapper(metrics: EOUMetrics):
            if turn_context is not None:
                turn_context["turn_num"] += 1
                turn_context["turn_id"] = f"t{turn_context['turn_num']:03d}"
            if job_logger:
                job_logger.info(
                    f"⏱️ EOU: eou_delay={metrics.end_of_utterance_delay:.3f}s, transcription_delay={metrics.transcription_delay:.3f}s",
                    extra={"turn_id": _tid()},
                )
            EOU_DELAY.observe(metrics.end_of_utterance_delay)

        def tts_metrics_wrapper(metrics: TTSMetrics):
            if job_logger:
                job_logger.info(
                    f"🔊 TTS: TTFB={metrics.ttfb:.3f}s, duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}",
                    extra={"turn_id": _tid()},
                )
            TTS_TTFB.labels(tts_provider=self.settings.tts_provider).observe(metrics.ttfb)
            TTS_AUDIO_DURATION.labels(tts_provider=self.settings.tts_provider).observe(
                metrics.audio_duration
            )

        llm.on("metrics_collected", llm_metrics_wrapper)
        stt.on("metrics_collected", stt_metrics_wrapper)
        tts.on("metrics_collected", tts_metrics_wrapper)

        session = AgentSession(
            turn_detection=turn_detection_model,
            vad=silero.VAD.load(
                min_silence_duration=self.settings.vad_min_silence_duration,
                activation_threshold=self.settings.vad_activation_threshold,
                min_speech_duration=self.settings.vad_min_speech_duration,
            ),
            stt=stt,
            llm=llm,
            tts=tts,
            userdata={},
            allow_interruptions=self.settings.allow_interruptions,
            min_interruption_words=self.settings.min_interruption_words,
            min_interruption_duration=self.settings.min_interruption_duration,
            min_endpointing_delay=self.settings.min_endpointing_delay,
            max_endpointing_delay=self.settings.max_endpointing_delay,
            user_away_timeout=self.settings.user_away_timeout,
        )

        session.on(
            "metrics_collected",
            lambda ev: (
                eou_metrics_wrapper(ev.metrics) if isinstance(ev.metrics, EOUMetrics) else None
            ),
        )

        return session


def parse_room_metadata(ctx: agents.JobContext, job_logger) -> dict:
    """Parsea la metadata JSON del room. Retorna dict vacío si falta o es inválida."""
    if not ctx.room.metadata:
        job_logger.warning("Room metadata vacia")
        return {}
    try:
        metadata = json.loads(ctx.room.metadata)
        job_logger.info(
            "Metadata parseada",
            extra={
                "keys": list(metadata.keys()),
                "owner_age": metadata.get("owner_age"),
                "language": metadata.get("preferred_language", "es"),
                "personality": metadata.get("personality_profile"),
            },
        )
        return metadata
    except json.JSONDecodeError as e:
        job_logger.error("Error parseando metadata", extra={"error": str(e)})
        return {}


def build_instructions(room_metadata: dict, settings: Settings, job_logger) -> str:
    """Construye las instrucciones del agente a partir de metadata y settings."""
    raw_prompt = room_metadata.get("agent_prompt")
    custom_prompt = (
        _sanitize_custom_prompt(raw_prompt, settings.max_custom_prompt_chars)
        if raw_prompt
        else None
    )
    owner_context = _build_owner_context(room_metadata)
    if custom_prompt:
        job_logger.info("Usando prompt personalizado", extra={"length": len(custom_prompt)})
    else:
        job_logger.info("Usando prompt por defecto")
        custom_prompt = get_system_prompt()
    if owner_context:
        job_logger.info("Contexto del owner inyectado en prompt")
    return custom_prompt + owner_context + CAPABILITIES_BLOCK


def setup_variety_engine(
    session: AgentSession, room_metadata: dict, settings: Settings, job_logger
):
    """Inicializa VarietyEngine si está habilitado. Retorna el perfil de personalidad."""
    if not settings.enable_variety_engine:
        session.userdata["variety"] = None
        job_logger.info("VarietyEngine disabled - using hardcoded neutral profile")
        return SimpleNamespace(id="neutral", name="Neutral")

    from src.personalities import get_profile
    from src.variety import VarietyEngine

    personality_id = room_metadata.get("personality_profile")
    try:
        profile = get_profile(personality_id)
    except ValueError:
        job_logger.warning(
            "Unknown personality profile, using default",
            extra={"requested": personality_id},
        )
        profile = get_profile()
    session.userdata["variety"] = VarietyEngine(profile=profile)
    job_logger.info("VarietyEngine enabled", extra={"profile": profile.id})
    return profile


async def send_initial_greeting(
    session: AgentSession, settings: Settings, room_metadata: dict, job_logger
) -> None:
    """Envía el saludo inicial tras el delay configurado."""
    if not settings.greeting_enabled:
        return
    await asyncio.sleep(settings.greeting_delay)
    raw_greeting = room_metadata.get("greeting")
    greeting_text = (
        _sanitize_custom_prompt(raw_greeting, settings.max_custom_prompt_chars)
        if raw_greeting
        else get_greeting()
    )
    job_logger.info("Enviando greeting inicial")
    try:
        await session.say(greeting_text)
    except Exception as e:
        job_logger.error("Error enviando greeting", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="greeting").inc()


def _build_owner_context(room_metadata: dict) -> str:
    """Construye un bloque de contexto sobre el niño/owner para inyectar en el prompt."""
    lines = []
    if name := room_metadata.get("owner_name"):
        lines.append(f"- Nombre del niño: {name}")
    if age := room_metadata.get("owner_age"):
        lines.append(f"- Edad: {age} años")
    if interests := room_metadata.get("owner_interests"):
        lines.append(f"- Intereses: {interests}")
    if goals := room_metadata.get("learning_goals"):
        lines.append(f"- Objetivos de aprendizaje: {goals}")
    if toy_name := room_metadata.get("toy_name"):
        lines.append(f"- En esta sesión te llamas '{toy_name}'")
    if not lines:
        return ""
    return "\n\nCONTEXTO DE ESTA SESIÓN:\n" + "\n".join(lines)


def _sanitize_custom_prompt(prompt: str, max_chars: int) -> str:
    """Trunca y elimina bytes de control de prompts externos (anti-injection)."""
    prompt = prompt.strip()[:max_chars]
    return "".join(c for c in prompt if c >= " " or c in "\n\t")
