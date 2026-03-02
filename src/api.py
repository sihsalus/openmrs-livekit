"""
API REST Module - Expone endpoints HTTP para el agente
"""

import asyncio
import traceback
from typing import Dict, Any
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.logger import get_logger
from src.health_check import HealthChecker


logger = get_logger("nebu.api")

# Instancia global del health checker
_health_checker: HealthChecker = None


def get_health_checker() -> HealthChecker:
    """Obtiene la instancia del health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-Api-Key")):
    """Valida la API key si está configurada"""
    settings = get_settings()
    if settings.api_key is None:
        return True
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager para la aplicación FastAPI"""
    # Startup
    logger.info("Iniciando API REST")
    health_checker = get_health_checker()
    
    # Ejecutar health checks iniciales
    health_status = await health_checker.run_all_checks()
    logger.info(f"Initial health check: {health_status['status']}")
    
    yield
    
    # Shutdown
    logger.info("Apagando API REST")


def create_app() -> FastAPI:
    """Crea la aplicación FastAPI"""
    app = FastAPI(
        title="Nebu Agent API",
        description="API REST para el Agente de voz Nebu",
        version="2.0.0",
        lifespan=lifespan,
    )

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"]
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Captura excepciones no manejadas, las reporta a Sentry y retorna 500"""
        sentry_sdk.capture_exception(exc)
        logger.error(
            "Unhandled exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @app.get("/health", tags=["Health"])
    async def health_check() -> Dict[str, Any]:
        """
        Health check endpoint
        
        Retorna el estado de salud del agente sin ejecutar checks
        (respuesta más rápida)
        """
        health_checker = get_health_checker()
        return health_checker.get_health_status()

    @app.get("/health/full", tags=["Health"])
    async def health_check_full() -> Dict[str, Any]:
        """
        Health check completo endpoint
        
        Ejecuta todos los checks de salud y retorna resultados detallados.
        Puede ser más lento que /health
        """
        health_checker = get_health_checker()
        return await health_checker.run_all_checks()

    @app.get("/ready", tags=["Health"])
    async def readiness_check() -> Response:
        """
        Readiness check endpoint (Kubernetes-style)
        
        Retorna 200 OK si el agente está listo, 503 si no
        """
        health_checker = get_health_checker()
        status = health_checker.get_health_status()
        
        if status["status"] == "healthy":
            return JSONResponse(
                status_code=200,
                content={"ready": True, "status": status["status"]}
            )
        else:
            return JSONResponse(
                status_code=503,
                content={"ready": False, "status": status["status"]}
            )

    @app.get("/alive", tags=["Health"])
    async def liveness_check() -> Response:
        """
        Liveness check endpoint (Kubernetes-style)
        
        Retorna 200 OK si el agente está ejecutándose
        """
        health_checker = get_health_checker()
        status = health_checker.get_health_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "alive": True,
                "uptime_seconds": status["uptime_seconds"],
                "version": status["version"],
            }
        )

    @app.get("/info", tags=["System"])
    async def system_info(auth=Depends(require_api_key)) -> Dict[str, Any]:
        """
        System information endpoint
        
        Retorna información general del sistema
        """
        settings = get_settings()
        health_checker = get_health_checker()
        status = health_checker.get_health_status()
        
        return {
            "agent_name": settings.agent_name,
            "version": "2.0.0",
            "log_level": settings.log_level,
            "health_status": status["status"],
            "uptime_seconds": status["uptime_seconds"],
        }

    return app


# Instancia de la aplicación
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    logger.info(f"Iniciando servidor en {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
