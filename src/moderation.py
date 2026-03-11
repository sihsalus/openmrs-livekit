"""
moderation.py — Content moderation for children's voice AI.

Two-layer detection:
1. Regex (instant, ~0ms) — catches obvious profanity in Spanish/English
2. OpenAI Moderation API (async, free, ~200ms) — semantic detection of
   harassment, self-harm, sexual content, violence, hate speech in 40+ languages

NO censura — solo detecta y notifica al backend para alertar a los padres.
"""

from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field

from src.backend_client import backend_request, is_backend_configured
from src.config import Settings
from src.logger import get_logger

logger = get_logger("nebu.moderation")

# ── Layer 1: Regex patterns ─────────────────────────────────────────────────
# Unicode-normalized + case-insensitive matching.
# Covers Spanish (Latin America) and English profanity.

_PROFANITY_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        # ── Spanish groserías ──
        r"\bmi[e3]rda\b",
        r"\bput[ao]s?\b",
        r"\bpend[e3]j[ao]s?\b",
        r"\bch[iu]ng[ao]+\b",
        r"\bcul[oe]s?\b",
        r"\bver[gq]a\b",
        r"\bc[ao]j[ou]d[ao]\b",
        r"\bhij[ou][e3]?\s*(?:de\s+)?put[ao]\b",
        r"\bmal\s*parid[ao]\b",
        r"\bcar[a]j[o]\b",
        r"\bjod[ae3ir]\w*\b",
        r"\bconch[ae]\s*(?:de\s+)?(?:tu|su)\b",
        r"\bmaric[oó]n\b",
        r"\bhue?v[oó]n\b",
        r"\bimb[eé]cil\b",
        r"\best[uú]pid[ao]s?\b",
        r"\bidiot[ao]s?\b",
        r"\bweb[oó]n\b",
        r"\bchucha\b",
        r"\bconchatumadre\b",
        r"\bctm\b",
        r"\bptm\b",
        r"\bcsm\b",
        r"\bmaldito\b",
        r"\bpit[ao]\b",
        r"\bping[ao]\b",
        r"\bmamón\b",
        r"\bmam[oó]n\b",
        # ── Aggression / self-harm ──
        r"\bte\s+odio\b",
        r"\bte\s+voy\s+a\s+matar\b",
        r"\bm[aá]tate\b",
        r"\bsu[ií]c[ií]d\w*\b",
        r"\bme\s+quiero\s+morir\b",
        # ── English profanity (bilingual kids) ──
        r"\bfuck\w*\b",
        r"\bsh[i1]t\b",
        r"\bb[i1]tch\b",
        r"\bass\s*hole\b",
        r"\bdamn\b",
        r"\bwh[o0]re\b",
        r"\bd[i1]ck\b",
    ]
]


def _normalize_text(text: str) -> str:
    """Unicode NFKD normalize + strip accents for evasion detection."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def check_regex(text: str) -> str | None:
    """Layer 1: Fast regex check. Returns matched word or None."""
    normalized = _normalize_text(text.lower())
    for pattern in _PROFANITY_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return match.group(0)
    return None


# ── Layer 2: OpenAI Moderation API ──────────────────────────────────────────
# Free, supports 40+ languages including Spanish natively.
# Categories relevant for children: harassment, self-harm, sexual, violence.

# Lower thresholds for children's app (default is ~0.5)
_CHILD_SAFETY_THRESHOLDS: dict[str, float] = {
    "harassment": 0.3,
    "harassment/threatening": 0.2,
    "self-harm": 0.15,
    "self-harm/intent": 0.1,
    "self-harm/instructions": 0.1,
    "sexual": 0.15,
    "sexual/minors": 0.05,
    "violence": 0.3,
    "violence/graphic": 0.2,
    "hate": 0.3,
    "hate/threatening": 0.2,
}


@dataclass
class ModerationResult:
    """Result from the moderation check."""

    flagged: bool = False
    source: str = ""  # "regex" or "openai_moderation"
    detected: str = ""  # matched word or category
    categories: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)


async def check_openai_moderation(text: str) -> ModerationResult:
    """Layer 2: OpenAI Moderation API (free, async). Returns ModerationResult."""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI()
        response = await client.moderations.create(
            model="omni-moderation-latest",
            input=text,
        )
        result = response.results[0]

        # Check against child-safe thresholds
        flagged_categories = []
        category_scores = {}

        for category, threshold in _CHILD_SAFETY_THRESHOLDS.items():
            # category_scores uses dots in some SDKs, underscores in others
            attr_name = category.replace("/", "_").replace("-", "_")
            score = getattr(result.category_scores, attr_name, 0.0)
            if score is None:
                score = 0.0
            category_scores[category] = score
            if score >= threshold:
                flagged_categories.append(category)

        if flagged_categories:
            return ModerationResult(
                flagged=True,
                source="openai_moderation",
                detected=flagged_categories[0],
                categories=flagged_categories,
                scores=category_scores,
            )

        return ModerationResult(flagged=False)

    except Exception as exc:
        logger.warning(
            "OpenAI moderation API failed, relying on regex only", extra={"error": str(exc)}
        )
        return ModerationResult(flagged=False)


# ── Cooldown ────────────────────────────────────────────────────────────────
_ALERT_COOLDOWN_SECONDS = 300  # 5 minutes between parent notifications


# ── ContentModerator class ──────────────────────────────────────────────────


class ContentModerator:
    """Two-layer content moderator for children's voice sessions."""

    def __init__(self, settings: Settings, room_name: str, job_logger):
        self.settings = settings
        self.room_name = room_name
        self.job_logger = job_logger
        self._last_alert_time: float = 0
        self._flagged_words: list[str] = []
        self._total_flags: int = 0

    def check_regex(self, text: str) -> str | None:
        """Layer 1: instant regex check."""
        return check_regex(text)

    async def check_full(self, text: str) -> ModerationResult:
        """
        Full two-layer check:
        1. Regex (instant) — if hit, return immediately
        2. OpenAI Moderation API (async) — semantic analysis
        """
        # Layer 1: regex
        regex_match = check_regex(text)
        if regex_match:
            self._record_flag(regex_match)
            return ModerationResult(
                flagged=True,
                source="regex",
                detected=regex_match,
            )

        # Layer 2: OpenAI Moderation API
        result = await check_openai_moderation(text)
        if result.flagged:
            self._record_flag(result.detected)
            self.job_logger.info(
                "OpenAI moderation flagged content",
                extra={
                    "categories": result.categories,
                    "top_score": max(result.scores.values()) if result.scores else 0,
                },
            )

        return result

    def _record_flag(self, detected: str) -> None:
        self._total_flags += 1
        self._flagged_words.append(detected)
        self.job_logger.info(
            "Content flagged",
            extra={"detected": detected, "total_flags": self._total_flags},
        )

    def should_alert(self) -> bool:
        """Returns True if we should send an alert (respecting cooldown)."""
        now = time.time()
        if now - self._last_alert_time < _ALERT_COOLDOWN_SECONDS:
            return False
        self._last_alert_time = now
        return True

    async def send_behavior_flag(self, result: ModerationResult, transcript_snippet: str) -> None:
        """Send behavior flag to backend for parent notification."""
        if not is_backend_configured(self.settings):
            return

        if not self.should_alert():
            self.job_logger.debug("Alert cooldown active, skipping notification")
            return

        try:
            await backend_request(
                self.settings,
                "POST",
                "voice/sessions/behavior-flag",
                self.job_logger,
                json={
                    "roomName": self.room_name,
                    "flagType": result.detected
                    if result.source == "regex"
                    else result.categories[0]
                    if result.categories
                    else "unknown",
                    "details": {
                        "source": result.source,
                        "detected": result.detected,
                        "categories": result.categories,
                        "snippet": transcript_snippet[:200],
                        "totalFlags": self._total_flags,
                    },
                },
                label="behavior flag",
            )
        except Exception as exc:
            self.job_logger.warning("Error sending behavior flag", extra={"error": str(exc)})

    @property
    def flagged_words(self) -> list[str]:
        return list(self._flagged_words)

    @property
    def total_flags(self) -> int:
        return self._total_flags
