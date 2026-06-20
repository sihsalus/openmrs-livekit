"""
OpenMRS LiveKit Agent — entry point principal.

Responsabilidades de este módulo:
- main() y _entrypoint(): orquestación del ciclo de vida del agente.
- start_metrics_server(): servidor HTTP para /metrics de Prometheus.
- Precarga de modelos (silero VAD).

La lógica de sesión, eventos y transcripts está en session.py, events.py, transcript.py.
"""

from __future__ import annotations

import asyncio
import atexit
import functools
import time
from typing import Any

from livekit import agents, rtc
from livekit.agents import Agent
from livekit.agents.voice.room_io import AudioOutputOptions, RoomOptions
from livekit.plugins import silero

from src.backend_client import close_session as _close_backend_session
from src.config import AGENT_VERSION, Settings
from src.events import AGENT_ROOM_PREFIX, setup_event_listeners
from src.logger import get_logger, setup_logging
from src.metrics import (
    ACTIVE_SESSIONS,
    AGENT_INFO,
    ERRORS_TOTAL,
    SESSION_DURATION,
    SESSIONS_TOTAL,
)
from src.session import (
    NebuAgent,
    TranscriptFlag,
    TurnContext,
    build_instructions,
    parse_room_metadata,
    send_initial_greeting,
)
from src.tools import get_tools

logger = get_logger("nebu.agent")


def _prewarm_models(proc: agents.JobProcess) -> None:
    """Precarga de modelos — top-level para ser picklable por forkserver."""
    silero.VAD.load()
    logger.info("Models preloaded: Silero VAD")


async def _entrypoint(ctx: agents.JobContext, settings: Settings) -> None:
    """Entrypoint del agente."""
    room_name = ctx.room.name if ctx.room else ""
    session_id = f"{room_name}_{int(time.time())}"
    job_logger = logger.with_context(
        job_id=ctx.job.id if ctx.job else "unknown",
        room=room_name,
        session_id=session_id,
    )
    job_logger.info("Starting agent entrypoint")

    if not room_name.startswith(AGENT_ROOM_PREFIX):
        job_logger.info(
            "Room ignored - not an agent room",
            extra={"room": room_name, "reason": "prefix_filter"},
        )
        return

    try:
        await ctx.connect()
    except Exception as e:
        job_logger.error("Failed to connect to room", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="connect").inc()
        return
    job_logger.info("Connected to room", extra={"room": ctx.room.name})

    room_metadata = parse_room_metadata(ctx, job_logger)

    instructions = build_instructions(room_metadata, settings, job_logger)
    turn_context = TurnContext()

    nebu = NebuAgent(settings)
    try:
        session = await nebu.create_session(
            instructions,
            job_logger=job_logger,
            turn_context=turn_context,
        )
    except Exception as e:
        job_logger.error("Failed to create session", extra={"error": str(e)}, exc_info=True)
        ERRORS_TOTAL.labels(type="session").inc()
        return

    session.userdata["base_instructions"] = instructions
    session.userdata["settings"] = settings
    session.userdata["room"] = ctx.room

    transcript_sent = TranscriptFlag()
    _register_session_lifecycle(ctx, session, room_name, job_logger, transcript_sent)

    agent = Agent(instructions=instructions, tools=get_tools(settings))
    setup_event_listeners(
        session, ctx.room, room_name, settings, turn_context, job_logger, transcript_sent
    )

    room_options = RoomOptions(
        audio_output=AudioOutputOptions(
            track_publish_options=rtc.TrackPublishOptions(
                source=rtc.TrackSource.SOURCE_MICROPHONE,
                red=True,
                dtx=False,
            )
        )
    )

    try:
        await session.start(room=ctx.room, agent=agent, room_options=room_options)
    except Exception as e:
        job_logger.error("Failed to start voice session", extra={"error": str(e)}, exc_info=True)
        return
    job_logger.info("Session started and listening")

    await send_initial_greeting(session, settings, room_metadata, job_logger)

    _setup_budget_timer(ctx, session, settings, room_metadata, job_logger)

    job_logger.info("Agent active and listening")


def _register_session_lifecycle(
    ctx: agents.JobContext,
    session: agents.AgentSession[Any],
    room_name: str,
    job_logger: Any,
    transcript_sent: TranscriptFlag,
) -> None:
    """Registra métricas de sesión activa y callback de cierre para transcript."""
    from src.transcript import save_transcript

    session_start = time.time()
    ACTIVE_SESSIONS.inc()
    SESSIONS_TOTAL.labels(personality="clinical").inc()

    async def _on_session_end() -> None:
        ACTIVE_SESSIONS.dec()
        SESSION_DURATION.observe(time.time() - session_start)
        settings: Settings = session.userdata.get("settings")
        if not transcript_sent.done and settings:
            transcript_sent.done = True
            await save_transcript(session, room_name, settings, job_logger)

    ctx.add_shutdown_callback(_on_session_end)


def _setup_budget_timer(
    ctx: agents.JobContext,
    session: agents.AgentSession[Any],
    settings: Settings,
    room_metadata: dict[str, object],
    job_logger: Any,
) -> None:
    """Configura el timer de budget: avisa y desconecta cuando se acaba el tiempo."""
    budget_minutes = room_metadata.get("budget_minutes")
    if not budget_minutes or not isinstance(budget_minutes, (int, float)) or budget_minutes <= 0:
        return

    job_logger.info("Session budget set", extra={"budget_minutes": budget_minutes})

    async def _budget_timer() -> None:
        warn_sec = settings.budget_warning_seconds
        warning_at = max(0, (int(budget_minutes) * 60) - warn_sec)
        await asyncio.sleep(warning_at)
        try:
            await session.say("Nos queda aproximadamente un minuto. ¿Algo más que registrar?")
        except Exception:
            job_logger.debug("Budget warning say failed", exc_info=True)
        await asyncio.sleep(warn_sec)
        job_logger.info("Budget exhausted, disconnecting")
        try:
            await session.say("Se acabó el tiempo de la sesión. Guardando el borrador.")
        except Exception:
            job_logger.debug("Budget goodbye say failed", exc_info=True)
        await asyncio.sleep(5)
        ctx.shutdown()

    budget_task = asyncio.create_task(_budget_timer())

    async def _cancel_budget_task() -> None:
        budget_task.cancel()

    ctx.add_shutdown_callback(_cancel_budget_task)


def make_entrypoint(settings: Settings) -> functools.partial[Any]:
    """Devuelve el entrypoint del agente picklable via functools.partial."""
    return functools.partial(_entrypoint, settings=settings)


def start_metrics_server(settings: Settings) -> None:
    """Start threaded HTTP server for /metrics."""
    if not settings.api_enabled:
        logger.info("Metrics server disabled (API_ENABLED=false)")
        return

    import threading
    from socketserver import ThreadingMixIn
    from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

    from prometheus_client import make_wsgi_app

    class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        daemon_threads = True

    class _SilentHandler(WSGIRequestHandler):
        def log_message(self, *_):  # type: ignore[no-untyped-def]
            pass

    app = make_wsgi_app()
    httpd = make_server(
        "0.0.0.0",
        settings.api_port,
        app,
        server_class=_ThreadingWSGIServer,
        handler_class=_SilentHandler,
    )
    thread = threading.Thread(target=httpd.serve_forever, name="metrics-server", daemon=True)
    thread.start()
    logger.info("Metrics server started", extra={"port": settings.api_port})


def main() -> None:
    """Función principal para ejecutar el agente."""
    settings = Settings()  # type: ignore[call-arg]  # pydantic loads from env
    setup_logging(settings)

    logger.info(
        "Starting OpenMRS LiveKit Agent",
        extra={
            "version": AGENT_VERSION,
            "log_level": settings.log_level,
            "tts_provider": settings.tts_provider,
        },
    )

    if settings.log_format == "text":
        logger.info(settings.display_config())

    AGENT_INFO.info(
        {
            "version": AGENT_VERSION,
            "agent_name": "clinical",
            "tts_provider": settings.tts_provider,
            "stt_provider": settings.stt_provider,
            "log_level": settings.log_level,
        }
    )

    start_metrics_server(settings)

    def _shutdown_backend() -> None:
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_close_backend_session())
            loop.close()
        except Exception:
            pass

    atexit.register(_shutdown_backend)

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=make_entrypoint(settings),
            prewarm_fnc=_prewarm_models,
        )
    )


if __name__ == "__main__":
    main()
