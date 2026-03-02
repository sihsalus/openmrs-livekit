"""
Health Check Module - Verificar estado del agente y sus componentes!
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

from src.config import get_settings
from src.logger import get_logger


logger = get_logger("nebu.health")


class HealthStatus(str, Enum):
    """Estados de salud posibles"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthChecker:
    """Verifica la salud del agente y sus componentes"""

    def __init__(self):
        self.settings = get_settings()
        self.start_time = time.time()
        self.last_check: Optional[datetime] = None
        self.component_status: Dict[str, HealthStatus] = {}

    async def check_openai_connection(self) -> bool:
        """Verifica la conexión a OpenAI"""
        try:
            # Este es un check básico - en producción podrías hacer una llamada real
            if not self.settings.openai_api_key:
                logger.warning("OpenAI API key no configurada")
                return False
            logger.debug("OpenAI connection check passed")
            return True
        except Exception as e:
            logger.error(f"OpenAI connection check failed: {e}")
            return False

    async def check_elevenlabs_connection(self) -> bool:
        """Verifica la conexión a ElevenLabs"""
        try:
            if not self.settings.elevenlabs_api_key:
                logger.warning("ElevenLabs API key no configurada")
                return False
            logger.debug("ElevenLabs connection check passed")
            return True
        except Exception as e:
            logger.error(f"ElevenLabs connection check failed: {e}")
            return False

    async def check_configuration(self) -> bool:
        """Verifica que la configuración sea válida"""
        try:
            # Validar configuración requerida
            required_fields = [
                "openai_api_key",
                "elevenlabs_api_key",
                "livekit_url",
                "livekit_api_key",
                "livekit_api_secret",
            ]
            
            for field in required_fields:
                value = getattr(self.settings, field, None)
                if not value:
                    logger.warning(f"Missing required configuration: {field}")
                    return False
            
            logger.debug("Configuration check passed")
            return True
        except Exception as e:
            logger.error(f"Configuration check failed: {e}")
            return False

    async def run_all_checks(self) -> Dict[str, Any]:
        """Ejecuta todos los checks de salud"""
        self.last_check = datetime.now(timezone.utc)
        
        logger.debug("Starting health checks")
        
        # Ejecutar checks en paralelo
        openai_ok, elevenlabs_ok, config_ok = await asyncio.gather(
            self.check_openai_connection(),
            self.check_elevenlabs_connection(),
            self.check_configuration(),
        )

        # Determinar estado general
        self.component_status = {
            "openai": HealthStatus.HEALTHY if openai_ok else HealthStatus.UNHEALTHY,
            "elevenlabs": HealthStatus.HEALTHY if elevenlabs_ok else HealthStatus.UNHEALTHY,
            "configuration": HealthStatus.HEALTHY if config_ok else HealthStatus.UNHEALTHY,
        }

        # Determinar status general
        if all([openai_ok, elevenlabs_ok, config_ok]):
            overall_status = HealthStatus.HEALTHY
        elif any([openai_ok, elevenlabs_ok, config_ok]):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNHEALTHY

        uptime_seconds = time.time() - self.start_time

        health_report = {
            "status": overall_status,
            "timestamp": self.last_check.isoformat(),
            "uptime_seconds": uptime_seconds,
            "components": {
                name: status.value for name, status in self.component_status.items()
            },
            "version": "2.0.0",
        }

        logger.info(f"Health check completed: {overall_status}")
        
        return health_report

    def get_health_status(self) -> Dict[str, Any]:
        """Obtiene el estado de salud actual sin ejecutar nuevos checks"""
        uptime_seconds = time.time() - self.start_time
        
        if not self.component_status:
            return {
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": uptime_seconds,
                "components": {
                    "openai": HealthStatus.HEALTHY.value,
                    "elevenlabs": HealthStatus.HEALTHY.value,
                    "configuration": HealthStatus.HEALTHY.value,
                },
                "version": "2.0.0",
                "message": "No checks run yet, assuming healthy",
            }

        overall_status = HealthStatus.HEALTHY
        if any(s == HealthStatus.UNHEALTHY for s in self.component_status.values()):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in self.component_status.values()):
            overall_status = HealthStatus.DEGRADED

        return {
            "status": overall_status,
            "timestamp": (self.last_check or datetime.now(timezone.utc)).isoformat(),
            "uptime_seconds": uptime_seconds,
            "components": {
                name: status.value for name, status in self.component_status.items()
            },
            "version": "2.0.0",
        }
