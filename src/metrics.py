"""
Métricas Prometheus para el agente Nebu.

Singleton — importar y usar directamente:
    from src.metrics import ACTIVE_SESSIONS, SESSIONS_TOTAL, ...
"""

from prometheus_client import Counter, Gauge, Histogram

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
