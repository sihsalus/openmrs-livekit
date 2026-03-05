"""
Nebu Agent - Agente de voz LiveKit mejorado

Características:
- Greeting automático al conectar
- Manejo de interrupciones
- pERSONALIA
- Eventos de ciclo de vida
- Graceful shutdown
- Logging estructurado
"""

import asyncio
import functools
import json
import threading
import time
from types import SimpleNamespace

import aiohttp

from livekit import agents, rtc
from livekit.agents import Agent, AgentSession, SpeechCreatedEvent
from livekit.agents.metrics import EOUMetrics, LLMMetrics, STTMetrics, TTSMetrics
from livekit.plugins import silero

from src.config import Settings
from src.logger import get_logger, setup_logging
from src.metrics import (
    ACTIVE_SESSIONS,
    AGENT_INFO,
    CHILD_SIGNALS_TOTAL,
    EOU_DELAY,
    ERRORS_TOTAL,
    LLM_LATENCY,
    SESSION_DURATION,
    SESSIONS_TOTAL,
    STT_DURATION,
    TURN_LATENCY,
    TURNS_TOTAL,
    TTS_AUDIO_DURATION,
    TTS_TTFB,
)
from src.prompts import CAPABILITIES_BLOCK, get_greeting, get_system_prompt
from src.providers import build_llm, build_stt, build_tts
from src.tools import get_tools
# Imports condicionales solo si están habilitados (ahorro ~25MB RAM)
# from src.variety import VarietyEngine  # Solo si enable_variety_engine=true
# from src.personalities import get_profile  # Solo si enable_variety_engine=true
# from livekit.plugins.turn_detector.multilingual import MultilingualModel  # Solo si enable_turn_detection=true

logger = get_logger("nebu.agent")

# ── Room & participant naming contracts ────────────────────────────────────────
# These prefixes define which rooms the agent joins and how parents are identified.
# Must match the values used in livekit-client.service.ts (generateVoiceAgentToken,
# generateParentToken) and any frontend/IoT code that creates rooms or identities.
AGENT_ROOM_PREFIX = "iot-device-"
PARENT_IDENTITY_PREFIX = "user-parent-"


class NebuAgent:
    """Agente Nebu con funcionalidades mejoradas"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session: AgentSession | None = None

    async def create_session(
        self, instructions: str, job_logger=None, turn_detection_model=None, turn_context=None
    ) -> AgentSession:
        """Crea una sesión de agente con la configuración actual"""
        # Build components
        stt = build_stt(self.settings)
        llm = build_llm(self.settings)
        tts = build_tts(self.settings)

        # Attach metrics collectors (always active; log only if job_logger provided)
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
            # Incrementar turn_id en EOU — dispara ANTES de STT/LLM/TTS metrics,
            # garantizando que los cuatro eventos de un mismo turno comparten el mismo turn_id.
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
            # VAD optimizado (reducido para menor CPU - evita "inference slower than realtime")
            vad=silero.VAD.load(
                min_silence_duration=self.settings.vad_min_silence_duration,
                activation_threshold=self.settings.vad_activation_threshold,
                min_speech_duration=self.settings.vad_min_speech_duration,
            ),
            stt=stt,
            llm=llm,
            tts=tts,
            userdata={},
            # Session optimizada para interrupciones rápidas
            allow_interruptions=self.settings.allow_interruptions,
            min_interruption_words=self.settings.min_interruption_words,
            min_interruption_duration=self.settings.min_interruption_duration,
            min_endpointing_delay=self.settings.min_endpointing_delay,
            max_endpointing_delay=self.settings.max_endpointing_delay,
            user_away_timeout=self.settings.user_away_timeout,
        )

        # EOUMetrics se emite desde AgentSession (no desde stt), hay que registrar aquí
        session.on("metrics_collected", lambda ev: eou_metrics_wrapper(ev.metrics) if isinstance(ev.metrics, EOUMetrics) else None)

        return session


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


def _prewarm_models(proc: agents.JobProcess, enable_turn_detection: bool):
    """Función de precarga de modelos — debe ser top-level para ser picklable por forkserver."""
    silero.VAD.load()
    if enable_turn_detection:
        from livekit.plugins.turn_detector.multilingual import MultilingualModel

        proc.userdata["turn_detection"] = MultilingualModel()
        logger.info("Modelos precargados: Silero VAD + Turn Detection")
    else:
        logger.info("Modelos precargados: Silero VAD")


def make_prewarm(settings: Settings):
    """Devuelve la función de precarga picklable via functools.partial."""
    return functools.partial(_prewarm_models, enable_turn_detection=settings.enable_turn_detection)


def _parse_room_metadata(ctx: agents.JobContext, job_logger) -> dict:
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


def _build_instructions(room_metadata: dict, settings: Settings, job_logger) -> str:
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


def _setup_variety_engine(
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


def _setup_walkie_talkie(
    ctx: agents.JobContext, session: AgentSession, settings: Settings, job_logger
):
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
            asyncio.create_task(_pause_for_walkie_talkie())

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        job_logger.info("Participante desconectado", extra={"participant": participant.identity})
        if _is_parent(participant) and not _has_parent_in_room():
            job_logger.info(
                "Padre desconectado - reanudando AI",
                extra={"parent_identity": participant.identity},
            )
            asyncio.create_task(_resume_from_walkie_talkie())

    job_logger.info("Walkie-talkie mode enabled")
    return _has_parent_in_room


def _setup_event_listeners(
    session: AgentSession,
    settings: Settings,
    turn_context: dict,
    profile,
    job_logger,
) -> None:
    """Registra listeners: user_input_transcribed, conversation_item_added, speech_created."""
    # Estado compartido entre los tres listeners
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
            extra={"turn_id": turn_context["turn_id"], "transcript_len": len(text)},
        )

        if settings.filler_sound_enabled:
            if _state["filler_task"] and not _state["filler_task"].done():
                _state["filler_task"].cancel()

            async def _maybe_filler():
                await asyncio.sleep(settings.filler_delay)
                try:
                    await session.say(settings.filler_sound_text)
                except (asyncio.CancelledError, Exception):
                    pass

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
            asyncio.create_task(session.current_agent.update_instructions(base + extra))

    def on_conversation_item(ev):
        """Latencia LLM + anti-repetición (si VarietyEngine activo)."""
        item = ev.item
        if not hasattr(item, "role") or item.role != "assistant":
            return
        if _state["turn_start"] is not None:
            LLM_LATENCY.labels(personality=profile.id).observe(
                time.time() - _state["turn_start"]
            )
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
            TURN_LATENCY.labels(
                personality=profile.id, tts_provider=settings.tts_provider
            ).observe(ev.created_at - _state["turn_start"])
            _state["turn_start"] = None

    session.on("user_input_transcribed", on_user_transcribed)
    session.on("conversation_item_added", on_conversation_item)
    session.on("speech_created", on_speech_created)


async def _send_initial_greeting(
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


async def _save_transcript(
    session: AgentSession,
    room_name: str,
    settings: Settings,
    job_logger,
) -> None:
    """Envía el transcript completo al backend en un único HTTP call al cierre de sesión."""
    if not settings.agent_backend_url or not settings.agent_internal_secret:
        return

    try:
        messages = session.chat_ctx.messages
    except Exception:
        return

    lines = []
    for msg in messages:
        role = getattr(msg, "role", None)
        if role == "system":
            continue
        label = "Niño" if role == "user" else "Nebu"
        text = getattr(msg, "text_content", None) or ""
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
                json={"roomName": room_name, "transcript": transcript, "messageCount": message_count},
                headers={"x-agent-secret": settings.agent_internal_secret},
            )
            if resp.status == 200:
                job_logger.info("Transcript guardado", extra={"messages": message_count})
            else:
                body = await resp.text()
                job_logger.warning("Backend rechazó transcript", extra={"status": resp.status, "body": body[:200]})
    except Exception as exc:
        job_logger.warning("Error guardando transcript", extra={"error": str(exc)})


async def _entrypoint(ctx: agents.JobContext, settings: Settings):
    """Entrypoint del agente — función top-level para ser picklable por forkserver."""
    room_name = ctx.room.name if ctx.room else ""
    session_id = f"{room_name}_{int(time.time())}"
    job_logger = logger.with_context(
        job_id=ctx.job.id if ctx.job else "unknown",
        room=room_name,
        session_id=session_id,
    )
    job_logger.info("Iniciando entrypoint del agente")

    if not room_name.startswith(AGENT_ROOM_PREFIX):
        job_logger.info(
            "Sala ignorada - no es para agente",
            extra={"room": room_name, "reason": "prefix_filter"},
        )
        return

    try:
        await ctx.connect()
    except Exception as e:
        job_logger.error("Error conectando al room", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="connect").inc()
        return
    job_logger.info("Conectado al room", extra={"room": ctx.room.name})

    room_metadata = _parse_room_metadata(ctx, job_logger)
    instructions = _build_instructions(room_metadata, settings, job_logger)

    turn_context: dict = {"turn_id": None, "turn_num": 0}
    nebu = NebuAgent(settings)
    prewarmed_td = (
        ctx.proc.userdata.get("turn_detection") if settings.enable_turn_detection else None
    )
    try:
        session = await nebu.create_session(
            instructions,
            job_logger=job_logger,
            turn_detection_model=prewarmed_td,
            turn_context=turn_context,
        )
    except Exception as e:
        job_logger.error("Error creando sesión", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="session").inc()
        return

    profile = _setup_variety_engine(session, room_metadata, settings, job_logger)
    session.userdata["base_instructions"] = instructions

    _session_start = time.time()
    ACTIVE_SESSIONS.inc()
    SESSIONS_TOTAL.labels(personality=profile.id).inc()

    async def _on_session_end():
        ACTIVE_SESSIONS.dec()
        SESSION_DURATION.observe(time.time() - _session_start)
        await _save_transcript(session, room_name, settings, job_logger)

    ctx.add_shutdown_callback(_on_session_end)

    agent = Agent(instructions=instructions, tools=get_tools(settings))
    has_parent_in_room = _setup_walkie_talkie(ctx, session, settings, job_logger)
    _setup_event_listeners(session, settings, turn_context, profile, job_logger)

    try:
        await session.start(room=ctx.room, agent=agent)
    except Exception as e:
        job_logger.error("Error iniciando sesión de voz", extra={"error": str(e)}, exc_info=True)
        return
    job_logger.info("Sesión iniciada y escuchando")

    if has_parent_in_room and has_parent_in_room():
        job_logger.info("Padre ya presente en la sala - iniciando en modo walkie-talkie")
        session.interrupt()
        session.input.set_audio_enabled(False)
        session.output.set_audio_enabled(False)
    else:
        await _send_initial_greeting(session, settings, room_metadata, job_logger)

    job_logger.info("Agente activo y escuchando")


def make_entrypoint(settings: Settings):
    """Devuelve el entrypoint del agente picklable via functools.partial."""
    return functools.partial(_entrypoint, settings=settings)



def start_metrics_server(settings: Settings) -> None:
    """Inicia un servidor HTTP mínimo para el endpoint /metrics de Prometheus.

    Reemplaza FastAPI/uvicorn. Usa wsgiref (stdlib) + prometheus_client.
    Soporta multiprocess mode (PROMETHEUS_MULTIPROC_DIR).
    """
    if not settings.api_enabled:
        logger.info("Servidor de métricas deshabilitado (API_ENABLED=false)")
        return

    import os
    from wsgiref.simple_server import WSGIRequestHandler, make_server

    from prometheus_client import CollectorRegistry
    from prometheus_client import multiprocess as prom_mp
    from prometheus_client.exposition import make_wsgi_app

    multiprocess_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")

    def _metrics_wsgi(environ, start_response):
        if multiprocess_dir:
            registry = CollectorRegistry()
            prom_mp.MultiProcessCollector(registry)
        else:
            registry = None  # usa el registry global por defecto
        return make_wsgi_app(registry)(environ, start_response)

    class _SilentHandler(WSGIRequestHandler):
        def log_message(self, *_):
            pass  # Suprime logs de acceso HTTP en stdout

    httpd = make_server("0.0.0.0", settings.api_port, _metrics_wsgi, handler_class=_SilentHandler)
    thread = threading.Thread(target=httpd.serve_forever, name="metrics-server", daemon=True)
    thread.start()
    logger.info("Metrics server iniciado", extra={"port": settings.api_port})


def main():
    """Función principal para ejecutar el agente"""
    settings = Settings()
    setup_logging(settings)

    logger.info(
        "Iniciando Nebu Agent",
        extra={
            "version": "2.0.0",
            "agent_name": settings.agent_name,
            "log_level": settings.log_level,
            "tts_provider": settings.tts_provider,
        },
    )

    if settings.log_format == "text":
        print(settings.display_config())

    # Publicar info estática en métricas (legible por NestJS vía /metrics)
    AGENT_INFO.info(
        {
            "version": "2.0.0",
            "agent_name": settings.agent_name,
            "tts_provider": settings.tts_provider,
            "stt_provider": settings.stt_provider,
            "log_level": settings.log_level,
        }
    )

    start_metrics_server(settings)

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=make_entrypoint(settings),
            prewarm_fnc=make_prewarm(settings),
        )
    )


if __name__ == "__main__":
    main()
