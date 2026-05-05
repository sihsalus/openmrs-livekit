"""
Tests para src/backend_client.

Cubre la regresión de marzo 2026: aiohttp.ClientSession descartaba el path
del `base_url`, así que el agente pegaba a /voice/... en vez de /api/v1/voice/...
y el backend respondía 404 silenciosamente.
"""

from __future__ import annotations

import socket
from unittest.mock import patch

import pytest
from aiohttp import web

from src.backend_client import _build_url, backend_request, close_session
from src.config import Settings


def _settings(backend_url: str | None, secret: str | None = "test-secret") -> Settings:
    """Construye un Settings con las URL/secret deseadas, sin tocar el .env."""
    return Settings(agent_backend_url=backend_url, agent_internal_secret=secret)


def _free_port() -> int:
    """Reserva un puerto libre para que el servidor de tests no choque."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _Log:
    """Logger mínimo: captura warnings, ignora el resto."""

    def __init__(self) -> None:
        self.warnings: list[str] = []

    def warning(self, msg, *_a, **_kw):
        self.warnings.append(str(msg))

    def debug(self, *_a, **_kw):
        pass

    def info(self, *_a, **_kw):
        pass


# ── _build_url: unidad pequeña que reemplazó al base_url roto ────────────────


def test_build_url_preserves_api_prefix():
    s = _settings("http://localhost:3001/api/v1")
    assert (
        _build_url(s, "voice/sessions/transcript")
        == "http://localhost:3001/api/v1/voice/sessions/transcript"
    )


def test_build_url_strips_redundant_slashes():
    s = _settings("http://localhost:3001/api/v1/")
    assert (
        _build_url(s, "/voice/sessions/transcript")
        == "http://localhost:3001/api/v1/voice/sessions/transcript"
    )


def test_build_url_works_without_prefix():
    s = _settings("http://backend.internal:3001")
    assert (
        _build_url(s, "voice/sessions/transcript")
        == "http://backend.internal:3001/voice/sessions/transcript"
    )


# ── backend_request end-to-end con servidor real ─────────────────────────────


@pytest.fixture
async def cleanup_session():
    """La session aiohttp es singleton — cerrar tras cada test."""
    yield
    await close_session()


async def _start_server(app: web.Application) -> tuple[web.AppRunner, str, int]:
    runner = web.AppRunner(app)
    await runner.setup()
    port = _free_port()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    return runner, "127.0.0.1", port


async def test_backend_request_hits_full_path_with_prefix(cleanup_session):
    """Regresión: con AGENT_BACKEND_URL='.../api/v1', el POST debe llegar a /api/v1/...

    Antes del fix, aiohttp.ClientSession(base_url=...) descartaba el path
    y la request llegaba a /voice/sessions/transcript → 404 silencioso.
    """
    captured: dict = {}

    async def handler(request: web.Request) -> web.Response:
        captured["path"] = request.path
        captured["secret"] = request.headers.get("x-agent-secret")
        captured["body"] = await request.json()
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/api/v1/voice/sessions/transcript", handler)
    runner, host, port = await _start_server(app)
    try:
        settings = _settings(f"http://{host}:{port}/api/v1", secret="abc123")
        result = await backend_request(
            settings,
            "POST",
            "voice/sessions/transcript",
            _Log(),
            json={"roomName": "r1", "transcript": "hola", "messageCount": 1},
            label="save transcript",
        )

        assert result == {"ok": True}
        assert captured["path"] == "/api/v1/voice/sessions/transcript"
        assert captured["secret"] == "abc123"
        assert captured["body"]["roomName"] == "r1"
    finally:
        await runner.cleanup()


async def test_backend_request_returns_none_on_404(cleanup_session):
    """404 debe tratarse como fallo recuperable (None), nunca excepción."""

    async def handler(_request: web.Request) -> web.Response:
        return web.json_response({"error": "Not Found"}, status=404)

    app = web.Application()
    app.router.add_post("/voice/sessions/transcript", handler)
    runner, host, port = await _start_server(app)
    try:
        settings = _settings(f"http://{host}:{port}")
        log = _Log()
        result = await backend_request(
            settings, "POST", "voice/sessions/transcript", log, json={}, label="x"
        )
        assert result is None
        assert any("404" in w for w in log.warnings)
    finally:
        await runner.cleanup()


async def test_backend_request_accepts_empty_200_response(cleanup_session):
    """Endpoints internos pueden responder 200 sin JSON, como save transcript."""

    async def handler(_request: web.Request) -> web.Response:
        return web.Response(status=200)

    app = web.Application()
    app.router.add_post("/api/v1/voice/sessions/transcript", handler)
    runner, host, port = await _start_server(app)
    try:
        settings = _settings(f"http://{host}:{port}/api/v1")
        result = await backend_request(
            settings,
            "POST",
            "voice/sessions/transcript",
            _Log(),
            json={"roomName": "r1", "transcript": "hola", "messageCount": 1},
            label="save transcript",
        )
        assert result == {}
    finally:
        await runner.cleanup()


async def test_backend_request_skips_when_unconfigured():
    """Sin backend_url o sin secret no debe abrir socket ni crashear."""
    settings = _settings(None, secret=None)

    with patch("src.backend_client._get_session") as get_session:
        result = await backend_request(
            settings, "POST", "voice/sessions/transcript", _Log(), json={}
        )
    assert result is None
    get_session.assert_not_called()
