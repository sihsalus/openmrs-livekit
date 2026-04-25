"""
Factories de proveedores LLM, STT, TTS.

Cada factory lee Settings y retorna la instancia configurada.
Añadir soporte para un nuevo proveedor = un bloque if aquí, sin tocar agent.py.
"""

from livekit.plugins import openai

from src.config import Settings
from src.logger import get_logger

logger = get_logger("nebu.providers")


def _build_with_fallback(
    label: str,
    primary: str,
    fallback_csv: str | None,
    builder,
):
    """Intenta construir con el proveedor primario; si falla, recorre los fallbacks."""
    chain = [primary]
    if fallback_csv:
        chain += [p.strip() for p in fallback_csv.split(",") if p.strip()]

    last_error: Exception | None = None
    for provider in chain:
        try:
            instance = builder(provider)
            if provider != primary:
                logger.warning(
                    f"{label} fallback activo",
                    extra={"using": provider, "primary": primary},
                )
            return instance
        except Exception as e:
            logger.error(f"{label} provider falló", extra={"provider": provider, "error": str(e)})
            last_error = e

    raise ValueError(
        f"Todos los proveedores {label} fallaron. Último error: {last_error}"
    ) from last_error


def _build_llm_provider(provider: str, settings: Settings):
    """Construye una instancia LLM para un proveedor específico."""
    if provider == "openai":
        return openai.LLM(
            model=settings.openai_model,
            temperature=settings.llm_temperature,
            max_completion_tokens=settings.llm_max_output_tokens,
        )

    if provider == "anthropic":
        from livekit.plugins import anthropic

        return anthropic.LLM(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_output_tokens,
        )

    if provider == "groq":
        # Groq es compatible con la API de OpenAI — se usa el plugin de OpenAI con base_url diferente
        return openai.LLM(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=settings.llm_temperature,
            max_completion_tokens=settings.llm_max_output_tokens,
        )

    if provider == "xai":
        # xAI (Grok) también es compatible con la API de OpenAI
        return openai.LLM(
            model=settings.xai_model,
            api_key=settings.xai_api_key,
            base_url="https://api.x.ai/v1",
            temperature=settings.llm_temperature,
            max_completion_tokens=settings.llm_max_output_tokens,
        )

    raise ValueError(f"LLM provider desconocido: {provider}")


def build_llm(settings: Settings):
    """Construye el LLM con fallback automático si el proveedor primario falla."""
    return _build_with_fallback(
        "LLM",
        settings.llm_provider,
        settings.llm_fallback_providers,
        lambda p: _build_llm_provider(p, settings),
    )


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
            profanity_filter=True,
            endpointing_ms=settings.deepgram_endpointing_ms,
        )

    raise ValueError(f"STT provider desconocido: {provider}")


def build_stt(settings: Settings):
    """Construye el STT con fallback automático si el proveedor primario falla."""
    return _build_with_fallback(
        "STT",
        settings.stt_provider,
        settings.stt_fallback_providers,
        lambda p: _build_stt_provider(p, settings),
    )


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
            buffer_char_threshold=settings.inworld_buffer_char_threshold,
            max_buffer_delay_ms=settings.inworld_max_buffer_delay_ms,
        )

    raise ValueError(f"TTS provider desconocido: {provider}")


def build_tts(settings: Settings):
    """Construye el TTS con fallback automático si el proveedor primario falla."""
    return _build_with_fallback(
        "TTS",
        settings.tts_provider,
        settings.tts_fallback_providers,
        lambda p: _build_tts_provider(p, settings),
    )
