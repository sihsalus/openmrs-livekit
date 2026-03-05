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
from livekit.plugins import silero

from src.config import Settings
from src.logger import get_logger, setup_logging
from src.providers import build_llm, build_stt, build_tts
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
from src.tools import get_tools
from src.tracing import get_tracer

# Imports condicionales solo si están habilitados (ahorro ~25MB RAM)
# from src.variety import VarietyEngine  # Solo si enable_variety_engine=true
# from src.personalities import get_profile  # Solo si enable_variety_engine=true
# from livekit.plugins.turn_detector.multilingual import MultilingualModel  # Solo si enable_turn_detection=true

logger = get_logger("nebu.agent")


class NebuAgent:
    """Agente Nebu con funcionalidades mejoradas"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session: AgentSession | None = None

    async def create_session(
        self, instructions: str, job_logger=None, turn_detection_model=None
    ) -> AgentSession:
        """Crea una sesión de agente con la configuración actual"""
        # Build components
        stt = build_stt(self.settings)
        llm = build_llm(self.settings)
        tts = build_tts(self.settings)

        # Attach metrics collectors (always active; log only if job_logger provided)
        def llm_metrics_wrapper(metrics: LLMMetrics):
            if job_logger:
                job_logger.info(
                    f"🧠 LLM: TTFT={metrics.ttft:.3f}s, tokens/s={metrics.tokens_per_second:.1f}, "
                    f"prompt_tok={metrics.prompt_tokens}, completion_tok={metrics.completion_tokens}"
                )

        def stt_metrics_wrapper(metrics: STTMetrics):
            if job_logger:
                job_logger.info(
                    f"🎤 STT: duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}"
                )
            STT_DURATION.labels(stt_provider=self.settings.stt_provider).observe(metrics.duration)

        def eou_metrics_wrapper(metrics: EOUMetrics):
            if job_logger:
                job_logger.info(
                    f"⏱️ EOU: eou_delay={metrics.end_of_utterance_delay:.3f}s, transcription_delay={metrics.transcription_delay:.3f}s"
                )
            EOU_DELAY.observe(metrics.end_of_utterance_delay)

        def tts_metrics_wrapper(metrics: TTSMetrics):
            if job_logger:
                job_logger.info(
                    f"🔊 TTS: TTFB={metrics.ttfb:.3f}s, duration={metrics.duration:.3f}s, audio={metrics.audio_duration:.3f}s, streamed={metrics.streamed}"
                )
            TTS_TTFB.labels(tts_provider=self.settings.tts_provider).observe(metrics.ttfb)
            TTS_AUDIO_DURATION.labels(tts_provider=self.settings.tts_provider).observe(metrics.audio_duration)

        llm.on("metrics_collected", llm_metrics_wrapper)
        stt.on("metrics_collected", stt_metrics_wrapper)
        stt.on("eou_metrics_collected", eou_metrics_wrapper)
        tts.on("metrics_collected", tts_metrics_wrapper)

        return AgentSession(
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


def make_prewarm(settings: Settings):
    """Devuelve la función de precarga con settings inyectadas via closure."""

    def prewarm_models(proc: agents.JobProcess):
        silero.VAD.load()
        if settings.enable_turn_detection:
            from livekit.plugins.turn_detector.multilingual import MultilingualModel

            proc.userdata["turn_detection"] = MultilingualModel()
            logger.info("Modelos precargados: Silero VAD + Turn Detection")
        else:
            logger.info("Modelos precargados: Silero VAD")

    return prewarm_models


def make_entrypoint(settings: Settings):
    """Devuelve el entrypoint del agente con settings inyectadas via closure."""

    async def entrypoint(ctx: agents.JobContext):
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

        instructions = custom_prompt + owner_context + CAPABILITIES_BLOCK

        if owner_context:
            job_logger.info("Contexto del owner inyectado en prompt")

        # Crear instancia del agente
        nebu = NebuAgent(settings)

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
        _session_span.set_attribute(
            "session.language", room_metadata.get("preferred_language", "es")
        )

        async def _on_session_end():
            ACTIVE_SESSIONS.dec()
            duration = time.time() - _session_start
            SESSION_DURATION.observe(duration)
            _session_span.set_attribute("session.duration_seconds", duration)
            _session_span.end()

        ctx.add_shutdown_callback(_on_session_end)

        # Crear agente con instrucciones y tools
        agent = Agent(instructions=instructions, tools=get_tools(settings))

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

        # ── Event listeners: conectar VarietyEngine + filler al flujo real ──
        _turn_start: float | None = None
        _filler_task: asyncio.Task | None = None

        def on_user_transcribed(ev):
            """Filler sound + FSM Mood Lite + Persona Anchor/Sliding Summary."""
            nonlocal _turn_start, _filler_task
            if not ev.is_final:
                return

            _turn_start = time.time()

            # Filtro anti-ruido: ignorar transcripciones muy cortas o basura
            text = ev.transcript.strip()
            if len(text) < 4 or not any(c.isalpha() for c in text):
                job_logger.debug("Transcripción descartada (ruido)", extra={"text": text})
                return

            # Filler sound: reproducir "mmm..." si el LLM tarda más de filler_delay
            if settings.filler_sound_enabled:
                if _filler_task and not _filler_task.done():
                    _filler_task.cancel()

                async def _maybe_filler():
                    await asyncio.sleep(settings.filler_delay)
                    try:
                        await session.say(settings.filler_sound_text)
                    except (asyncio.CancelledError, Exception):
                        pass

                _filler_task = asyncio.create_task(_maybe_filler())

            # VarietyEngine — solo si está habilitado
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
            """Gap 2 + latencia: procesa items de asistente en un solo listener."""
            nonlocal _turn_start
            item = ev.item
            if not hasattr(item, "role") or item.role != "assistant":
                return
            # Métrica de latencia LLM
            if _turn_start is not None:
                LLM_LATENCY.labels(personality=profile.id).observe(time.time() - _turn_start)
            # Anti-repetición (solo si VarietyEngine activo)
            text = item.text_content
            if text:
                variety = session.userdata.get("variety")
                if variety:
                    variety.record_agent_response(text)

        def on_speech_created(ev: SpeechCreatedEvent):
            """Cancela el filler si el LLM respondió a tiempo; registra latencia de turno."""
            nonlocal _turn_start, _filler_task
            # Cancelar filler pendiente — el agente ya tiene su respuesta real
            if _filler_task and not _filler_task.done():
                _filler_task.cancel()
                _filler_task = None
            if _turn_start is not None:
                TURN_LATENCY.labels(
                    personality=profile.id, tts_provider=settings.tts_provider
                ).observe(ev.created_at - _turn_start)
                _turn_start = None

        # Registrar listener de transcripción si alguna feature lo necesita
        if settings.enable_variety_engine or settings.filler_sound_enabled:
            session.on("user_input_transcribed", on_user_transcribed)

        # Siempre activo: métricas de latencia + anti-repetición (si variety activo)
        session.on("conversation_item_added", on_conversation_item)
        session.on("speech_created", on_speech_created)

        # Iniciar sesión de voz
        try:
            await session.start(
                room=ctx.room,
                agent=agent,
            )
        except Exception as e:
            job_logger.error(
                "Error iniciando sesión de voz", extra={"error": str(e)}, exc_info=True
            )
            return
        job_logger.info("Sesión iniciada y escuchando")

        # Check if a parent is already in the room (joined before agent) - only if walkie-talkie enabled
        if settings.enable_walkie_talkie and _has_parent_in_room():
            job_logger.info("Padre ya presente en la sala - iniciando en modo walkie-talkie")
            await _pause_for_walkie_talkie()
        else:
            # Enviar greeting inicial
            await asyncio.sleep(settings.greeting_delay)
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
                    job_logger.error(
                        "Error enviando greeting", extra={"error": str(e)}, exc_info=True
                    )
                    ERRORS_TOTAL.labels(type="greeting").inc()

        job_logger.info("Agente activo y escuchando")

    return entrypoint


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
