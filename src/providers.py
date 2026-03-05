"""
Factories de proveedores LLM, STT, TTS.

Cada factory lee Settings y retorna la instancia configurada.
Añadir soporte para un nuevo proveedor = un bloque if aquí, sin tocar agent.py.
"""

from livekit.plugins import openai

from src.config import Settings


def build_llm(settings: Settings):
    """Construye el LLM según la configuración."""
    return openai.LLM(
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        parallel_tool_calls=False,
        max_completion_tokens=settings.openai_max_completion_tokens,
    )


def build_stt(settings: Settings):
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


def _build_tts_provider(provider: str, settings: Settings):
    """Construye una instancia TTS para un proveedor específico."""
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
            language=settings.tts_language,
        )

    if provider == "cartesia":
        from livekit.plugins import cartesia

        return cartesia.TTS(
            api_key=settings.cartesia_api_key,
            model=settings.cartesia_model,
            voice=settings.cartesia_voice_id,
            language=settings.tts_language,
        )

    if provider == "google":
        from livekit.plugins import google

        return google.TTS(language=f"{settings.tts_language}-US")

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


def build_tts(settings: Settings):
    """Construye el TTS con fallback automático si el proveedor primario falla.

    Orden de intento: tts_provider → tts_fallback_providers (comma-separated).
    Registra un warning si se activa el fallback.
    """
    from src.logger import get_logger

    logger = get_logger("nebu.providers")

    chain = [settings.tts_provider]
    if settings.tts_fallback_providers:
        chain += [p.strip() for p in settings.tts_fallback_providers.split(",") if p.strip()]

    last_error: Exception | None = None
    for provider in chain:
        try:
            tts = _build_tts_provider(provider, settings)
            if provider != settings.tts_provider:
                logger.warning(
                    "TTS fallback activo",
                    extra={"using": provider, "primary": settings.tts_provider},
                )
            return tts
        except Exception as e:
            logger.error("TTS provider falló", extra={"provider": provider, "error": str(e)})
            last_error = e

    raise ValueError(f"Todos los proveedores TTS fallaron. Último error: {last_error}") from last_error
