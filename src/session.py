"""
session.py — Setup y lifecycle de AgentSession.

Incluye:
- TurnContext: dataclass para estado de turno compartido entre session y events.
- NebuAgent: clase que construye la AgentSession con STT/LLM/TTS y métricas.
- Helpers de construcción de instrucciones a partir de room metadata.
- Setup de VarietyEngine y envío del saludo inicial.
"""

import asyncio
import json
import re
from dataclasses import dataclass
from types import SimpleNamespace

from livekit import agents
from livekit.agents import AgentSession
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


@dataclass
class TurnContext:
    turn_num: int = 0
    turn_id: str | None = None


@dataclass
class TranscriptFlag:
    """Shared flag to ensure transcript is saved exactly once."""

    done: bool = False


class NebuAgent:
    """Agente Nebu — construye y configura la AgentSession."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._job_logger = None
        self._turn_context: TurnContext | None = None

    def _on_llm_metrics(self, metrics: LLMMetrics) -> None:
        if self._job_logger:
            self._job_logger.info(
                f"🧠 LLM: TTFT={metrics.ttft:.3f}s, tokens/s={metrics.tokens_per_second:.1f}, "
                f"prompt_tok={metrics.prompt_tokens}, completion_tok={metrics.completion_tokens}",
                extra={"turn_id": self._turn_context.turn_id if self._turn_context else None},
            )

    def _on_stt_metrics(self, metrics: STTMetrics) -> None:
        if self._job_logger:
            self._job_logger.info(
                f"🎤 STT: duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}",
                extra={"turn_id": self._turn_context.turn_id if self._turn_context else None},
            )
        STT_DURATION.labels(stt_provider=self.settings.stt_provider).observe(metrics.duration)

    def _on_eou_metrics(self, metrics: EOUMetrics) -> None:
        if self._turn_context is not None:
            self._turn_context.turn_num += 1
            self._turn_context.turn_id = f"t{self._turn_context.turn_num:03d}"
        if self._job_logger:
            self._job_logger.info(
                f"⏱️ EOU: eou_delay={metrics.end_of_utterance_delay:.3f}s, transcription_delay={metrics.transcription_delay:.3f}s",
                extra={"turn_id": self._turn_context.turn_id if self._turn_context else None},
            )
        EOU_DELAY.observe(metrics.end_of_utterance_delay)

    def _on_tts_metrics(self, metrics: TTSMetrics) -> None:
        if self._job_logger:
            self._job_logger.info(
                f"🔊 TTS: TTFB={metrics.ttfb:.3f}s, duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}",
                extra={"turn_id": self._turn_context.turn_id if self._turn_context else None},
            )
        TTS_TTFB.labels(tts_provider=self.settings.tts_provider).observe(metrics.ttfb)
        TTS_AUDIO_DURATION.labels(tts_provider=self.settings.tts_provider).observe(
            metrics.audio_duration
        )

    def _on_session_metrics(self, ev) -> None:
        if isinstance(ev.metrics, EOUMetrics):
            self._on_eou_metrics(ev.metrics)

    async def create_session(
        self,
        instructions: str,
        job_logger=None,
        turn_context: TurnContext | None = None,
    ) -> AgentSession:
        """Crea una sesión de agente con la configuración actual."""
        self._job_logger = job_logger
        self._turn_context = turn_context

        stt = build_stt(self.settings)
        llm = build_llm(self.settings)
        tts = build_tts(self.settings)

        llm.on("metrics_collected", self._on_llm_metrics)
        stt.on("metrics_collected", self._on_stt_metrics)
        tts.on("metrics_collected", self._on_tts_metrics)

        session = AgentSession(
            vad=silero.VAD.load(),
            stt=stt,
            llm=llm,
            tts=tts,
            userdata={},
            allow_interruptions=self.settings.allow_interruptions,
            min_interruption_words=self.settings.min_interruption_words,
            min_interruption_duration=self.settings.min_interruption_duration,
            min_endpointing_delay=self.settings.min_endpointing_delay,
            max_endpointing_delay=self.settings.max_endpointing_delay,
        )

        session.on("metrics_collected", self._on_session_metrics)

        return session


def parse_room_metadata(ctx: agents.JobContext, job_logger) -> dict:
    """Parsea la metadata JSON del room. Retorna dict vacío si falta o es inválida."""
    if not ctx.room.metadata:
        job_logger.warning("Room metadata empty")
        return {}
    try:
        metadata = json.loads(ctx.room.metadata)
        job_logger.info(
            "Metadata parsed",
            extra={
                "keys": list(metadata.keys()),
                "has_age": metadata.get("owner_age") is not None,
                "language": metadata.get("preferred_language", "es"),
                "personality": metadata.get("personality_profile"),
            },
        )
        return metadata
    except json.JSONDecodeError as e:
        job_logger.error("Failed to parse metadata", extra={"error": str(e)})
        return {}


def build_instructions(
    room_metadata: dict,
    settings: Settings,
    job_logger,
    memory_context: str | None = None,
    agent_name: str = "Nebu",
) -> str:
    """Construye las instrucciones del agente a partir de metadata y settings."""
    raw_prompt = room_metadata.get("agent_prompt")
    custom_prompt = (
        _sanitize_custom_prompt(raw_prompt, settings.max_custom_prompt_chars)
        if raw_prompt
        else None
    )
    owner_context = _build_owner_context(room_metadata)
    if custom_prompt:
        job_logger.info("Using custom prompt", extra={"length": len(custom_prompt)})
    else:
        job_logger.info("Using default prompt")
        custom_prompt = get_system_prompt(name=agent_name)
    if owner_context:
        job_logger.info("Owner context injected into prompt")

    memory_block = ""
    if memory_context:
        memory_block = (
            "\n\nMEMORIA PREVIA (no repitas datos ya contados):\n" + memory_context
        )
        job_logger.info("Memory context injected into prompt", extra={"length": len(memory_context)})

    return custom_prompt + owner_context + memory_block + CAPABILITIES_BLOCK


async def setup_variety_engine(
    session: AgentSession,
    room_metadata: dict,
    settings: Settings,
    job_logger,
    agent_name: str = "Nebu",
):
    """Inicializa VarietyEngine si está habilitado. Retorna el perfil de personalidad."""
    if not settings.enable_variety_engine:
        session.userdata["variety"] = None
        job_logger.info("VarietyEngine disabled - using hardcoded neutral profile")
        return SimpleNamespace(id="neutral", name="Neutral")

    from src.personalities import get_profile
    from src.variety import VarietyEngine

    profile = None

    # Priority 1: Custom personality from backend
    custom_personality_id = room_metadata.get("custom_personality_id")
    if custom_personality_id:
        from src.custom_personality import fetch_custom_personality

        profile = await fetch_custom_personality(custom_personality_id, settings, job_logger)
        if profile:
            job_logger.info(
                "Custom personality loaded from backend",
                extra={"id": custom_personality_id, "display_name": profile.display_name},
            )

    # Priority 2: Built-in YAML personality
    if profile is None:
        personality_id = room_metadata.get("personality_profile")
        try:
            profile = get_profile(personality_id)
        except ValueError:
            job_logger.warning(
                "Unknown personality profile, using default",
                extra={"requested": personality_id},
            )
            profile = get_profile()

    profile.resolve_name(agent_name)
    session.userdata["variety"] = VarietyEngine(profile=profile, agent_name=agent_name)
    job_logger.info(
        "VarietyEngine enabled", extra={"profile": profile.id, "agent_name": agent_name}
    )
    return profile


async def send_initial_greeting(
    session: AgentSession,
    settings: Settings,
    room_metadata: dict,
    job_logger,
    agent_name: str = "Nebu",
) -> None:
    """Envía el saludo inicial tras el delay configurado."""
    if not settings.greeting_enabled:
        return
    await asyncio.sleep(settings.greeting_delay)
    raw_greeting = room_metadata.get("greeting")
    greeting_text = (
        _sanitize_custom_prompt(raw_greeting, settings.max_custom_prompt_chars)
        if raw_greeting
        else get_greeting(name=agent_name)
    )
    job_logger.info("Sending initial greeting")
    try:
        await session.say(greeting_text)
    except Exception as e:
        job_logger.error("Failed to send greeting", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="greeting").inc()


def _build_owner_context(room_metadata: dict) -> str:
    """Construye un bloque de contexto sobre el niño/owner para inyectar en el prompt."""

    def sanitize(v, limit=200):
        return _sanitize_custom_prompt(str(v), limit)

    lines = []
    if name := room_metadata.get("owner_name"):
        lines.append(f"- Nombre del niño: {sanitize(name, 100)}")
    if age := room_metadata.get("owner_age"):
        lines.append(f"- Edad: {sanitize(age, 10)} años")
    if interests := room_metadata.get("owner_interests"):
        lines.append(f"- Intereses: {sanitize(interests, 500)}")
    if goals := room_metadata.get("learning_goals"):
        lines.append(f"- Objetivos de aprendizaje: {sanitize(goals, 500)}")
    if not lines:
        return ""
    return "\n\nCONTEXTO DE ESTA SESIÓN:\n" + "\n".join(lines)


_INJECTION_PATTERNS = re.compile(
    r"(^|\n)\s*(SYSTEM\s*:|ASSISTANT\s*:|<\|im_start\|>|<\|system\|>|\[INST\])",
    re.IGNORECASE,
)


def _sanitize_custom_prompt(prompt: str, max_chars: int) -> str:
    """Trunca, elimina bytes de control y filtra patrones de inyección."""
    prompt = prompt.strip()[:max_chars]
    prompt = "".join(c for c in prompt if c >= " " or c in "\n\t")
    return _INJECTION_PATTERNS.sub("", prompt)
