"""Tests for local provider configuration (ollama, whisper, piper)."""

import pytest

from src.config import Settings


class TestOllamaConfig:
    def test_ollama_provider_accepted(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            llm_provider="ollama",
            tts_provider="piper",
            stt_provider="whisper",
        )
        assert s.llm_provider == "ollama"
        assert s.active_llm_model == "qwen3:8b"

    def test_ollama_custom_model(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            llm_provider="ollama",
            ollama_model="medgemma:latest",
            tts_provider="piper",
            stt_provider="whisper",
        )
        assert s.active_llm_model == "medgemma:latest"

    def test_ollama_base_url_default(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            llm_provider="ollama",
            tts_provider="piper",
            stt_provider="whisper",
        )
        assert s.ollama_base_url == "http://localhost:11434/v1"


class TestWhisperConfig:
    def test_whisper_provider_accepted(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            stt_provider="whisper",
            llm_provider="ollama",
            tts_provider="piper",
        )
        assert s.stt_provider == "whisper"
        assert s.whisper_model_size == "medium"

    def test_whisper_no_api_key_needed(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            stt_provider="whisper",
            llm_provider="ollama",
            tts_provider="piper",
        )
        assert s.openai_api_key is None
        assert s.deepgram_api_key is None


class TestPiperConfig:
    def test_piper_provider_accepted(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            tts_provider="piper",
            llm_provider="ollama",
            stt_provider="whisper",
        )
        assert s.tts_provider == "piper"
        assert "piper" in s.piper_binary


class TestFullLocalStack:
    def test_all_local_no_api_keys(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
        monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
        monkeypatch.delenv("INWORLD_API_KEY", raising=False)
        s = Settings(
            livekit_url="ws://localhost:7880",
            livekit_api_key="k",
            livekit_api_secret="s",
            llm_provider="ollama",
            stt_provider="whisper",
            tts_provider="piper",
        )
        assert s.llm_provider == "ollama"
        assert s.stt_provider == "whisper"
        assert s.tts_provider == "piper"

    def test_openai_still_requires_key(self):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            Settings(
                livekit_url="ws://localhost:7880",
                livekit_api_key="k",
                livekit_api_secret="s",
                llm_provider="openai",
                openai_api_key=None,
                tts_provider="piper",
                stt_provider="whisper",
            )
