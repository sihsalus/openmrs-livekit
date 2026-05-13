"""Shared fixtures for Nebu agent tests."""

from dataclasses import dataclass, field
from unittest.mock import AsyncMock

import pytest


# ── Environment: set dummy env vars so Settings() doesn't fail ──────────────
@pytest.fixture(autouse=True)
def _env_defaults(monkeypatch):
    """Provide required env vars for any test that imports Settings."""
    defaults = {
        "LIVEKIT_URL": "ws://localhost:7880",
        "LIVEKIT_API_KEY": "test-key",
        "LIVEKIT_API_SECRET": "test-secret",
        "OPENAI_API_KEY": "sk-test",
        "ELEVENLABS_API_KEY": "el-test",
        "INWORLD_API_KEY": "iw-test",
        "DEEPGRAM_API_KEY": "dg-test",
    }
    for k, v in defaults.items():
        monkeypatch.setenv(k, v)


# ── Mock RunContext for @function_tool tests ────────────────────────────────
@dataclass
class FakeAgent:
    """Minimal mock of livekit Agent with update_instructions."""

    instructions: str = ""
    update_instructions: AsyncMock = field(default_factory=AsyncMock)


@dataclass
class FakeSession:
    """Minimal mock of AgentSession."""

    userdata: dict = field(default_factory=dict)
    current_agent: FakeAgent = field(default_factory=FakeAgent)


class FakeRunContext:
    """Minimal mock of livekit RunContext passed to @function_tool functions."""

    def __init__(self, userdata: dict | None = None, instructions: str = ""):
        self.session = FakeSession(
            userdata=userdata or {},
            current_agent=FakeAgent(instructions=instructions),
        )

    @property
    def userdata(self):
        return self.session.userdata


@pytest.fixture
def fake_context():
    """Create a FakeRunContext with a VarietyEngine pre-loaded."""
    from src.variety import VarietyEngine

    base = "Base instructions for testing."
    ctx = FakeRunContext(
        userdata={
            "variety": VarietyEngine(),
            "base_instructions": base,
        },
        instructions=base,
    )
    return ctx
