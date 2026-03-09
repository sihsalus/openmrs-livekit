"""
Nebu Agent — entry point principal.

Responsabilidades de este módulo:
- main() y _entrypoint(): orquestación del ciclo de vida del agente.
- start_metrics_server(): servidor HTTP para /metrics de Prometheus.
- Precarga de modelos (silero VAD, turn detection).

La lógica de sesión, eventos y transcripts está en session.py, events.py, transcript.py.
"""

import functools
import threading
import time

from livekit import agents
from livekit.agents import Agent
from livekit.plugins import silero

from src.config import Settings
from src.events import AGENT_ROOM_PREFIX, setup_event_listeners, setup_walkie_talkie
from src.logger import get_logger, setup_logging
from src.memory import fetch_memory_context
from src.metrics import (
    ACTIVE_SESSIONS,
    AGENT_INFO,
    ERRORS_TOTAL,
    SESSION_DURATION,
    SESSIONS_TOTAL,
)
from src.session import (
    NebuAgent,
    TurnContext,
    build_instructions,
    parse_room_metadata,
    send_initial_greeting,
    setup_variety_engine,
)
from src.tools import get_tools
from src.transcript import save_transcript

logger = get_logger("nebu.agent")


def _prewarm_models(proc: agents.JobProcess, enable_turn_detection: bool):
    """Precarga de modelos — top-level para ser picklable por forkserver."""
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


async def _entrypoint(ctx: agents.JobContext, settings: Settings):
    """Entrypoint del agente — top-level para ser picklable por forkserver."""
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

    room_metadata = parse_room_metadata(ctx, job_logger)

    agent_name = room_metadata.get("toy_name") or settings.agent_name
    job_logger.info("Agent name resolved", extra={"agent_name": agent_name})

    toy_id = room_metadata.get("toy_id")
    memory_context = None
    if toy_id:
        memory_context = await fetch_memory_context(toy_id, settings, job_logger)
    else:
        job_logger.info("No toy_id in metadata, skipping memory fetch")

    instructions = build_instructions(
        room_metadata, settings, job_logger, memory_context=memory_context,
        agent_name=agent_name,
    )
    turn_context = TurnContext()

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

    profile = setup_variety_engine(session, room_metadata, settings, job_logger, agent_name=agent_name)
    session.userdata["base_instructions"] = instructions
    session.userdata["agent_name"] = agent_name

    _session_start = time.time()
    _transcript_sent = {"done": False}
    ACTIVE_SESSIONS.inc()
    SESSIONS_TOTAL.labels(personality=profile.id).inc()

    async def _on_session_end():
        ACTIVE_SESSIONS.dec()
        SESSION_DURATION.observe(time.time() - _session_start)
        if not _transcript_sent["done"]:
            _transcript_sent["done"] = True
            await save_transcript(session, room_name, settings, job_logger)

    ctx.add_shutdown_callback(_on_session_end)

    agent = Agent(instructions=instructions, tools=get_tools(settings))
    has_parent_in_room = setup_walkie_talkie(ctx, session, settings, job_logger)
    setup_event_listeners(
        session, ctx.room, room_name, settings, turn_context, profile, job_logger, _transcript_sent
    )

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
        await send_initial_greeting(session, settings, room_metadata, job_logger, agent_name=agent_name)

    job_logger.info("Agente activo y escuchando")


def make_entrypoint(settings: Settings):
    """Devuelve el entrypoint del agente picklable via functools.partial."""
    return functools.partial(_entrypoint, settings=settings)


def _build_wsgi_app():
    """Build a WSGI app that routes /personalities and /metrics."""
    import json
    import os

    from prometheus_client import CollectorRegistry
    from prometheus_client import multiprocess as prom_mp
    from prometheus_client.exposition import make_wsgi_app

    from src.personalities import REGISTRY

    multiprocess_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    metrics_app = None

    def app(environ, start_response):
        nonlocal metrics_app
        path = environ.get("PATH_INFO", "")

        if path == "/personalities":
            profiles = [
                {"id": p.id, "display_name": p.display_name, "description": p.description}
                for p in REGISTRY.values()
            ]
            body = json.dumps(profiles).encode()
            start_response(
                "200 OK",
                [
                    ("Content-Type", "application/json"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        # /metrics (default)
        if metrics_app is None:
            if multiprocess_dir:
                registry = CollectorRegistry()
                prom_mp.MultiProcessCollector(registry)
            else:
                registry = None
            metrics_app = make_wsgi_app(registry)
        return metrics_app(environ, start_response)

    return app


def start_metrics_server(settings: Settings) -> None:
    """Inicia un servidor HTTP para /metrics y /personalities."""
    if not settings.api_enabled:
        logger.info("Servidor de métricas deshabilitado (API_ENABLED=false)")
        return

    from wsgiref.simple_server import WSGIRequestHandler, make_server

    class _SilentHandler(WSGIRequestHandler):
        def log_message(self, *_):
            pass

    app = _build_wsgi_app()
    httpd = make_server("0.0.0.0", settings.api_port, app, handler_class=_SilentHandler)
    thread = threading.Thread(target=httpd.serve_forever, name="metrics-server", daemon=True)
    thread.start()
    logger.info("Metrics server iniciado", extra={"port": settings.api_port})


def main():
    """Función principal para ejecutar el agente."""
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
        logger.info(settings.display_config())

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
