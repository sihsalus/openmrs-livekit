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

from livekit import agents, rtc
from livekit.agents import Agent, AgentSession
from livekit.plugins import openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from src.config import Settings, get_settings
from src.logger import get_logger, setup_logging
from src.metrics import (
    ACTIVE_SESSIONS,
    CHILD_SIGNALS_TOTAL,
    ERRORS_TOTAL,
    SESSION_DURATION,
    SESSIONS_TOTAL,
    TURNS_TOTAL,
)
from src.personalities import get_profile
from src.prompts import CAPABILITIES_BLOCK, get_greeting, get_system_prompt
from src.tools import ALL_TOOLS
from src.variety import VarietyEngine

# Setup logging al importar
setup_logging()
logger = get_logger("nebu.agent")
_api_server = None


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

    async def create_session(self, instructions: str) -> AgentSession:
        """Crea una sesión de agente con la configuración actual"""
        return AgentSession(
            turn_detection=MultilingualModel(),
            # VAD optimizado para captura rápida de interrupciones
            vad=silero.VAD.load(
                min_silence_duration=self.settings.vad_min_silence_duration,
                activation_threshold=self.settings.vad_activation_threshold,
                min_speech_duration=self.settings.vad_min_speech_duration,
            ),
            # STT configurable (Deepgram/OpenAI)
            stt=_build_stt(self.settings),
            # LLM
            llm=openai.LLM(
                model=self.settings.openai_model,
                temperature=0.7,
                parallel_tool_calls=False,
            ),
            # TTS configurable
            tts=_build_tts(self.settings),
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


def prewarm_models(proc: agents.JobProcess):
    """Precarga los modelos para mejor rendimiento inicial"""
    silero.VAD.load()
    logger.info("Modelos precargados: Silero VAD")


async def entrypoint(ctx: agents.JobContext):
    """Punto de entrada principal del agente"""
    settings = get_settings()

    # Crear logger con contexto del job
    job_logger = logger.with_context(
        job_id=ctx.job.id if ctx.job else "unknown", room=ctx.room.name if ctx.room else "unknown"
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
    custom_prompt = room_metadata.get("agent_prompt")
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

    # Crear sesión con variety engine y prompt base
    try:
        session = await nebu.create_session(instructions)
    except Exception as e:
        job_logger.error("Error creando sesión", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="session").inc()
        return
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
    job_logger.info("Personality loaded", extra={"profile": profile.id})
    session.userdata["base_instructions"] = instructions

    # Métricas: registrar inicio de sesión
    _session_start = time.time()
    ACTIVE_SESSIONS.inc()
    SESSIONS_TOTAL.labels(personality=profile.id).inc()

    async def _on_session_end():
        ACTIVE_SESSIONS.dec()
        SESSION_DURATION.observe(time.time() - _session_start)

    ctx.add_shutdown_callback(_on_session_end)

    # Crear agente con instrucciones y tools
    agent = Agent(instructions=instructions, tools=ALL_TOOLS)

    # Walkie-talkie mode: pause AI when a parent joins the room
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
        job_logger.info("Participante desconectado", extra={"participant": participant.identity})
        if _is_parent(participant) and not _has_parent_in_room():
            job_logger.info(
                "Padre desconectado - reanudando AI",
                extra={"parent_identity": participant.identity},
            )
            asyncio.create_task(_resume_from_walkie_talkie())

    # ── Event listeners: conectar VarietyEngine al flujo real ──────────
    def on_user_transcribed(ev):
        """Gap 1+3: FSM Mood Lite + Persona Anchor/Sliding Summary."""
        if not ev.is_final:
            return

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

    session.on("user_input_transcribed", on_user_transcribed)
    session.on("conversation_item_added", on_conversation_item)

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

    # Check if a parent is already in the room (joined before agent)
    if _has_parent_in_room():
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
        global _api_server
        if _api_server is not None:
            _api_server.should_exit = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def start_api_server():
    """Inicia el servidor API en un hilo separado si está habilitado"""
    settings = get_settings()
    if not settings.api_enabled:
        logger.info("API REST deshabilitada; no se inicia servidor HTTP")
        return None

    try:
        import uvicorn

        from src.api import app
    except Exception as exc:
        logger.error(f"No se pudo iniciar la API REST: {exc}")
        return None

    config = uvicorn.Config(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, name="api-server", daemon=True)
    thread.start()
    logger.info(
        "API REST iniciada",
        extra={"host": settings.api_host, "port": settings.api_port},
    )
    return server


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

    global _api_server
    _api_server = start_api_server()

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm_models,
        )
    )


if __name__ == "__main__":
    main()
