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
    openai_model: str = Field(default="gpt-4.1", description="Modelo de OpenAI para LLM")
    openai_stt_model: str = Field(default="gpt-4o-transcribe", description="Modelo STT")

    # ============= TTS Configuration =============
    tts_provider: Literal["elevenlabs", "openai", "cartesia", "google", "deepgram", "inworld"] = Field(
        default="inworld", description="Proveedor de TTS"
    )
    elevenlabs_api_key: str | None = Field(default=None, description="API Key de ElevenLabs")
    voice_id: str = Field(default="wnQAQM2xwHFeVXM7PQOq", description="Voice ID (ElevenLabs)")
    openai_tts_voice: str = Field(default="nova", description="Voz de OpenAI TTS (alloy, echo, fable, onyx, nova, shimmer)")
    openai_tts_model: str = Field(default="tts-1", description="Modelo OpenAI TTS (tts-1, tts-1-hd)")
    cartesia_api_key: str | None = Field(default=None, description="API Key de Cartesia")
    cartesia_voice_id: str = Field(
        default="ccfea4bf-b3f4-421e-87ed-dd05dae01431",
        description="Voice ID de Cartesia (default: Alondra - Reassuring Sister)",
    )
    cartesia_model: str = Field(default="sonic-2", description="Modelo Cartesia (sonic-2, sonic-3)")
    google_credentials_file: str | None = Field(default=None, description="Path a credenciales Google")

    # ============= Inworld Configuration =============
    inworld_api_key: str | None = Field(default=None, description="API Key de Inworld")
    inworld_voice_id: str = Field(
        default="default-oklrorszoxbwzfdj8zjhng__nebucherry",
        description="Voice ID de Inworld (voz clonada NEBUCherry)"
    )
    inworld_model: str = Field(
        default="inworld-tts-1.5-max",
        description="Modelo Inworld (inworld-tts-1, inworld-tts-1.5-max)"
    )
    inworld_speaking_rate: float = Field(
        default=1.0,
        description="Velocidad de habla Inworld (0.5-1.5, 1.0 = normal)"
    )
    inworld_temperature: float = Field(
        default=1.1,
        description="Temperatura Inworld (0-2, controla variabilidad emocional)"
    )

    # ============= Deepgram Configuration (Optional) =============
    deepgram_api_key: str | None = Field(default=None, description="API Key Deepgram")

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

    # ============= VAD Settings =============
    vad_min_silence_duration: float = Field(default=0.5, description="Silencio mínimo")
    vad_threshold: float = Field(default=0.5, description="Threshold VAD (0.0-1.0)")

    # ============= Session Settings =============
    allow_interruptions: bool = Field(default=True, description="Permitir interrupciones")
    greeting_enabled: bool = Field(default=True, description="Habilitar saludo inicial")

    # ============= API Settings =============
    api_enabled: bool = Field(default=True, description="Habilitar API REST")
    api_host: str = Field(default="0.0.0.0", description="Host del servidor API")
    api_port: int = Field(default=8000, description="Puerto del servidor API")
    api_key: str | None = Field(default=None, description="API key para endpoints protegidos")
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "https://api.flow-telligence.com",
            "http://localhost:3000",
            "http://localhost:8000",
        ],
        description="Lista de orígenes permitidos para CORS",
    )
    @field_validator("vad_threshold")
    @classmethod
    def validate_vad_threshold(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("vad_threshold debe estar entre 0.0 y 1.0")
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


# Singleton
_settings: Settings | None = None


def get_settings(reload: bool = False) -> Settings:
    """Obtiene la instancia de configuración (singleton)"""
    global _settings
    if _settings is None or reload:
        _settings = Settings()
    return _settings


def reset_settings():
    """Resetea el singleton (útil para testing)"""
    global _settings
    _settings = None
