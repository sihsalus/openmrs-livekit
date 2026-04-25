"""Tests for all @function_tool implementations."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import Settings
from tests.conftest import FakeRunContext

pytestmark = pytest.mark.asyncio


# ── datetime_tool ────────────────────────────────────────────────────────────


class TestDatetimeTool:
    async def test_returns_spanish_date(self, fake_context):
        from src.tools.datetime_tool import get_current_datetime

        result = await get_current_datetime._func(fake_context, timezone="America/Bogota")
        assert "Hoy es" in result
        assert "horas" in result

    async def test_invalid_timezone_falls_back_to_utc(self, fake_context):
        from src.tools.datetime_tool import get_current_datetime

        result = await get_current_datetime._func(fake_context, timezone="Invalid/Zone")
        assert "Hoy es" in result

    async def test_contains_current_year(self, fake_context):
        from src.tools.datetime_tool import get_current_datetime

        result = await get_current_datetime._func(fake_context)
        year = str(datetime.datetime.now().year)
        assert year in result


# ── weather_tool ─────────────────────────────────────────────────────────────


class TestWeatherTool:
    async def test_successful_weather_lookup(self, fake_context):
        from src.tools.weather_tool import get_weather

        mock_geo_response = MagicMock()
        mock_geo_response.status = 200
        mock_geo_response.json = AsyncMock(
            return_value={"results": [{"latitude": 4.6, "longitude": -74.08, "name": "Bogotá"}]}
        )
        mock_geo_response.__aenter__ = AsyncMock(return_value=mock_geo_response)
        mock_geo_response.__aexit__ = AsyncMock(return_value=False)

        mock_weather_response = MagicMock()
        mock_weather_response.status = 200
        mock_weather_response.json = AsyncMock(
            return_value={
                "current": {
                    "temperature_2m": 18.5,
                    "relative_humidity_2m": 72,
                    "weather_code": 3,
                    "wind_speed_10m": 12.3,
                }
            }
        )
        mock_weather_response.__aenter__ = AsyncMock(return_value=mock_weather_response)
        mock_weather_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=[mock_geo_response, mock_weather_response])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("src.tools.weather_tool.aiohttp.ClientSession", return_value=mock_session):
            result = await get_weather._func(fake_context, city="Bogota")

        assert "Bogotá" in result
        assert "18.5" in result
        assert "nublado" in result

    async def test_city_not_found(self, fake_context):
        from src.tools.weather_tool import get_weather

        mock_geo_response = MagicMock()
        mock_geo_response.status = 200
        mock_geo_response.json = AsyncMock(return_value={})
        mock_geo_response.__aenter__ = AsyncMock(return_value=mock_geo_response)
        mock_geo_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_geo_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("src.tools.weather_tool.aiohttp.ClientSession", return_value=mock_session):
            result = await get_weather._func(fake_context, city="Xyzzyville")

        assert "No encontré" in result

    async def test_network_error_returns_fallback(self, fake_context):
        from src.tools.weather_tool import get_weather

        with patch(
            "src.tools.weather_tool.aiohttp.ClientSession", side_effect=Exception("Network error")
        ):
            result = await get_weather._func(fake_context, city="Bogota")

        assert "No pude consultar" in result


# ── fun_fact_tool ────────────────────────────────────────────────────────────


class TestFunFactTool:
    async def test_returns_prompt_with_variety(self, fake_context):
        from src.tools.fun_fact_tool import get_fun_fact

        result = await get_fun_fact._func(fake_context, topic="")
        assert "DATO CURIOSO" in result
        assert "PERSONALIDAD" in result

    async def test_includes_topic_when_provided(self, fake_context):
        from src.tools.fun_fact_tool import get_fun_fact

        result = await get_fun_fact._func(fake_context, topic="dinosaurios")
        assert "dinosaurios" in result

    async def test_fallback_without_variety(self):
        ctx = FakeRunContext(userdata={})
        from src.tools.fun_fact_tool import get_fun_fact

        result = await get_fun_fact._func(ctx, topic="")
        assert "dato curioso" in result


# ── games: start_trivia ─────────────────────────────────────────────────────


class TestStartTrivia:
    async def test_updates_instructions_with_trivia(self, fake_context):
        from src.tools.games import start_trivia

        result = await start_trivia._func(fake_context)

        fake_context.session.current_agent.update_instructions.assert_awaited_once()
        call_args = fake_context.session.current_agent.update_instructions.call_args[0][0]
        assert "MODO JUEGO: TRIVIA" in call_args
        assert "Base instructions" in call_args
        assert "Trivia iniciada" in result
        assert len(call_args) < 500

    async def test_includes_category_hint(self, fake_context):
        from src.tools.games import start_trivia

        result = await start_trivia._func(fake_context)
        assert "CATEGORIA" in result


# ── games: start_riddles ─────────────────────────────────────────────────────


class TestStartRiddles:
    async def test_updates_instructions_with_riddles(self, fake_context):
        from src.tools.games import start_riddles

        result = await start_riddles._func(fake_context)

        fake_context.session.current_agent.update_instructions.assert_awaited_once()
        call_args = fake_context.session.current_agent.update_instructions.call_args[0][0]
        assert "MODO JUEGO: ADIVINANZAS" in call_args
        assert "Adivinanzas iniciadas" in result


# ── games: start_story ───────────────────────────────────────────────────────


class TestStartStory:
    async def test_updates_instructions_with_story(self, fake_context):
        from src.tools.games import start_story

        result = await start_story._func(fake_context)

        fake_context.session.current_agent.update_instructions.assert_awaited_once()
        call_args = fake_context.session.current_agent.update_instructions.call_args[0][0]
        assert "MODO JUEGO: CUENTO INTERACTIVO" in call_args
        assert "Cuento interactivo iniciado" in result


# ── games: end_game ──────────────────────────────────────────────────────────


class TestEndGame:
    async def test_restores_base_instructions(self, fake_context):
        from src.tools.games import end_game

        result = await end_game._func(fake_context)

        fake_context.session.current_agent.update_instructions.assert_awaited_once()
        call_args = fake_context.session.current_agent.update_instructions.call_args[0][0]
        assert call_args == "Base instructions for testing."
        assert "Juego terminado" in result


# ── web_search_tool ─────────────────────────────────────────────────────────


def _mock_settings(**overrides):
    """Crea un mock de Settings con valores por defecto para web search."""
    defaults = {
        "web_search_provider": "tavily",
        "web_search_parental_consent": True,
        "tavily_api_key": "tvly-test-key",
        "brave_search_api_key": None,
        "serpapi_api_key": None,
        "web_search_max_results": 3,
        "stt_language": "es",
    }
    defaults.update(overrides)
    mock = MagicMock(spec=Settings)
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


class TestWebSearchTool:
    def _make_tool(self, **overrides):
        """Create a web_search tool via the factory with mock settings."""
        from src.tools.web_search_tool import make_web_search

        return make_web_search(_mock_settings(**overrides))

    async def test_tavily_search_success(self, fake_context):
        tool = self._make_tool()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "results": [
                    {"title": "Noticia importante", "content": "El presidente fue vacado hoy."},
                    {"title": "Otra noticia", "content": "Detalles del evento."},
                ]
            }
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("src.tools.web_search_tool.aiohttp.ClientSession", return_value=mock_session):
            result = await tool._func(fake_context, query="noticias Peru")

        assert "Noticia importante" in result
        assert "presidente" in result
        assert len(result) < 300

    async def test_brave_search_success(self, fake_context):
        tool = self._make_tool(
            web_search_provider="brave",
            brave_search_api_key="BSA-test-key",
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "web": {
                    "results": [
                        {"title": "Resultado Brave", "description": "Info desde Brave Search."},
                    ]
                }
            }
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("src.tools.web_search_tool.aiohttp.ClientSession", return_value=mock_session):
            result = await tool._func(fake_context, query="noticias Peru")

        assert "Resultado Brave" in result

    async def test_unknown_provider_returns_error(self, fake_context):
        tool = self._make_tool(web_search_provider="unknown_provider")

        result = await tool._func(fake_context, query="test")

        assert "desconocido" in result

    async def test_missing_api_key(self, fake_context):
        tool = self._make_tool(tavily_api_key=None)

        result = await tool._func(fake_context, query="test")

        assert "Falta" in result

    async def test_network_error_returns_fallback(self, fake_context):
        tool = self._make_tool()

        with patch(
            "src.tools.web_search_tool.aiohttp.ClientSession",
            side_effect=Exception("Network error"),
        ):
            result = await tool._func(fake_context, query="test")

        assert "No pude realizar" in result

    async def test_no_results_message(self, fake_context):
        tool = self._make_tool()

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"results": []})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("src.tools.web_search_tool.aiohttp.ClientSession", return_value=mock_session):
            result = await tool._func(fake_context, query="asdfghjkl123")

        assert "No encontré resultados" in result

    async def test_consent_gate_in_get_tools(self):
        """Parental consent gate is enforced by get_tools(), not the tool itself."""
        from src.tools import get_tools

        settings = _mock_settings(web_search_parental_consent=False)
        tools = get_tools(settings)

        tool_names = [getattr(t, "name", "") for t in tools]
        assert "web_search" not in tool_names

    async def test_pii_email_stripped_from_query(self, fake_context):
        from src.tools.web_search_tool import _sanitize_query

        result = _sanitize_query("busca info de juan@gmail.com en Peru")
        assert "juan@gmail.com" not in result
        assert "Peru" in result

    async def test_pii_phone_stripped_from_query(self, fake_context):
        from src.tools.web_search_tool import _sanitize_query

        result = _sanitize_query("mi telefono es +51 987 654 321 noticias")
        assert "987" not in result
        assert "noticias" in result

    async def test_pii_address_stripped_from_query(self, fake_context):
        from src.tools.web_search_tool import _sanitize_query

        result = _sanitize_query("vivo en Avenida Javier Prado 123 noticias")
        assert "Javier Prado" not in result
        assert "noticias" in result

    async def test_clean_query_passes_through(self, fake_context):
        from src.tools.web_search_tool import _sanitize_query

        result = _sanitize_query("presidente de Peru 2025")
        assert result == "presidente de Peru 2025"
