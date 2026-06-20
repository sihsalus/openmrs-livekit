"""
session.py — Setup y lifecycle de AgentSession.

Incluye:
- TurnContext: dataclass para estado de turno compartido entre session y events.
- NebuAgent: clase que construye la AgentSession con STT/LLM/TTS y métricas.
- Helpers de construcción de instrucciones a partir de room metadata.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any

from livekit import agents
from livekit.agents import AgentSession
from livekit.agents.metrics import EOUMetrics, LLMMetrics, STTMetrics, TTSMetrics

from src.config import Settings
from src.logger import get_logger
from src.metrics import (
    EOU_DELAY,
    ERRORS_TOTAL,
    STT_DURATION,
    TTS_AUDIO_DURATION,
    TTS_TTFB,
)
from src.prompt_budget import BudgetSection, compose_budgeted_text, estimate_tokens
from src.prompts import get_capabilities_block, get_greeting, get_system_prompt

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
    """Clinical voice agent — construye y configura la AgentSession."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._job_logger = None
        self._turn_context: TurnContext | None = None

    def _on_llm_metrics(self, metrics: LLMMetrics) -> None:
        if self._job_logger:
            self._job_logger.info(
                f"LLM: TTFT={metrics.ttft:.3f}s, tokens/s={metrics.tokens_per_second:.1f}, "
                f"prompt_tok={metrics.prompt_tokens}, completion_tok={metrics.completion_tokens}",
                extra={"turn_id": self._turn_context.turn_id if self._turn_context else None},
            )

    def _on_stt_metrics(self, metrics: STTMetrics) -> None:
        if self._job_logger:
            self._job_logger.info(
                f"STT: duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}",
                extra={"turn_id": self._turn_context.turn_id if self._turn_context else None},
            )
        STT_DURATION.labels(stt_provider=self.settings.stt_provider).observe(metrics.duration)

    def _on_eou_metrics(self, metrics: EOUMetrics) -> None:
        if self._turn_context is not None:
            self._turn_context.turn_num += 1
            self._turn_context.turn_id = f"t{self._turn_context.turn_num:03d}"
        if self._job_logger:
            self._job_logger.info(
                f"EOU: eou_delay={metrics.end_of_utterance_delay:.3f}s, transcription_delay={metrics.transcription_delay:.3f}s",
                extra={"turn_id": self._turn_context.turn_id if self._turn_context else None},
            )
        EOU_DELAY.observe(metrics.end_of_utterance_delay)

    def _on_tts_metrics(self, metrics: TTSMetrics) -> None:
        if self._job_logger:
            self._job_logger.info(
                f"TTS: TTFB={metrics.ttfb:.3f}s, duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}",
                extra={"turn_id": self._turn_context.turn_id if self._turn_context else None},
            )
        TTS_TTFB.labels(tts_provider=self.settings.tts_provider).observe(metrics.ttfb)
        TTS_AUDIO_DURATION.labels(tts_provider=self.settings.tts_provider).observe(
            metrics.audio_duration
        )

    def _on_session_metrics(self, ev: Any) -> None:
        if isinstance(ev.metrics, EOUMetrics):
            self._on_eou_metrics(ev.metrics)

    async def create_session(
        self,
        instructions: str,
        job_logger=None,
        turn_context: TurnContext | None = None,
    ) -> AgentSession:
        """Crea una sesión de agente con la configuración actual."""
        from livekit.plugins import silero

        from src.providers import build_llm, build_stt, build_tts

        self._job_logger = job_logger
        self._turn_context = turn_context

        stt = build_stt(self.settings)
        llm = build_llm(self.settings)
        tts = build_tts(self.settings)

        llm.on("metrics_collected", self._on_llm_metrics)
        stt.on("metrics_collected", self._on_stt_metrics)
        tts.on("metrics_collected", self._on_tts_metrics)

        session = AgentSession(
            vad=silero.VAD.load(
                min_silence_duration=self.settings.vad_min_silence_duration,
                activation_threshold=self.settings.vad_activation_threshold,
                min_speech_duration=self.settings.vad_min_speech_duration,
                prefix_padding_duration=self.settings.vad_prefix_padding_duration,
            ),
            stt=stt,
            llm=llm,
            tts=tts,
            turn_detection=self.settings.turn_detection_mode,
            userdata={},
            allow_interruptions=self.settings.allow_interruptions,
            min_interruption_words=self.settings.min_interruption_words,
            min_interruption_duration=self.settings.min_interruption_duration,
            min_endpointing_delay=self.settings.min_endpointing_delay,
            max_endpointing_delay=self.settings.max_endpointing_delay,
        )

        session.on("metrics_collected", self._on_session_metrics)

        return session


def parse_room_metadata(ctx: agents.JobContext, job_logger) -> dict[str, object]:  # type: ignore[type-arg]
    """Parsea la metadata JSON del room. Retorna dict vacío si falta o es inválida."""
    if not ctx.room.metadata:
        job_logger.warning("Room metadata empty")
        return {}
    try:
        metadata = json.loads(ctx.room.metadata)
        job_logger.info("Metadata parsed", extra={"keys": list(metadata.keys())})
        return metadata
    except json.JSONDecodeError as e:
        job_logger.error("Failed to parse metadata", extra={"error": str(e)})
        return {}


def build_instructions(
    room_metadata: dict[str, object],
    settings: Settings,
    job_logger,
) -> str:
    """Construye las instrucciones del agente a partir de metadata y settings."""
    raw_prompt = room_metadata.get("agent_prompt")
    if raw_prompt and isinstance(raw_prompt, str):
        custom_prompt = _sanitize_custom_prompt(raw_prompt, settings.max_custom_prompt_chars)
        job_logger.info("Using custom prompt", extra={"length": len(custom_prompt)})
    else:
        custom_prompt = get_system_prompt()
        job_logger.info("Using clinical prompt")

    caps_block = get_capabilities_block()

    if not settings.llm_apply_token_limits:
        instructions = custom_prompt + "\n\n" + caps_block.strip()
        job_logger.info(
            "Instruction prompt built without token budget",
            extra={"approx_prompt_tokens": estimate_tokens(instructions)},
        )
        return instructions

    total_tokens = settings.llm_max_input_tokens
    instructions, budget_meta = compose_budgeted_text(
        [
            BudgetSection(
                name="custom_prompt",
                text=custom_prompt,
                required=True,
                max_tokens=max(28, total_tokens - 20),
                min_tokens=max(18, total_tokens // 2),
                trim_priority=20,
            ),
            BudgetSection(
                name="capabilities_block",
                text=caps_block,
                required=True,
                min_tokens=estimate_tokens(caps_block),
                trim_priority=10,
            ),
        ],
        total_tokens=total_tokens,
    )
    approx_tokens = estimate_tokens(instructions)
    if budget_meta["truncated_sections"] or budget_meta["hard_truncated"]:
        job_logger.warning(
            "Instruction prompt truncated to fit budget",
            extra={
                "approx_prompt_tokens": approx_tokens,
                "input_budget_tokens": settings.llm_max_input_tokens,
                "truncated_sections": budget_meta["truncated_sections"],
                "dropped_sections": budget_meta["dropped_sections"],
                "hard_truncated": budget_meta["hard_truncated"],
            },
        )
    else:
        job_logger.info(
            "Instruction prompt budgeted",
            extra={
                "approx_prompt_tokens": approx_tokens,
                "input_budget_tokens": settings.llm_max_input_tokens,
            },
        )
    return instructions


async def send_initial_greeting(
    session: AgentSession,
    settings: Settings,
    room_metadata: dict[str, object],
    job_logger,
) -> None:
    """Envía el saludo inicial tras el delay configurado."""
    if not settings.greeting_enabled:
        return
    await asyncio.sleep(settings.greeting_delay)
    raw_greeting = room_metadata.get("greeting")
    if raw_greeting and isinstance(raw_greeting, str):
        greeting_text = _sanitize_custom_prompt(raw_greeting, settings.max_custom_prompt_chars)
    else:
        greeting_text = get_greeting()
    job_logger.info("Sending initial greeting")
    try:
        await session.say(greeting_text)
    except Exception as e:
        job_logger.error("Failed to send greeting", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="greeting").inc()


_INJECTION_PATTERNS = re.compile(
    r"(^|\n)\s*(SYSTEM\s*:|ASSISTANT\s*:|<\|im_start\|>|<\|system\|>|\[INST\])",
    re.IGNORECASE,
)


def _sanitize_custom_prompt(prompt: str, max_chars: int) -> str:
    """Trunca, elimina bytes de control y filtra patrones de inyección."""
    prompt = prompt.strip()[:max_chars]
    prompt = "".join(c for c in prompt if c >= " " or c in "\n\t")
    return _INJECTION_PATTERNS.sub("", prompt)
