import pytest

from src.config import Settings
from src.prompts import CAPABILITIES_BLOCK
from src.session import build_instructions


class DummyLogger:
    def __init__(self):
        self.records = []

    def info(self, message, extra=None):
        self.records.append(("info", message, extra))

    def warning(self, message, extra=None):
        self.records.append(("warning", message, extra))


def test_build_instructions_truncates_memory_first_when_budget_enabled():
    settings = Settings(llm_apply_token_limits=True)
    logger = DummyLogger()
    room_metadata = {
        "agent_prompt": "REGLAS IMPORTANTES\n" + ("A" * 260),
        "owner_name": "Luna",
        "owner_interests": "astronomia",
    }
    memory_context = "M" * 500

    result = build_instructions(room_metadata, settings, logger, memory_context=memory_context)

    assert "MEMORIA PREVIA" not in result
    assert "REGLAS IMPORTANTES" in result
    assert "CONTEXTO:" in result
    assert "Nombre: Luna" in result
    assert CAPABILITIES_BLOCK.strip() in result
    assert len(result) <= settings.llm_max_input_tokens * 4


def test_build_instructions_no_truncation_when_budget_disabled():
    settings = Settings(llm_apply_token_limits=False)
    logger = DummyLogger()
    room_metadata = {
        "agent_prompt": "REGLAS IMPORTANTES\n" + ("A" * 260),
        "owner_name": "Luna",
        "owner_interests": "astronomia",
    }
    memory_context = "M" * 500

    result = build_instructions(room_metadata, settings, logger, memory_context=memory_context)

    assert "MEMORIA PREVIA" in result
    assert "REGLAS IMPORTANTES" in result
    assert "CONTEXTO:" in result
    assert "Nombre: Luna" in result
    assert CAPABILITIES_BLOCK.strip() in result


def test_legacy_llm_max_tokens_alias_maps_to_output_budget():
    settings = Settings(llm_max_tokens=17)
    assert settings.llm_max_output_tokens == 17


def test_invalid_total_budget_raises():
    with pytest.raises(ValueError, match="llm_max_input_tokens \\+ llm_max_output_tokens"):
        Settings(
            llm_apply_token_limits=True,
            llm_max_input_tokens=110,
            llm_max_output_tokens=20,
            llm_hard_limit_tokens=120,
        )
