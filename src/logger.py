"""Logger estructurado con soporte JSON para observabilidad"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from src.config import Settings


class JSONFormatter(logging.Formatter):
    """Formatter que produce logs en formato JSON estructurado"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Agregar campos extra si existen
        known_extras = ("room", "participant", "agent_id", "job_id")
        for key in known_extras:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        # Capturar cualquier extra adicional pasado via logger.warning(..., extra={...})
        _builtin = {*logging.LogRecord("", 0, "", 0, "", (), None).__dict__, "message", "asctime"}
        for key, val in record.__dict__.items():
            if key not in _builtin and key not in log_data:
                log_data[key] = val

        # Agregar excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Formatter tradicional con colores para desarrollo"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Construir mensaje base
        msg = f"{color}{timestamp} {record.levelname:8}{self.RESET} {record.name}: {record.getMessage()}"

        # Agregar campos extra
        extras = []
        if hasattr(record, "room"):
            extras.append(f"room={record.room}")
        if hasattr(record, "participant"):
            extras.append(f"participant={record.participant}")
        if hasattr(record, "agent_id"):
            extras.append(f"agent_id={record.agent_id}")

        if extras:
            msg += f" [{', '.join(extras)}]"

        return msg


class AgentLogger(logging.LoggerAdapter):
    """Logger adapter que facilita agregar contexto a los logs"""

    def __init__(self, logger: logging.Logger, extra: dict[str, Any] | None = None):
        super().__init__(logger, extra or {})

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        # Combinar extra del adapter con extra del mensaje
        extra = {**self.extra, **kwargs.pop("extra", {})}
        kwargs["extra"] = extra
        return msg, kwargs

    def with_context(self, **context) -> "AgentLogger":
        """Crea un nuevo logger con contexto adicional"""
        new_extra = {**self.extra, **context}
        return AgentLogger(self.logger, new_extra)


def setup_logging(settings: Settings) -> logging.Logger:
    """Configura el sistema de logging según la configuración"""

    # Crear logger raíz para la aplicación
    logger = logging.getLogger("nebu")
    logger.setLevel(getattr(logging, settings.log_level))

    # Limpiar handlers existentes
    logger.handlers.clear()

    # Crear handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level))

    # Seleccionar formatter según configuración
    if settings.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    # Configurar loggers de librerías externas
    logging.getLogger("livekit").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return logger


def get_logger(name: str = "nebu") -> AgentLogger:
    """Obtiene un logger con el nombre especificado"""
    logger = logging.getLogger(name)
    return AgentLogger(logger)
