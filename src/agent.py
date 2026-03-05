"""
Nebu Agent - Agente de voz LiveKit mejorado

Características:
- Greeting automático al conectar
- Manejo de interrupciones
- Eventos de ciclo de vida
- Graceful shutdown
- Logging estructurado
"""

import asyncio
import json
import signal
import threading
import time
from types import SimpleNamespace

from livekit import agents, rtc
from livekit.agents import Agent, AgentSession, SpeechCreatedEvent
from livekit.agents.metrics import LLMMetrics, STTMetrics, TTSMetrics, EOUMetrics
from livekit.plugins import openai, silero

from src.config import Settings, get_settings
from src.logger import get_logger, setup_logging
from src.metrics import (
    ACTIVE_SESSIONS,
    AGENT_INFO,
    CHILD_SIGNALS_TOTAL,
    ERRORS_TOTAL,
    LLM_LATENCY,
    SESSION_DURATION,
    SESSIONS_TOTAL,
    TURN_LATENCY,
    TURNS_TOTAL,
)
from src.prompts import CAPABILITIES_BLOCK, get_greeting, get_system_prompt
from src.tools import ALL_TOOLS
from src.tracing import get_tracer

# Imports condicionales solo si están habilitados (ahorro ~25MB RAM)
# from src.variety import VarietyEngine  # Solo si enable_variety_engine=true
# from src.personalities import get_profile  # Solo si enable_variety_engine=true
# from livekit.plugins.turn_detector.multilingual import MultilingualModel  # Solo si enable_turn_detection=true

# Setup logging al importar
setup_logging()
logger = get_logger("nebu.agent")


def _build_stt(settings: Settings):
    """Construye el STT según el proveedor configurado."""
    provider = settings.stt_provider

    if provider == "openai":
        return openai.STT(
            model=settings.openai_stt_model,
            language="es",
            noise_reduction_type="far_field",
        )

    if provider == "deepgram":
        from livekit.plugins import deepgram

        return deepgram.STT(
            model=settings.deepgram_model,
            language=settings.deepgram_language,
            interim_results=True,
            smart_format=settings.deepgram_smart_format,
            punctuate=settings.deepgram_punctuate,
            profanity_filter=False,
            endpointing_ms=settings.deepgram_endpointing_ms,
        )

    raise ValueError(f"STT provider desconocido: {provider}")


def _build_tts(settings: Settings):
    """Construye el TTS según el proveedor configurado."""
    provider = settings.tts_provider

    if provider == "openai":
        return openai.TTS(
            voice=settings.openai_tts_voice,
            model=settings.openai_tts_model,
        )

    if provider == "elevenlabs":
        from livekit.plugins import elevenlabs

        return elevenlabs.TTS(
            voice_id=settings.voice_id,
            api_key=settings.elevenlabs_api_key,
            language="es",
        )

    if provider == "cartesia":
        from livekit.plugins import cartesia

        return cartesia.TTS(
            api_key=settings.cartesia_api_key,
            model=settings.cartesia_model,
            voice=settings.cartesia_voice_id,
            language="es",
        )

    if provider == "google":
        from livekit.plugins import google

        return google.TTS(language="es-US")

    if provider == "deepgram":
        from livekit.plugins import deepgram

        return deepgram.TTS(api_key=settings.deepgram_api_key)

    if provider == "inworld":
        from livekit.plugins import inworld

        return inworld.TTS(
            api_key=settings.inworld_api_key,
            voice=settings.inworld_voice_id,
            model=settings.inworld_model,
            speaking_rate=settings.inworld_speaking_rate,
            temperature=settings.inworld_temperature,
        )

    raise ValueError(f"TTS provider desconocido: {provider}")


class NebuAgent:
    """Agente Nebu con funcionalidades mejoradas"""

    def __init__(self):
        self.settings = get_settings()
        self.session: AgentSession | None = None
        self._shutdown_event = asyncio.Event()

    async def create_session(
        self, instructions: str, job_logger=None, turn_detection_model=None
    ) -> AgentSession:
        """Crea una sesión de agente con la configuración actual"""
        # Build components
        stt = _build_stt(self.settings)
        llm = openai.LLM(
            model=self.settings.openai_model,
            temperature=0.6,  # Más directo
            parallel_tool_calls=False,
            max_completion_tokens=200,  # Respuestas cortas para reducir latencia
        )
        tts = _build_tts(self.settings)

        # Attach metrics collectors if logger provided
        if job_logger:

            def llm_metrics_wrapper(metrics: LLMMetrics):
                job_logger.info(
                    f"🧠 LLM: TTFT={metrics.ttft:.3f}s, tokens/s={metrics.tokens_per_second:.1f}, "
                    f"prompt_tok={metrics.prompt_tokens}, completion_tok={metrics.completion_tokens}"
                )

            llm.on("metrics_collected", llm_metrics_wrapper)

            def stt_metrics_wrapper(metrics: STTMetrics):
                job_logger.info(
                    f"🎤 STT: duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}"
                )

            stt.on("metrics_collected", stt_metrics_wrapper)

            def eou_metrics_wrapper(metrics: EOUMetrics):
                job_logger.info(
                    f"⏱️ EOU: eou_delay={metrics.end_of_utterance_delay:.3f}s, transcription_delay={metrics.transcription_delay:.3f}s"
                )

            stt.on("eou_metrics_collected", eou_metrics_wrapper)

            def tts_metrics_wrapper(metrics: TTSMetrics):
                job_logger.info(
                    f"🔊 TTS: TTFB={metrics.ttfb:.3f}s, duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}"
                )

            tts.on("metrics_collected", tts_metrics_wrapper)

        return AgentSession(
            turn_detection=turn_detection_model,
            # VAD optimizado (reducido para menor CPU - evita "inference slower than realtime")
            vad=silero.VAD.load(
                min_silence_duration=0.6,  # Era 0.5 → menos procesamiento
                activation_threshold=0.4,  # Era 0.3 → menos sensible, menos false positives
                min_speech_duration=0.3,  # Era 0.2 → ignora ruidos muy cortos
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
            user_away_timeout=30.0,
        )


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


_MAX_CUSTOM_PROMPT = 4096


def _sanitize_custom_prompt(prompt: str) -> str:
    """Trunca y elimina bytes de control de prompts externos (anti-injection)."""
    prompt = prompt.strip()[:_MAX_CUSTOM_PROMPT]
    return "".join(c for c in prompt if c >= " " or c in "\n\t")


def prewarm_models(proc: agents.JobProcess):
    """Precarga los modelos para mejor rendimiento inicial"""
    silero.VAD.load()
    settings = get_settings()
    if settings.enable_turn_detection:
        from livekit.plugins.turn_detector.multilingual import MultilingualModel

        proc.userdata["turn_detection"] = MultilingualModel()
        logger.info("Modelos precargados: Silero VAD + Turn Detection")
    else:
        logger.info("Modelos precargados: Silero VAD")


async def entrypoint(ctx: agents.JobContext):
    """Punto de entrada principal del agente"""
    settings = get_settings()

    # Crear logger con contexto del job
    job_logger = logger.with_context(
        job_id=ctx.job.id if ctx.job else "unknown",
        room=ctx.room.name if ctx.room else "unknown",
    )

    job_logger.info("Iniciando entrypoint del agente")

    # FILTRO: Solo procesar rooms que NO sean para humano-a-humano
    room_name = ctx.room.name if ctx.room else ""
    if not room_name.startswith("iot-device-"):
        job_logger.info(
            "Sala ignorada - no es para agente",
            extra={"room": room_name, "reason": "prefix_filter"},
        )
        return

    # Conectar al room
    try:
        await ctx.connect()
    except Exception as e:
        job_logger.error("Error conectando al room", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="connect").inc()
        return
    job_logger.info("Conectado al room", extra={"room": ctx.room.name})

    # Leer metadata del room para obtener prompt personalizado
    room_metadata = {}
    metadata_raw = ctx.room.metadata
    if metadata_raw:
        try:
            room_metadata = json.loads(metadata_raw)
            job_logger.info("Metadata parseada", extra={"keys": list(room_metadata.keys())})
        except json.JSONDecodeError as e:
            job_logger.error("Error parseando metadata", extra={"error": str(e)})
    else:
        job_logger.warning("Room metadata vacia")

    # Obtener prompt personalizado desde metadata o usar default
    raw_prompt = room_metadata.get("agent_prompt")
    custom_prompt = _sanitize_custom_prompt(raw_prompt) if raw_prompt else None
    owner_context = _build_owner_context(room_metadata)

    if custom_prompt:
        job_logger.info("Usando prompt personalizado", extra={"length": len(custom_prompt)})
        instructions = custom_prompt + owner_context + CAPABILITIES_BLOCK
    else:
        job_logger.info("Usando prompt por defecto")
        instructions = get_system_prompt()
        if owner_context:
            instructions = instructions.replace(
                CAPABILITIES_BLOCK, owner_context + CAPABILITIES_BLOCK
            )

    if owner_context:
        job_logger.info("Contexto del owner inyectado en prompt")

    # Crear instancia del agente
    nebu = NebuAgent()

    # Crear sesión con variety engine y prompt base (con metrics logger)
    prewarmed_td = (
        ctx.proc.userdata.get("turn_detection") if settings.enable_turn_detection else None
    )
    try:
        session = await nebu.create_session(
            instructions, job_logger=job_logger, turn_detection_model=prewarmed_td
        )
    except Exception as e:
        job_logger.error("Error creando sesión", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="session").inc()
        return
    # Hardcoded simple personality (no module loading)
    profile = SimpleNamespace(id="neutral", name="Neutral")

    # VarietyEngine - solo si está habilitado (import condicional)
    if settings.enable_variety_engine:
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
    else:
        session.userdata["variety"] = None
        job_logger.info("VarietyEngine disabled - using hardcoded neutral profile")
    session.userdata["base_instructions"] = instructions

    # Métricas y tracing: registrar inicio de sesión
    _session_start = time.time()
    ACTIVE_SESSIONS.inc()
    SESSIONS_TOTAL.labels(personality=profile.id).inc()

    tracer = get_tracer()
    _session_span = tracer.start_span("voice_session")
    _session_span.set_attribute("session.room", ctx.room.name if ctx.room else "unknown")
    _session_span.set_attribute("session.personality", profile.id)
    _session_span.set_attribute("session.owner_age", str(room_metadata.get("owner_age", "")))
    _session_span.set_attribute("session.language", room_metadata.get("preferred_language", "es"))

    async def _on_session_end():
        ACTIVE_SESSIONS.dec()
        duration = time.time() - _session_start
        SESSION_DURATION.observe(duration)
        _session_span.set_attribute("session.duration_seconds", duration)
        _session_span.end()

    ctx.add_shutdown_callback(_on_session_end)

    # Crear agente con instrucciones y tools
    agent = Agent(instructions=instructions, tools=ALL_TOOLS)

    # Walkie-talkie mode: pause AI when a parent joins the room (OPTIONAL)
    if settings.enable_walkie_talkie:
        walkie_talkie_active = False

        def _is_parent(participant: rtc.RemoteParticipant) -> bool:
            return participant.identity.startswith("user-parent-")

        def _has_parent_in_room() -> bool:
            for p in ctx.room.remote_participants.values():
                if _is_parent(p):
                    return True
            return False

        async def _pause_for_walkie_talkie():
            nonlocal walkie_talkie_active
            walkie_talkie_active = True
            session.interrupt()
            session.input.set_audio_enabled(False)
            session.output.set_audio_enabled(False)
            job_logger.info("AI pausado - modo walkie-talkie activo")

        async def _resume_from_walkie_talkie():
            nonlocal walkie_talkie_active
            walkie_talkie_active = False
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
            job_logger.info(
                "Participante desconectado", extra={"participant": participant.identity}
            )
            if _is_parent(participant) and not _has_parent_in_room():
                job_logger.info(
                    "Padre desconectado - reanudando AI",
                    extra={"parent_identity": participant.identity},
                )
                asyncio.create_task(_resume_from_walkie_talkie())

        job_logger.info("Walkie-talkie mode enabled")
    else:
        job_logger.info("Walkie-talkie mode disabled")

    # ── Event listeners: conectar VarietyEngine al flujo real ──────────
    _turn_start: float | None = None

    def on_user_transcribed(ev):
        """Gap 1+3: FSM Mood Lite + Persona Anchor/Sliding Summary."""
        nonlocal _turn_start
        if not ev.is_final:
            return

        _turn_start = time.time()

        # Filtro anti-ruido: ignorar transcripciones muy cortas o basura
        text = ev.transcript.strip()
        if len(text) < 4 or not any(c.isalpha() for c in text):
            job_logger.debug("Transcripción descartada (ruido)", extra={"text": text})
            return

        variety = session.userdata.get("variety")
        if not variety:
            return

        # Gap 1: Detectar señal del niño y adaptar mood
        child_signal = variety.detect_child_signal(ev.transcript)
        variety.react_to_signal(child_signal)
        CHILD_SIGNALS_TOTAL.labels(signal=child_signal).inc()

        # Gap 3: Tick conversacional + refresh periódico de instrucciones
        variety.tick()
        TURNS_TOTAL.labels(personality=profile.id).inc()
        anchor = variety.build_persona_anchor()
        summary = variety.build_sliding_summary()
        if anchor or summary:
            base = session.userdata.get("base_instructions", "")
            extra = ""
            if anchor:
                extra += "\n" + anchor
            if summary:
                extra += "\n" + summary
            asyncio.create_task(session.current_agent.update_instructions(base + extra))

    def on_conversation_item(ev):
        """Gap 2: Record what the LLM actually said for anti-repetition."""
        item = ev.item
        if not hasattr(item, "role") or item.role != "assistant":
            return
        text = item.text_content
        if not text:
            return
        variety = session.userdata.get("variety")
        if variety:
            variety.record_agent_response(text)

    def on_conversation_item_for_latency(ev):
        """Record LLM latency from user speech end to assistant item ready."""
        nonlocal _turn_start
        if not hasattr(ev.item, "role") or ev.item.role != "assistant":
            return
        if _turn_start is not None:
            LLM_LATENCY.labels(personality=profile.id).observe(time.time() - _turn_start)

    def on_speech_created(ev: SpeechCreatedEvent):
        """Record full turn latency from user speech end to TTS pipeline start."""
        nonlocal _turn_start
        if _turn_start is not None:
            TURN_LATENCY.labels(personality=profile.id, tts_provider=settings.tts_provider).observe(
                ev.created_at - _turn_start
            )
            _turn_start = None

    # Solo registrar listeners de VarietyEngine si está habilitado (ahorra CPU)
    if settings.enable_variety_engine:
        session.on("user_input_transcribed", on_user_transcribed)
        session.on("conversation_item_added", on_conversation_item)

    # Listeners de métricas siempre activos
    session.on("conversation_item_added", on_conversation_item_for_latency)
    session.on("speech_created", on_speech_created)

    # Iniciar sesión de voz
    try:
        await session.start(
            room=ctx.room,
            agent=agent,
        )
    except Exception as e:
        job_logger.error("Error iniciando sesión de voz", extra={"error": str(e)}, exc_info=True)
        return
    job_logger.info("Sesión iniciada y escuchando")

    # Check if a parent is already in the room (joined before agent) - only if walkie-talkie enabled
    if settings.enable_walkie_talkie and _has_parent_in_room():
        job_logger.info("Padre ya presente en la sala - iniciando en modo walkie-talkie")
        await _pause_for_walkie_talkie()
    else:
        # Enviar greeting inicial
        await asyncio.sleep(0.5)
        if settings.greeting_enabled:
            custom_greeting = room_metadata.get("greeting")
            if custom_greeting:
                greeting_text = custom_greeting
            else:
                greeting_text = get_greeting()

            job_logger.info("Enviando greeting inicial")
            try:
                await session.say(greeting_text)
            except Exception as e:
                job_logger.error("Error enviando greeting", extra={"error": str(e)}, exc_info=True)
                ERRORS_TOTAL.labels(type="greeting").inc()

    job_logger.info("Agente activo y escuchando")


def setup_signal_handlers():
    """Configura handlers para shutdown graceful"""

    def signal_handler(sig, frame):
        logger.info(f"Señal {sig} recibida, iniciando shutdown graceful")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


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
    setup_signal_handlers()
    settings = get_settings()

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
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm_models,
        )
    )


if __name__ == "__main__":
    main()
