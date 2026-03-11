"""Comprehensive tests for content moderation system."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.moderation import (
    ContentModerator,
    ModerationResult,
    _normalize_text,
    check_openai_moderation,
    check_regex,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 1: Regex tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNormalizeText:
    """Unicode normalization for evasion detection."""

    def test_strips_accents(self):
        assert _normalize_text("estúpido") == "estupido"

    def test_strips_tildes(self):
        assert _normalize_text("maricón") == "maricon"

    def test_nfkd_fullwidth(self):
        # Fullwidth characters should be normalized
        result = _normalize_text("ｍｉｅｒｄａ")
        assert result == "mierda"

    def test_plain_text_unchanged(self):
        assert _normalize_text("hola mundo") == "hola mundo"

    def test_empty_string(self):
        assert _normalize_text("") == ""


class TestCheckRegex:
    """Layer 1: Fast regex matching."""

    # ── Spanish profanity ──

    @pytest.mark.parametrize(
        "text",
        [
            "eres una mierda",
            "qué mi3rda",
            "MIERDA!",
            "puta madre",
            "eres un puto",
            "pendejo",
            "pend3ja",
            "chingao",
            "culo",
            "verga",
            "cojudo",
            "hijueputa",
            "hijo de puta",
            "malparida",
            "carajo",
            "joder",
            "jodido",
            "concha de tu madre",
            "maricón",
            "maricon",
            "huevón",
            "huevon",
            "imbécil",
            "imbecil",
            "estúpido",
            "estupida",
            "idiota",
            "webón",
            "chucha",
            "conchatumadre",
            "CTM",
            "ptm",
            "CSM",
            "maldito",
        ],
    )
    def test_detects_spanish_profanity(self, text):
        assert check_regex(text) is not None, f"Should detect: {text}"

    # ── English profanity ──

    @pytest.mark.parametrize(
        "text",
        [
            "fuck you",
            "fucking",
            "shit",
            "bitch",
            "asshole",
            "damn",
            "whore",
            "dick",
        ],
    )
    def test_detects_english_profanity(self, text):
        assert check_regex(text) is not None, f"Should detect: {text}"

    # ── Aggression / self-harm ──

    @pytest.mark.parametrize(
        "text",
        [
            "te odio",
            "te voy a matar",
            "mátate",
            "matate",
            "suicidio",
            "suicidarse",
            "me quiero morir",
        ],
    )
    def test_detects_aggression_selfharm(self, text):
        assert check_regex(text) is not None, f"Should detect: {text}"

    # ── Evasion via Unicode ──

    def test_detects_accented_evasion(self):
        # "estúpido" with accent should still be caught
        assert check_regex("estúpido") is not None

    def test_detects_fullwidth_evasion(self):
        # Fullwidth mierda
        assert check_regex("ｍｉｅｒｄａ") is not None

    # ── Clean text (should NOT be flagged) ──

    @pytest.mark.parametrize(
        "text",
        [
            "hola, ¿cómo estás?",
            "me gustan los dinosaurios",
            "quiero jugar fútbol",
            "mi mamá es bonita",
            "estoy feliz",
            "cuéntame un cuento",
            "¿puedo tener un helado?",
            "uno dos tres cuatro cinco",
            "me gusta el chocolate",
            "quiero ser astronauta",
            "hoy fui al colegio",
            "mi perro se llama Max",
            "jugamos en el parque",
            # Edge cases that should NOT trigger
            "mi cultura es bonita",  # "cul" inside "cultura"
            "el colegio tiene taller de pintura",  # "puta" is not present
            "me gusta computar",  # "put" inside "computar"
            "la cuerda está aquí",  # no match
            "estoy asustado",  # not "estúpido"
        ],
    )
    def test_clean_text_not_flagged(self, text):
        assert check_regex(text) is None, f"Should NOT detect: {text}"


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 2: OpenAI Moderation API tests (mocked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestOpenAIModerationAPI:
    """Layer 2: OpenAI Moderation API integration."""

    @pytest.mark.asyncio
    async def test_returns_flagged_when_above_threshold(self):
        """Should flag content that exceeds child-safe thresholds."""
        mock_scores = MagicMock()
        mock_scores.harassment = 0.8
        mock_scores.harassment_threatening = 0.1
        mock_scores.self_harm = 0.01
        mock_scores.self_harm_intent = 0.0
        mock_scores.self_harm_instructions = 0.0
        mock_scores.sexual = 0.01
        mock_scores.sexual_minors = 0.0
        mock_scores.violence = 0.05
        mock_scores.violence_graphic = 0.0
        mock_scores.hate = 0.02
        mock_scores.hate_threatening = 0.0

        mock_result = MagicMock()
        mock_result.category_scores = mock_scores

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        with patch("openai.AsyncOpenAI") as MockClient:
            instance = MockClient.return_value
            instance.moderations = MagicMock()
            instance.moderations.create = AsyncMock(return_value=mock_response)

            result = await check_openai_moderation("te voy a hacer daño")

            assert result.flagged
            assert "harassment" in result.categories
            assert result.source == "openai_moderation"

    @pytest.mark.asyncio
    async def test_returns_not_flagged_for_clean_content(self):
        """Should not flag clean children's content."""
        mock_scores = MagicMock()
        for attr in [
            "harassment",
            "harassment_threatening",
            "self_harm",
            "self_harm_intent",
            "self_harm_instructions",
            "sexual",
            "sexual_minors",
            "violence",
            "violence_graphic",
            "hate",
            "hate_threatening",
        ]:
            setattr(mock_scores, attr, 0.01)

        mock_result = MagicMock()
        mock_result.category_scores = mock_scores

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        with patch("openai.AsyncOpenAI") as MockClient:
            instance = MockClient.return_value
            instance.moderations = MagicMock()
            instance.moderations.create = AsyncMock(return_value=mock_response)

            result = await check_openai_moderation("me gustan los dinosaurios")

            assert not result.flagged
            assert result.categories == []

    @pytest.mark.asyncio
    async def test_low_sexual_minors_threshold(self):
        """sexual/minors has a very low threshold (0.05) for child safety."""
        mock_scores = MagicMock()
        for attr in [
            "harassment",
            "harassment_threatening",
            "self_harm",
            "self_harm_intent",
            "self_harm_instructions",
            "sexual",
            "violence",
            "violence_graphic",
            "hate",
            "hate_threatening",
        ]:
            setattr(mock_scores, attr, 0.01)
        mock_scores.sexual_minors = 0.06  # Just above 0.05 threshold

        mock_result = MagicMock()
        mock_result.category_scores = mock_scores

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        with patch("openai.AsyncOpenAI") as MockClient:
            instance = MockClient.return_value
            instance.moderations = MagicMock()
            instance.moderations.create = AsyncMock(return_value=mock_response)

            result = await check_openai_moderation("some text")

            assert result.flagged
            assert "sexual/minors" in result.categories

    @pytest.mark.asyncio
    async def test_api_failure_returns_not_flagged(self):
        """If OpenAI API fails, should return not flagged (fail-open for regex to cover)."""
        with patch("openai.AsyncOpenAI") as MockClient:
            instance = MockClient.return_value
            instance.moderations = MagicMock()
            instance.moderations.create = AsyncMock(side_effect=Exception("API down"))

            result = await check_openai_moderation("test text")

            assert not result.flagged


# ═══════════════════════════════════════════════════════════════════════════════
# ContentModerator integration tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestContentModerator:
    """Integration tests for the full moderation pipeline."""

    @pytest.fixture
    def moderator(self):
        settings = MagicMock()
        settings.agent_backend_url = None
        settings.agent_internal_secret = None
        return ContentModerator(settings, "test-room", MagicMock())

    def test_check_regex_detects_profanity(self, moderator):
        assert moderator.check_regex("eres una mierda") is not None

    def test_check_regex_passes_clean(self, moderator):
        assert moderator.check_regex("hola amigo") is None

    @pytest.mark.asyncio
    async def test_check_full_regex_hit_skips_api(self, moderator):
        """When regex hits, should NOT call OpenAI API (fast path)."""
        with patch("src.moderation.check_openai_moderation") as mock_api:
            result = await moderator.check_full("eres un pendejo")

            assert result.flagged
            assert result.source == "regex"
            mock_api.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_full_calls_api_on_regex_miss(self, moderator):
        """When regex misses, should call OpenAI Moderation API."""
        with patch("src.moderation.check_openai_moderation", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = ModerationResult(flagged=False)

            result = await moderator.check_full("me gustan los dinosaurios")

            assert not result.flagged
            mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_full_records_flag_on_detection(self, moderator):
        """Should track total flags and flagged words."""
        assert moderator.total_flags == 0

        with patch("src.moderation.check_openai_moderation", new_callable=AsyncMock):
            await moderator.check_full("qué mierda")
            assert moderator.total_flags == 1
            assert "mierda" in moderator.flagged_words

            await moderator.check_full("puta madre")
            assert moderator.total_flags == 2

    def test_cooldown_respected(self, moderator):
        """Should not alert more than once per cooldown period."""
        assert moderator.should_alert() is True
        assert moderator.should_alert() is False  # cooldown active

    def test_cooldown_expires(self, moderator):
        """After cooldown expires, should alert again."""
        moderator.should_alert()
        moderator._last_alert_time = time.time() - 301  # 5min + 1s ago
        assert moderator.should_alert() is True

    @pytest.mark.asyncio
    async def test_send_behavior_flag_skips_when_no_backend(self, moderator):
        """Should not crash when backend is not configured."""
        result = ModerationResult(flagged=True, source="regex", detected="mierda")
        await moderator.send_behavior_flag(result, "eres una mierda")
        # No exception = pass

    @pytest.mark.asyncio
    async def test_send_behavior_flag_calls_backend(self):
        """Should call backend API with correct payload."""
        settings = MagicMock()
        settings.agent_backend_url = "http://backend:3001/api/v1"
        settings.agent_internal_secret = "secret123"

        moderator = ContentModerator(settings, "room-123", MagicMock())

        result = ModerationResult(
            flagged=True,
            source="regex",
            detected="mierda",
            categories=[],
        )

        with patch("src.moderation.backend_request", new_callable=AsyncMock) as mock_req:
            with patch("src.moderation.is_backend_configured", return_value=True):
                await moderator.send_behavior_flag(result, "eres una mierda")

                mock_req.assert_called_once()
                call_kwargs = mock_req.call_args
                payload = call_kwargs.kwargs["json"]
                assert payload["roomName"] == "room-123"
                assert payload["flagType"] == "mierda"
                assert payload["details"]["source"] == "regex"

    @pytest.mark.asyncio
    async def test_send_behavior_flag_cooldown_prevents_second_call(self):
        """Second alert within cooldown should be skipped."""
        settings = MagicMock()
        settings.agent_backend_url = "http://backend:3001/api/v1"
        settings.agent_internal_secret = "secret123"

        moderator = ContentModerator(settings, "room-123", MagicMock())

        result = ModerationResult(flagged=True, source="regex", detected="mierda")

        with patch("src.moderation.backend_request", new_callable=AsyncMock) as mock_req:
            with patch("src.moderation.is_backend_configured", return_value=True):
                await moderator.send_behavior_flag(result, "text1")
                await moderator.send_behavior_flag(result, "text2")

                assert mock_req.call_count == 1  # Only first call goes through


# ═══════════════════════════════════════════════════════════════════════════════
# Edge cases and regression tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases that could cause false positives or misses."""

    def test_word_boundary_prevents_false_positives(self):
        """Words containing profanity substrings should NOT match."""
        # "puta" inside "computadora" — word boundary should prevent this
        assert check_regex("me gusta la computadora") is None
        # "culo" inside "cálculo"
        assert check_regex("estoy estudiando cálculo") is None

    def test_plural_forms_detected(self):
        assert check_regex("son unos pendejos") is not None
        assert check_regex("todas son putas") is not None

    def test_mixed_case(self):
        assert check_regex("MIERDA") is not None
        assert check_regex("Pendejo") is not None
        assert check_regex("cArAjO") is not None

    def test_with_punctuation(self):
        assert check_regex("¡mierda!") is not None
        assert check_regex("puta.") is not None
        assert check_regex("¿pendejo?") is not None

    def test_abbreviations(self):
        assert check_regex("ctm") is not None
        assert check_regex("ptm") is not None
        assert check_regex("csm") is not None
        assert check_regex("CTM!!!") is not None

    def test_empty_string(self):
        assert check_regex("") is None

    def test_numbers_only(self):
        assert check_regex("12345") is None

    def test_very_long_text(self):
        clean_text = "hola " * 1000
        assert check_regex(clean_text) is None

    def test_profanity_in_long_text(self):
        text = "hola " * 100 + "mierda" + " hola" * 100
        assert check_regex(text) is not None

    def test_leet_speak_e3(self):
        assert check_regex("mi3rda") is not None
        assert check_regex("pend3jo") is not None

    def test_self_harm_phrases(self):
        assert check_regex("me quiero morir") is not None
        assert check_regex("mátate ya") is not None

    def test_peruvian_slang(self):
        assert check_regex("chucha") is not None
        assert check_regex("conchatumadre") is not None
        assert check_regex("webón") is not None

    def test_mexican_slang(self):
        assert check_regex("chingao") is not None
        assert check_regex("pinche") is None  # not in list (could be added)

    def test_colombian_slang(self):
        assert check_regex("hijueputa") is not None
        assert check_regex("malparido") is not None


class TestModerationResult:
    """ModerationResult dataclass."""

    def test_default_not_flagged(self):
        r = ModerationResult()
        assert not r.flagged
        assert r.source == ""
        assert r.detected == ""
        assert r.categories == []
        assert r.scores == {}

    def test_flagged_result(self):
        r = ModerationResult(
            flagged=True,
            source="regex",
            detected="mierda",
        )
        assert r.flagged
        assert r.source == "regex"
