"""Tests for Mistral provider integration in build_llm."""

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from src.config import Settings


# ── Fixture: parchea todos los módulos externos que providers.py necesita ────

@pytest.fixture
def livekit_mock():
    """
    Inyecta mocks de livekit y src.logger/metrics en sys.modules antes de
    importar src.providers, que no está disponible en el entorno de test.
    """
    # Mock livekit.plugins.openai
    fake_openai = ModuleType("livekit.plugins.openai")
    fake_openai.LLM = MagicMock()

    fake_plugins = ModuleType("livekit.plugins")
    fake_plugins.openai = fake_openai

    fake_livekit = ModuleType("livekit")
    fake_livekit.plugins = fake_plugins

    # Mock src.logger (usa datetime.UTC que requiere Python 3.11+)
    fake_logger = ModuleType("src.logger")
    fake_logger.get_logger = MagicMock(return_value=MagicMock())

    # Mock src.metrics (puede tener deps externas)
    fake_metrics = ModuleType("src.metrics")
    fake_metrics.ERRORS_TOTAL = MagicMock()

    mocks = {
        "livekit": fake_livekit,
        "livekit.plugins": fake_plugins,
        "livekit.plugins.openai": fake_openai,
        "src.logger": fake_logger,
        "src.metrics": fake_metrics,
    }
    originals = {k: sys.modules.get(k) for k in mocks}

    # Fuerza re-import de providers con los mocks activos
    sys.modules.pop("src.providers", None)
    sys.modules.update(mocks)

    yield fake_openai

    for k, v in originals.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v
    sys.modules.pop("src.providers", None)


@pytest.fixture
def mistral_settings():
    return Settings(llm_provider="mistral", mistral_api_key="mist-test", llm_apply_token_limits=True)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestBuildLlmMistral:
    def test_mistral_uses_openai_plugin_with_mistral_base_url(self, livekit_mock, mistral_settings):
        fake_llm = MagicMock()
        livekit_mock.LLM.return_value = fake_llm

        from src.providers import build_llm
        result = build_llm(mistral_settings)

        assert result is fake_llm
        call_kwargs = livekit_mock.LLM.call_args.kwargs
        assert call_kwargs["base_url"] == "https://api.mistral.ai/v1"
        assert call_kwargs["api_key"] == "mist-test"
        assert call_kwargs["model"] == "ministral-8b-latest"

    def test_mistral_passes_temperature(self, livekit_mock, mistral_settings):
        livekit_mock.LLM.return_value = MagicMock()

        from src.providers import build_llm
        build_llm(mistral_settings)

        call_kwargs = livekit_mock.LLM.call_args.kwargs
        assert call_kwargs["temperature"] == mistral_settings.llm_temperature

    def test_mistral_passes_max_completion_tokens(self, livekit_mock, mistral_settings):
        livekit_mock.LLM.return_value = MagicMock()

        from src.providers import build_llm
        build_llm(mistral_settings)

        call_kwargs = livekit_mock.LLM.call_args.kwargs
        assert call_kwargs["max_completion_tokens"] == mistral_settings.llm_max_output_tokens

    def test_mistral_omits_max_completion_tokens_when_limits_disabled(self, livekit_mock):
        s = Settings(llm_provider="mistral", mistral_api_key="mist-test", llm_apply_token_limits=False)
        livekit_mock.LLM.return_value = MagicMock()

        from src.providers import build_llm
        build_llm(s)

        call_kwargs = livekit_mock.LLM.call_args.kwargs
        assert "max_completion_tokens" not in call_kwargs

    def test_mistral_custom_model(self, livekit_mock):
        s = Settings(
            llm_provider="mistral",
            mistral_api_key="mist-test",
            mistral_model="ministral-3b-latest",
        )
        livekit_mock.LLM.return_value = MagicMock()

        from src.providers import build_llm
        build_llm(s)

        assert livekit_mock.LLM.call_args.kwargs["model"] == "ministral-3b-latest"

    def test_mistral_fallback_activates_on_primary_failure(self, livekit_mock):
        """Si openai falla, el fallback mistral debe activarse."""
        s = Settings(
            llm_provider="openai",
            llm_fallback_providers="mistral",
            mistral_api_key="mist-test",
        )
        call_count = 0

        def fake_llm_cls(**kwargs):
            nonlocal call_count
            call_count += 1
            if kwargs.get("base_url") is None:
                raise RuntimeError("OpenAI down")
            return MagicMock()

        livekit_mock.LLM.side_effect = fake_llm_cls

        from src.providers import build_llm
        result = build_llm(s)

        assert result is not None
        assert call_count == 2  # openai falló + mistral ok

    def test_unknown_provider_raises(self, livekit_mock):
        s = Settings()

        from src.providers import _build_llm_provider
        with pytest.raises(ValueError, match="desconocido"):
            _build_llm_provider("unknown_provider", s)
