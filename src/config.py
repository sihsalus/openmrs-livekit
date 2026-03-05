"""Configuración centralizada con Pydantic Settings"""

from typing import Literal

from pydantic import Field, field_validator
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

    # ============= OpenAI Configuration =============
    openai_api_key: str = Field(..., description="API Key de OpenAI")
    openai_model: str = Field(default="gpt-4o-mini", description="Modelo de OpenAI para LLM")
    openai_stt_model: str = Field(default="gpt-4o-transcribe", description="Modelo STT")

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
    deepgram_language: str = Field(default="es", description="Idioma para Deepgram STT")
    deepgram_smart_format: bool = Field(
        default=True, description="Habilitar smart formatting en Deepgram"
    )
    deepgram_punctuate: bool = Field(default=True, description="Habilitar puntuación automática")
    deepgram_endpointing_ms: int = Field(
        default=300, description="Milisegundos de silencio para finalizar (200-1000ms)"
    )

    # ============= Web Search Configuration =============
    web_search_provider: Literal["tavily", "brave", "serpapi", "duckduckgo"] | None = Field(
        default=None, description="Proveedor de búsqueda web (None = deshabilitado)"
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

    # ============= VAD Settings (Optimizadas para interrupciones rápidas) =============
    vad_min_silence_duration: float = Field(
        default=0.5, description="Silencio mínimo para considerar fin de habla"
    )
    vad_activation_threshold: float = Field(
        default=0.3, description="Threshold VAD (0.0-1.0) - Más bajo = más sensible"
    )
    vad_min_speech_duration: float = Field(
        default=0.2, description="Duración mínima de habla para activar (evita ruido)"
    )

    # ============= Session Settings (Optimizadas para captura de interrupciones) =============
    allow_interruptions: bool = Field(default=True, description="Permitir interrupciones")
    min_interruption_words: int = Field(
        default=0, description="Palabras mínimas para interrumpir (0 = cualquier sonido)"
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
    greeting_enabled: bool = Field(default=True, description="Habilitar saludo inicial")

    # ============= TTS Fallback =============
    tts_fallback_providers: str = Field(
        default="",
        description="Proveedores TTS de fallback separados por coma si el primario falla (ej: 'cartesia,openai')",
    )

    # ============= API Settings =============
    api_enabled: bool = Field(default=True, description="Habilitar API REST")
    api_port: int = Field(default=8000, description="Puerto del servidor API")

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
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    NEBU AGENT v2.0.0                         ║
╠══════════════════════════════════════════════════════════════╣
║  Agent Name:       {self.agent_name:<40} ║
║  Log Level:        {self.log_level:<40} ║
║  LiveKit URL:      {self.livekit_url:<40} ║
║  OpenAI Model:     {self.openai_model:<40} ║
║  TTS Provider:     {self.tts_provider:<40} ║
║  Voice ID:         {self.voice_id:<40} ║
║  Greeting:         {str(self.greeting_enabled):<40} ║
║  Interruptions:    {str(self.allow_interruptions):<40} ║
╚══════════════════════════════════════════════════════════════╝
"""


