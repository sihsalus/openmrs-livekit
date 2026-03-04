"""
Utilidades para validar y mostrar la configuración del agente.
"""

import sys
from pathlib import Path

from src.config import get_settings
from src.logger import get_logger, setup_logging


def validate_config() -> bool:
    """
    Valida la configuración y retorna True si es válida.

    Returns:
        bool: True si la configuración es válida, False en caso contrario
    """
    logger = get_logger("config.validator")

    try:
        logger.info("Validando configuración...")
        settings = get_settings()

        # Validar URLs
        if not settings.livekit_url.startswith(("ws://", "wss://")):
            logger.error(
                "LIVEKIT_URL debe comenzar con ws:// o wss://", extra={"url": settings.livekit_url}
            )
            return False

        # Validar longitud de API keys
        if len(settings.livekit_api_key) < 8:
            logger.error("LIVEKIT_API_KEY parece ser inválida (muy corta)")
            return False

        if len(settings.livekit_api_secret) < 8:
            logger.error("LIVEKIT_API_SECRET parece ser inválida (muy corta)")
            return False

        if len(settings.openai_api_key) < 8:
            logger.error("OPENAI_API_KEY parece ser inválida (muy corta)")
            return False

        if len(settings.elevenlabs_api_key) < 8:
            logger.error("ELEVEN_API_KEY parece ser inválida (muy corta)")
            return False

        # Validar voice_id
        if len(settings.voice_id) < 8:
            logger.warning(
                "VOICE_ID parece ser inválido (muy corto)", extra={"voice_id": settings.voice_id}
            )

        logger.info("Configuración válida")
        return True

    except Exception as e:
        logger.error("Error al validar configuración", extra={"error": str(e)}, exc_info=True)
        return False


def display_config_sources():
    """Muestra las fuentes de configuración disponibles"""
    print("\n" + "=" * 60)
    print("📋 FUENTES DE CONFIGURACIÓN")
    print("=" * 60)

    # Verificar .env
    env_path = Path(".env")
    if env_path.exists():
        print(f".env encontrado: {env_path.absolute()}")
    else:
        print("❌ .env no encontrado")

    # Verificar env.example
    env_example = Path("env.example")
    if env_example.exists():
        print("ℹ️  env.example disponible como referencia")

    print("=" * 60)
    print("\nPrioridad de carga:")
    print("  1. Valores por defecto")
    print("  2. livekit.toml ([agent.env])")
    print("  3. Variables de entorno del sistema")
    print("  4. Archivo .env")
    print("\n")


def main():
    """Función principal para CLI"""
    setup_logging()

    print("\n" + "🔍 VALIDADOR DE CONFIGURACIÓN NEBU AGENT" + "\n")

    # Mostrar fuentes
    display_config_sources()

    # Validar configuración
    is_valid = validate_config()

    if is_valid:
        # Mostrar configuración
        settings = get_settings()
        print(settings.display_config())
        sys.exit(0)
    else:
        print("\n❌ La configuración tiene errores. Por favor revisa los logs.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
