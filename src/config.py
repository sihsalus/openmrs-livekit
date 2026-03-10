"""Configuración centralizada con Pydantic Settings"""

from importlib.metadata import PackageNotFoundError, version
from typing import Literal

try:
    AGENT_VERSION = version("nebu-agent")
except PackageNotFoundError:
    AGENT_VERSION = "dev"

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del agente Nebu validada con Pydantic"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============= LiveKit Configuration =============
    livekit_url: str = Field(..., description="WebSocket URL del servidor LiveKit")
    livekit_api_key: str = Field(..., description="API Key de LiveKit")
    livekit_api_secret: str = Field(..., description="API Secret de LiveKit")

    # ============= LLM Configuration =============
    llm_provider: Literal["openai", "anthropic", "groq", "xai"] = Field(
        default="openai", description="Proveedor LLM principal"
    )
    llm_fallback_providers: str = Field(
        default="",
        description="Proveedores LLM de fallback separados por coma (ej: 'anthropic,openai')",
    )

    # ============= OpenAI Configuration =============
    openai_api_key: str = Field(..., description="API Key de OpenAI")
    openai_model: str = Field(default="gpt-4.1-mini", description="Modelo OpenAI para LLM")
    openai_stt_model: str = Field(default="gpt-4o-mini-transcribe", description="Modelo STT")

    # ============= Anthropic Configuration =============
    anthropic_api_key: str | None = Field(default=None, description="API Key de Anthropic")
    anthropic_model: str = Field(
        default="claude-haiku-4-5-20251001",
        description="Modelo Anthropic (claude-haiku-4-5-20251001, claude-sonnet-4-6, claude-opus-4-6)",
    )

    # ============= Groq Configuration =============
    groq_api_key: str | None = Field(default=None, description="API Key de Groq")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Modelo Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant, gemma2-9b-it)",
    )

    # ============= xAI (Grok) Configuration =============
    xai_api_key: str | None = Field(default=None, description="API Key de xAI (platform.x.ai)")
    xai_model: str = Field(
        default="grok-3-mini",
        description="Modelo xAI (grok-3-mini, grok-3, grok-2-1212)",
    )

    # ============= TTS Configuration =============
    tts_provider: Literal["elevenlabs", "openai", "cartesia", "google", "deepgram", "inworld"] = (
        Field(default="inworld", description="Proveedor de TTS")
    )
    elevenlabs_api_key: str | None = Field(default=None, description="API Key de ElevenLabs")
    voice_id: str = Field(default="wnQAQM2xwHFeVXM7PQOq", description="Voice ID (ElevenLabs)")
    openai_tts_voice: str = Field(
        default="nova", description="Voz de OpenAI TTS (alloy, echo, fable, onyx, nova, shimmer)"
    )
    openai_tts_model: str = Field(
        default="tts-1", description="Modelo OpenAI TTS (tts-1, tts-1-hd)"
    )
    cartesia_api_key: str | None = Field(default=None, description="API Key de Cartesia")
    cartesia_voice_id: str = Field(
        default="ccfea4bf-b3f4-421e-87ed-dd05dae01431",
        description="Voice ID de Cartesia (default: Alondra - Reassuring Sister)",
    )
    cartesia_model: str = Field(default="sonic-2", description="Modelo Cartesia (sonic-2, sonic-3)")

    # ============= Inworld Configuration =============
    inworld_api_key: str | None = Field(default=None, description="API Key de Inworld")
    inworld_voice_id: str = Field(
        default="default-oklrorszoxbwzfdj8zjhng__nebucherry",
        description="Voice ID de Inworld (voz clonada NEBUCherry)",
    )
    inworld_model: str = Field(
        default="inworld-tts-1.5-mini",
        description="Modelo Inworld (inworld-tts-1, inworld-tts-1.5-mini, inworld-tts-1.5-max)",
    )
    inworld_speaking_rate: float = Field(
        default=1.0, description="Velocidad de habla Inworld (0.5-1.5, 1.0 = normal)"
    )
    inworld_temperature: float = Field(
        default=1.1, description="Temperatura Inworld (0-2, controla variabilidad emocional)"
    )

    # ============= Deepgram Configuration =============
    deepgram_api_key: str | None = Field(default=None, description="API Key Deepgram")

    # STT Provider
    stt_provider: Literal["openai", "deepgram"] = Field(
        default="deepgram", description="Proveedor de STT"
    )

    # Deepgram STT Settings
    deepgram_model: str = Field(
        default="nova-3", description="Modelo Deepgram (nova-3, nova-2, nova-2-general)"
    )
    deepgram_smart_format: bool = Field(
        default=True, description="Habilitar smart formatting en Deepgram"
    )
    deepgram_punctuate: bool = Field(default=True, description="Habilitar puntuación automática")
    deepgram_endpointing_ms: int = Field(
        default=300, description="Milisegundos de silencio para finalizar (200-1000ms)"
    )
    stt_language: str = Field(
        default="es", description="Idioma para STT (BCP-47 base: 'es', 'en', 'fr', etc.)"
    )
    stt_fallback_providers: str = Field(
        default="",
        description="Proveedores STT de fallback separados por coma si el primario falla (ej: 'openai')",
    )

    # ============= Web Search Configuration =============
    web_search_provider: Literal["tavily", "brave", "serpapi", "duckduckgo", "wikipedia"] | None = (
        Field(default=None, description="Proveedor de búsqueda web (None = deshabilitado)")
    )
    web_search_parental_consent: bool = Field(
        default=False,
        description="COPPA: Consentimiento parental verificado para búsquedas web",
    )
    tavily_api_key: str | None = Field(default=None, description="API Key de Tavily")
    brave_search_api_key: str | None = Field(default=None, description="API Key de Brave Search")
    serpapi_api_key: str | None = Field(default=None, description="API Key de SerpAPI")
    web_search_max_results: int = Field(default=3, description="Máximo de resultados de búsqueda")

    # ============= Agent Settings =============
    agent_name: str = Field(default="Nebu", description="Nombre del agente")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_format: Literal["json", "text"] = Field(default="json")

    # ============= LLM Settings =============
    llm_temperature: float = Field(
        default=0.6,
        description="Temperatura LLM (0.0-2.0) — 0.6 = respuestas directas sin aleatoriedad excesiva",
    )
    llm_max_tokens: int = Field(
        default=500,
        description="Tokens máximos de respuesta — 500 = respuestas completas sin cortes",
    )

    # ============= VAD Settings (Valores optimizados para respuesta rápida) =============
    vad_min_silence_duration: float = Field(
        default=0.5,
        description="Silencio mínimo para considerar fin de habla (segundos) — 0.5 = respuesta rápida",
    )
    vad_activation_threshold: float = Field(
        default=0.5, description="Threshold VAD (0.0-1.0) — 0.5 = balance entre sensibilidad y falsos positivos"
    )
    vad_min_speech_duration: float = Field(
        default=0.1,
        description="Duración mínima de habla para activar (segundos) — 0.1 = detecta habla rápidamente",
    )

    # ============= Session Settings (Optimizadas para captura de interrupciones) =============
    allow_interruptions: bool = Field(default=True, description="Permitir interrupciones")
    min_interruption_words: int = Field(
        default=2, description="Palabras mínimas para interrumpir (2 = evita falsos positivos por eco)"
    )
    min_interruption_duration: float = Field(
        default=0.3, description="Duración mínima para interrumpir (segundos)"
    )
    min_endpointing_delay: float = Field(
        default=0.5, description="Delay mínimo antes de considerar turno completo"
    )
    max_endpointing_delay: float = Field(
        default=2.0, description="Delay máximo para esperar continuación"
    )
    user_away_timeout: float = Field(
        default=30.0, description="Segundos de inactividad antes de considerar al usuario ausente"
    )
    greeting_delay: float = Field(
        default=0.5,
        description="Segundos de espera antes del saludo inicial (da tiempo al audio a estabilizarse)",
    )
    greeting_enabled: bool = Field(default=True, description="Habilitar saludo inicial")
    budget_warning_seconds: int = Field(
        default=60,
        description="Segundos antes del fin del budget para avisar al niño",
    )

    # ============= Language Settings =============
    tts_language: str = Field(
        default="es", description="Idioma para TTS (BCP-47 base: 'es', 'en', 'fr', etc.)"
    )
    tts_google_language: str = Field(
        default="es-US",
        description="Locale BCP-47 completo para Google TTS (ej: 'es-US', 'es-MX', 'en-US')",
    )

    # ============= Filler Sound =============
    filler_sound_enabled: bool = Field(
        default=True, description="Reproducir sonido de 'pensar' mientras el LLM genera respuesta"
    )
    filler_sound_text: str = Field(
        default="mmm...", description="Texto del filler sound (pronunciado por TTS)"
    )
    filler_delay: float = Field(
        default=0.4,
        description="Segundos antes de reproducir el filler — si el LLM responde antes, se cancela",
    )

    # ============= Security =============
    max_custom_prompt_chars: int = Field(
        default=4096,
        description="Tamaño máximo en caracteres para prompts personalizados (anti-injection)",
    )

    # ============= TTS Fallback =============
    tts_fallback_providers: str = Field(
        default="",
        description="Proveedores TTS de fallback separados por coma si el primario falla (ej: 'cartesia,openai')",
    )

    # ============= API Settings =============
    api_enabled: bool = Field(default=True, description="Habilitar API REST")
    api_port: int = Field(default=8000, description="Puerto del servidor API")

    # ============= Backend Integration =============
    agent_backend_url: str | None = Field(
        default=None,
        description="URL interna del backend NestJS (ej: http://localhost:3001/api/v1)",
    )
    agent_internal_secret: str | None = Field(
        default=None, description="Secret compartido para llamadas internas agente→backend"
    )

    # ═══════════════════════════════════════════════════════════════
    # Feature Flags - Optimización para ESP32
    # ═══════════════════════════════════════════════════════════════
    enable_turn_detection: bool = Field(
        default=False,
        description="Enable semantic turn detection model (~20MB RAM overhead)",
    )

    enable_variety_engine: bool = Field(
        default=False,
        description="Enable anti-repetition FSM and sliding context (~10MB RAM overhead)",
    )

    enable_walkie_talkie: bool = Field(
        default=False,
        description="Enable parent pause mode for multi-participant rooms",
    )

    @model_validator(mode="after")
    def validate_provider_api_keys(self) -> "Settings":
        """Falla en startup si el proveedor seleccionado no tiene API key configurada."""
        llm_requirements: dict[str, tuple[str, str]] = {
            "anthropic": ("anthropic_api_key", "ANTHROPIC_API_KEY"),
            "groq": ("groq_api_key", "GROQ_API_KEY"),
            "xai": ("xai_api_key", "XAI_API_KEY"),
        }
        if self.llm_provider in llm_requirements:
            field, env = llm_requirements[self.llm_provider]
            if not getattr(self, field):
                raise ValueError(f"LLM_PROVIDER={self.llm_provider} requiere {env}")

        tts_requirements: dict[str, tuple[str, str]] = {
            "elevenlabs": ("elevenlabs_api_key", "ELEVENLABS_API_KEY"),
            "cartesia": ("cartesia_api_key", "CARTESIA_API_KEY"),
            "inworld": ("inworld_api_key", "INWORLD_API_KEY"),
            "deepgram": ("deepgram_api_key", "DEEPGRAM_API_KEY"),
        }
        if self.tts_provider in tts_requirements:
            field, env = tts_requirements[self.tts_provider]
            if not getattr(self, field):
                raise ValueError(f"TTS_PROVIDER={self.tts_provider} requiere {env}")

        if self.stt_provider == "deepgram" and not self.deepgram_api_key:
            raise ValueError("STT_PROVIDER=deepgram requiere DEEPGRAM_API_KEY")

        return self

    @property
    def active_llm_model(self) -> str:
        """Retorna el modelo del proveedor LLM activo."""
        return {
            "openai": self.openai_model,
            "anthropic": self.anthropic_model,
            "groq": self.groq_model,
            "xai": self.xai_model,
        }.get(self.llm_provider, self.openai_model)

    @field_validator("vad_activation_threshold")
    @classmethod
    def validate_vad_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("vad_activation_threshold debe estar entre 0.0 y 1.0")
        return v

    @field_validator("vad_min_silence_duration")
    @classmethod
    def validate_silence_duration(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("vad_min_silence_duration debe ser mayor que 0")
        return v

    def display_config(self) -> str:
        """Retorna un resumen de la configuración (sin secretos)"""
        v = AGENT_VERSION
        llm_label = f"{self.llm_provider}/{self.active_llm_model}"
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    NEBU AGENT v{v:<29}║
╠══════════════════════════════════════════════════════════════╣
║  Agent Name:       {self.agent_name:<40} ║
║  Log Level:        {self.log_level:<40} ║
║  LiveKit URL:      {self.livekit_url:<40} ║
║  LLM:              {llm_label:<40} ║
║  STT:              {self.stt_provider:<40} ║
║  TTS:              {self.tts_provider:<40} ║
║  Greeting:         {str(self.greeting_enabled):<40} ║
║  Interruptions:    {str(self.allow_interruptions):<40} ║
╚══════════════════════════════════════════════════════════════╝
"""
