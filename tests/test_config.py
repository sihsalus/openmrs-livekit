"""Tests for Settings validation."""

import pytest

from src.config import Settings, reset_settings


@pytest.fixture(autouse=True)
def _reset():
    """Reset singleton between tests."""
    reset_settings()
    yield
    reset_settings()


class TestSettingsDefaults:
    def test_loads_with_required_env_vars(self):
        s = Settings()
        assert s.livekit_url == "ws://localhost:7880"
        assert s.openai_model == "gpt-4o"
        assert s.agent_name == "Nebu"

    def test_greeting_enabled_by_default(self):
        s = Settings()
        assert s.greeting_enabled is True

    def test_api_enabled_by_default(self):
        s = Settings()
        assert s.api_enabled is True


class TestVadValidation:
    def test_valid_threshold(self):
        s = Settings(vad_activation_threshold=0.5)
        assert s.vad_activation_threshold == 0.5

    def test_threshold_zero_is_valid(self):
        s = Settings(vad_activation_threshold=0.0)
        assert s.vad_activation_threshold == 0.0

    def test_threshold_one_is_valid(self):
        s = Settings(vad_activation_threshold=1.0)
        assert s.vad_activation_threshold == 1.0

    def test_threshold_above_one_raises(self):
        with pytest.raises(ValueError, match="vad_activation_threshold"):
            Settings(vad_activation_threshold=1.5)

    def test_threshold_negative_raises(self):
        with pytest.raises(ValueError, match="vad_activation_threshold"):
            Settings(vad_activation_threshold=-0.1)

    def test_silence_duration_positive(self):
        s = Settings(vad_min_silence_duration=0.3)
        assert s.vad_min_silence_duration == 0.3

    def test_silence_duration_zero_raises(self):
        with pytest.raises(ValueError, match="vad_min_silence_duration"):
            Settings(vad_min_silence_duration=0)

    def test_silence_duration_negative_raises(self):
        with pytest.raises(ValueError, match="vad_min_silence_duration"):
            Settings(vad_min_silence_duration=-1)


class TestDisplayConfig:
    def test_display_config_hides_secrets(self):
        s = Settings()
        display = s.display_config()
        assert "sk-test" not in display
        assert "el-test" not in display
        assert "Nebu" in display
