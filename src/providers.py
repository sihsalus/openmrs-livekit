"""
Factories de proveedores LLM, STT, TTS.

Cada factory lee Settings y retorna la instancia configurada.
Añadir soporte para un nuevo proveedor = un bloque if aquí, sin tocar agent.py.
"""

from livekit.plugins import openai

from src.config import Settings


def _build_llm_provider(provider: str, settings: Settings):
    """Construye una instancia LLM para un proveedor específico."""
    if provider == "openai":
        return openai.LLM(
            model=settings.openai_model,
            temperature=settings.llm_temperature,
            parallel_tool_calls=False,
            max_completion_tokens=settings.llm_max_tokens,
        )

    if provider == "anthropic":
        from livekit.plugins import anthropic

        return anthropic.LLM(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    if provider == "groq":
        # Groq es compatible con la API de OpenAI — se usa el plugin de OpenAI con base_url diferente
        return openai.LLM(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=settings.llm_temperature,
            max_completion_tokens=settings.llm_max_tokens,
        )

    if provider == "xai":
        # xAI (Grok) también es compatible con la API de OpenAI
        return openai.LLM(
            model=settings.xai_model,
            api_key=settings.xai_api_key,
            base_url="https://api.x.ai/v1",
            temperature=settings.llm_temperature,
            max_completion_tokens=settings.llm_max_tokens,
        )

    raise ValueError(f"LLM provider desconocido: {provider}")


def build_llm(settings: Settings):
    """Construye el LLM con fallback automático si el proveedor primario falla.

    Orden de intento: llm_provider → llm_fallback_providers (comma-separated).
    Registra un warning si se activa el fallback.
    """
    from src.logger import get_logger

    logger = get_logger("nebu.providers")

    chain = [settings.llm_provider]
    if settings.llm_fallback_providers:
        chain += [p.strip() for p in settings.llm_fallback_providers.split(",") if p.strip()]

    last_error: Exception | None = None
    for provider in chain:
        try:
            llm = _build_llm_provider(provider, settings)
            if provider != settings.llm_provider:
                logger.warning(
                    "LLM fallback activo",
                    extra={"using": provider, "primary": settings.llm_provider},
                )
            return llm
        except Exception as e:
            logger.error("LLM provider falló", extra={"provider": provider, "error": str(e)})
            last_error = e

    raise ValueError(
        f"Todos los proveedores LLM fallaron. Último error: {last_error}"
    ) from last_error


def _build_stt_provider(provider: str, settings: Settings):
    """Construye una instancia STT para un proveedor específico."""
    if provider == "openai":
        return openai.STT(
            model=settings.openai_stt_model,
            language=settings.stt_language,
            noise_reduction_type="far_field",
        )

    if provider == "deepgram":
        from livekit.plugins import deepgram

        return deepgram.STT(
            model=settings.deepgram_model,
            language=settings.stt_language,
            interim_results=True,
            smart_format=settings.deepgram_smart_format,
            punctuate=settings.deepgram_punctuate,
            profanity_filter=False,
            endpointing_ms=settings.deepgram_endpointing_ms,
        )

    raise ValueError(f"STT provider desconocido: {provider}")


def build_stt(settings: Settings):
    """Construye el STT con fallback automático si el proveedor primario falla.

    Orden de intento: stt_provider → stt_fallback_providers (comma-separated).
    Registra un warning si se activa el fallback.
    """
    from src.logger import get_logger

    logger = get_logger("nebu.providers")

    chain = [settings.stt_provider]
    if settings.stt_fallback_providers:
        chain += [p.strip() for p in settings.stt_fallback_providers.split(",") if p.strip()]

    last_error: Exception | None = None
    for provider in chain:
        try:
            stt = _build_stt_provider(provider, settings)
            if provider != settings.stt_provider:
                logger.warning(
                    "STT fallback activo",
                    extra={"using": provider, "primary": settings.stt_provider},
                )
            return stt
        except Exception as e:
            logger.error("STT provider falló", extra={"provider": provider, "error": str(e)})
            last_error = e

    raise ValueError(
        f"Todos los proveedores STT fallaron. Último error: {last_error}"
    ) from last_error


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

        return google.TTS(language=settings.tts_google_language)

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

    raise ValueError(
        f"Todos los proveedores TTS fallaron. Último error: {last_error}"
    ) from last_error
