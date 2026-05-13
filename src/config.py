"""Configuración centralizada con Pydantic Settings."""

from importlib.metadata import PackageNotFoundError, version
from typing import Any, Literal

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
    llm_provider: Literal["openai", "anthropic", "groq", "xai", "google", "mistral"] = Field(
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
    google_api_key: str | None = Field(
        default=None, description="API Key de Google Gemini (GOOGLE_API_KEY)"
    )
    google_model: str = Field(
        default="gemini-2.5-flash",
        description="Modelo Gemini (gemini-2.5-flash, gemini-2.0-flash-001)",
    )

    # ============= Mistral Configuration =============
    mistral_api_key: str | None = Field(
        default=None, description="API Key de Mistral AI (console.mistral.ai)"
    )
    mistral_model: str = Field(
        default="ministral-8b-latest",
        description="Modelo Mistral (ministral-8b-latest, ministral-3b-latest, mistral-small-latest)",
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
    inworld_buffer_char_threshold: int = Field(
        default=60,
        description="Caracteres mínimos antes de enviar chunk de audio (streaming) — menor = más rápido pero más fragmentado",
    )
    inworld_max_buffer_delay_ms: int = Field(
        default=1500,
        description="Delay máximo en ms antes de forzar envío del buffer — evita esperas largas en frases cortas",
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
        default=25,
        description="Milisegundos de silencio para finalizar — 25ms = default del plugin nova-3, óptimo con turn_detection=stt",
    )
    deepgram_use_flux: bool = Field(
        default=False, description="Usar Deepgram Flux (STTv2) con turn detection semántico"
    )
    deepgram_eot_threshold: float = Field(
        default=0.7, description="Flux: umbral de confianza para EndOfTurn (0.5-0.9)"
    )
    deepgram_eager_eot_threshold: float | None = Field(
        default=None,
        description="Flux: umbral para EagerEndOfTurn — arranca LLM preemptivo 150-250ms antes. None=deshabilitado",
    )
    deepgram_eot_timeout_ms: int = Field(
        default=3000,
        description="Flux: timeout en ms para forzar EndOfTurn si no hay señal del modelo",
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
    llm_apply_token_limits: bool = Field(
        default=True,
        description="Aplicar límites de tokens para prompt/respuesta",
    )
    llm_max_input_tokens: int = Field(
        default=760,
        description="Presupuesto aproximado de tokens de entrada por turno",
    )
    llm_max_output_tokens: int = Field(
        default=120,
        description="Tokens máximos de salida por turno",
    )
    llm_soft_limit_tokens: int = Field(
        default=840,
        description="Presupuesto blando total por turno (entrada + salida)",
    )
    llm_hard_limit_tokens: int = Field(
        default=900,
        description="Límite absoluto total por turno (entrada + salida)",
    )
    llm_max_tokens: int | None = Field(
        default=None,
        description="Alias legacy de llm_max_output_tokens para compatibilidad temporal",
    )

    # ============= VAD Settings (Valores por defecto de LiveKit Silero VAD) =============
    vad_min_silence_duration: float = Field(
        default=0.55,
        description="Silencio mínimo para considerar fin de habla (segundos) — 0.55 = default LiveKit",
    )
    vad_activation_threshold: float = Field(
        default=0.5, description="Threshold VAD (0.0-1.0) — 0.5 = default LiveKit"
    )
    vad_min_speech_duration: float = Field(
        default=0.05,
        description="Duración mínima de habla para activar (segundos) — 0.05 = default LiveKit",
    )

    # ============= Session Settings (Optimizadas según LiveKit docs para Pipeline Agent sin Turn Detector) =============
    allow_interruptions: bool = Field(default=True, description="Permitir interrupciones")
    min_interruption_words: int = Field(
        default=0,
        description="Palabras mínimas para interrumpir (2 = evita falsos positivos por eco)",
    )
    min_interruption_duration: float = Field(
        default=0.5,
        description="Duración mínima para interrumpir (segundos) — 0.5 = default LiveKit",
    )
    min_endpointing_delay: float = Field(
        default=0.5,
        description="Delay antes de considerar turno completo (segundos) — 0.8 = recomendado sin turn detector",
    )
    max_endpointing_delay: float = Field(
        default=0.5, description="Sin turn detector, debe ser igual a min_endpointing_delay"
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
        default=5120,
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
        default=True,
        description="Enable anti-repetition FSM and sliding context (~10MB RAM overhead)",
    )

    enable_walkie_talkie: bool = Field(
        default=False,
        description="Enable parent pause mode for multi-participant rooms",
    )

    enable_content_moderation: bool = Field(
        default=True,
        description="Enable content moderation",
    )

    # ═══════════════════════════════════════════════════════════════
    # Latency Tuning
    # ═══════════════════════════════════════════════════════════════
    turn_detection_mode: Literal["stt", "vad"] = Field(
        default="stt",
        description="Modo de detección de turno: 'stt' delega al endpointing del STT (más rápido), 'vad' usa solo Silero",
    )
    vad_prefix_padding_duration: float = Field(
        default=0.2,
        description="Padding de audio antes del inicio de habla (segundos) — 0.2 reduce latencia vs 0.5 default",
    )

    @model_validator(mode="before")
    @classmethod
    def apply_legacy_llm_aliases(cls, data: Any) -> Any:
        """Mapea aliases legacy antes de validar el modelo."""
        if not isinstance(data, dict):
            return data
        if data.get("llm_max_tokens") is not None and data.get("llm_max_output_tokens") is None:
            data["llm_max_output_tokens"] = data["llm_max_tokens"]
        return data

    @model_validator(mode="after")
    def validate_provider_api_keys(self) -> "Settings":
        """Falla en startup si el proveedor seleccionado no tiene API key configurada."""
        llm_requirements: dict[str, tuple[str, str]] = {
            "anthropic": ("anthropic_api_key", "ANTHROPIC_API_KEY"),
            "groq": ("groq_api_key", "GROQ_API_KEY"),
            "xai": ("xai_api_key", "XAI_API_KEY"),
            "google": ("google_api_key", "GOOGLE_API_KEY"),
            "mistral": ("mistral_api_key", "MISTRAL_API_KEY"),
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

    @model_validator(mode="after")
    def validate_llm_token_budget(self) -> "Settings":
        """Valida coherencia del presupuesto de tokens por turno."""
        if not self.llm_apply_token_limits:
            return self
        if self.llm_max_input_tokens <= 0:
            raise ValueError("llm_max_input_tokens debe ser mayor que 0")
        if self.llm_max_output_tokens <= 0:
            raise ValueError("llm_max_output_tokens debe ser mayor que 0")
        if self.llm_soft_limit_tokens <= 0:
            raise ValueError("llm_soft_limit_tokens debe ser mayor que 0")
        if self.llm_hard_limit_tokens <= 0:
            raise ValueError("llm_hard_limit_tokens debe ser mayor que 0")
        total = self.llm_max_input_tokens + self.llm_max_output_tokens
        if self.llm_soft_limit_tokens > self.llm_hard_limit_tokens:
            raise ValueError("llm_soft_limit_tokens no puede superar llm_hard_limit_tokens")
        if total > self.llm_hard_limit_tokens:
            raise ValueError(
                "llm_max_input_tokens + llm_max_output_tokens no puede superar "
                "llm_hard_limit_tokens"
            )
        return self

    @property
    def active_llm_model(self) -> str:
        """Retorna el modelo del proveedor LLM activo."""
        return {
            "openai": self.openai_model,
            "anthropic": self.anthropic_model,
            "groq": self.groq_model,
            "xai": self.xai_model,
            "google": self.google_model,
            "mistral": self.mistral_model,
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
        budget_mode = "ON" if self.llm_apply_token_limits else "OFF"
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    NEBU AGENT v{v:<29}║
╠══════════════════════════════════════════════════════════════╣
║  Agent Name:       {self.agent_name:<40} ║
║  Log Level:        {self.log_level:<40} ║
║  LiveKit URL:      {self.livekit_url:<40} ║
║  LLM:              {llm_label:<40} ║
    ║  LLM Limits:       {budget_mode:<40} ║
║  LLM Budget:       {f"{self.llm_max_input_tokens}+{self.llm_max_output_tokens} / {self.llm_soft_limit_tokens}-{self.llm_hard_limit_tokens}":<40} ║
║  STT:              {self.stt_provider:<40} ║
║  TTS:              {self.tts_provider:<40} ║
║  Greeting:         {str(self.greeting_enabled):<40} ║
║  Interruptions:    {str(self.allow_interruptions):<40} ║
╚══════════════════════════════════════════════════════════════╝
"""
