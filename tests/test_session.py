import pytest

from src.config import Settings
from src.prompts import get_capabilities_block
from src.session import build_instructions


class DummyLogger:
    def __init__(self):
        self.records: list[tuple[str, str, dict | None]] = []

    def info(self, message, extra=None):
        self.records.append(("info", message, extra))

    def warning(self, message, extra=None):
        self.records.append(("warning", message, extra))


def test_build_instructions_uses_clinical_prompt_by_default():
    settings = Settings(llm_apply_token_limits=False)
    logger = DummyLogger()

    result = build_instructions({}, settings, logger)

    assert "asistente clínico" in result
    assert "record_clinical_fact" in result
    assert get_capabilities_block().strip() in result


def test_build_instructions_respects_custom_prompt():
    settings = Settings(llm_apply_token_limits=False)
    logger = DummyLogger()

    result = build_instructions(
        {"agent_prompt": "Eres un asistente de triaje."},
        settings,
        logger,
    )

    assert "Eres un asistente de triaje" in result
    assert get_capabilities_block().strip() in result


def test_build_instructions_truncates_when_budget_enabled():
    settings = Settings(llm_apply_token_limits=True)
    logger = DummyLogger()
    room_metadata = {"agent_prompt": "REGLAS IMPORTANTES\n" + ("A" * 260)}

    result = build_instructions(room_metadata, settings, logger)

    assert "REGLAS IMPORTANTES" in result
    assert len(result) <= settings.llm_max_input_tokens * 4


def test_legacy_llm_max_tokens_alias_maps_to_output_budget():
    settings = Settings(llm_max_tokens=17)
    assert settings.llm_max_output_tokens == 17


def test_invalid_total_budget_raises():
    with pytest.raises(ValueError, match="llm_max_input_tokens \\+ llm_max_output_tokens"):
        Settings(
            llm_apply_token_limits=True,
            llm_max_input_tokens=110,
            llm_max_output_tokens=20,
            llm_soft_limit_tokens=115,
            llm_hard_limit_tokens=120,
        )
