"""
Métricas Prometheus para el agente Nebu.

Singleton — importar y usar directamente:
    from src.metrics import ACTIVE_SESSIONS, SESSIONS_TOTAL, ...
"""

import time

from prometheus_client import Counter, Gauge, Histogram, Info

# Información estática del agente — se llama AGENT_INFO.info({...}) al arrancar
# Expone: nebu_agent_info{version="2.0.0", agent_name="Nebu", tts_provider="inworld", ...} 1.0
AGENT_INFO = Info("nebu_agent", "Nebu agent static configuration info")

# Timestamp de arranque del proceso principal (persiste en multiprocess dir)
AGENT_START_TIME = Gauge(
    "nebu_agent_start_time_seconds",
    "Unix timestamp when the agent main process started",
    multiprocess_mode="liveall",
)
AGENT_START_TIME.set(time.time())

# Sesiones LiveKit activas en este momento
# multiprocess_mode='liveall' — suma solo procesos vivos (correcto para gauges de conteo)
ACTIVE_SESSIONS = Gauge(
    "nebu_agent_active_sessions",
    "Sesiones LiveKit activas ahora mismo",
    multiprocess_mode="liveall",
)

# Total de sesiones iniciadas (por personalidad)
SESSIONS_TOTAL = Counter(
    "nebu_agent_sessions_total",
    "Total de sesiones de voz iniciadas",
    ["personality"],
)

# Duración de sesiones completadas
SESSION_DURATION = Histogram(
    "nebu_agent_session_duration_seconds",
    "Duración de sesiones de voz en segundos",
    buckets=[30, 60, 120, 300, 600, 1200, 1800],
)

# Errores por tipo (connect, session, greeting)
ERRORS_TOTAL = Counter(
    "nebu_agent_errors_total",
    "Errores del agente por tipo",
    ["type"],
)

# Turnos conversacionales procesados (por personalidad)
TURNS_TOTAL = Counter(
    "nebu_agent_turns_total",
    "Turnos conversacionales procesados",
    ["personality"],
)

# Señales detectadas en el input del niño
CHILD_SIGNALS_TOTAL = Counter(
    "nebu_agent_child_signals_total",
    "Señales detectadas en el input del niño",
    ["signal"],
)

# Latencia LLM: desde transcripción final hasta respuesta completa del modelo
# (conversation_item_added con role=assistant)
LLM_LATENCY = Histogram(
    "nebu_agent_llm_latency_seconds",
    "Latencia LLM: desde transcripción final hasta respuesta completa del modelo",
    ["personality"],
    buckets=[0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 5.0],
)

# Latencia de turno percibida: desde transcripción final hasta inicio de audio TTS
# (speech_created — momento en que el niño comenzará a escuchar audio)
TURN_LATENCY = Histogram(
    "nebu_agent_turn_latency_seconds",
    "Latencia de turno percibida: desde transcripción final hasta inicio de audio TTS",
    ["personality", "tts_provider"],
    buckets=[0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 5.0],
)
