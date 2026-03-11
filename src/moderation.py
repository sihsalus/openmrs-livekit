"""
moderation.py — Detección de lenguaje inapropiado en tiempo real.

Lightweight keyword-based detector que corre en cada transcripción del niño.
NO censura — solo detecta y notifica al backend para alertar a los padres.
"""

import re
import time

from src.backend_client import backend_request, is_backend_configured
from src.config import Settings
from src.logger import get_logger

logger = get_logger("nebu.moderation")

# Palabras y patrones inapropiados en español (Latin America)
# Incluye variaciones comunes y escritura alternativa
_PROFANITY_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        # Groserías comunes
        r"\bmi[e3]rda\b",
        r"\bput[ao]\b",
        r"\bpend[e3]j[ao]\b",
        r"\bch[iu]ng[ao]\b",
        r"\bcul[oe]\b",
        r"\bver[gq]a\b",
        r"\bc[ao]j[ou]d[ao]\b",
        r"\bhij[ou][e3]?\s*(?:de\s+)?put[ao]\b",
        r"\bmal\s*parido\b",
        r"\bcar[a]j[o]\b",
        r"\bjod[ae3]r\b",
        r"\bjod[aeio]\b",
        r"\bconch[ae]\s*(?:de\s+)?(?:tu|su)\b",
        r"\bmaricon\b",
        r"\bmaric[oó]n\b",
        r"\bhue?v[oó]n\b",
        r"\bimbecil\b",
        r"\bimb[eé]cil\b",
        r"\best[uú]pid[ao]\b",
        r"\bidiot[ao]\b",
        r"\btont[ao]\b",  # suave pero en contexto agresivo
        r"\bweb[oó]n\b",
        r"\bchucha\b",
        r"\bconchatumadre\b",
        r"\bctm\b",
        r"\bptm\b",
        r"\bcsm\b",
        # Insultos/agresión
        r"\bte\s+odio\b",
        r"\bte\s+voy\s+a\s+matar\b",
        r"\bm[aá]tate\b",
        r"\bsu[ií]c[ií]d\w*\b",
        # English profanity (bilingual kids)
        r"\bfuck\w*\b",
        r"\bshit\b",
        r"\bbitch\b",
        r"\bass\s*hole\b",
        r"\bdamn\b",
    ]
]

# Cooldown: no enviar más de 1 alerta por sesión cada N segundos
_ALERT_COOLDOWN_SECONDS = 300  # 5 minutos


class ContentModerator:
    """Detecta lenguaje inapropiado y notifica al backend."""

    def __init__(self, settings: Settings, room_name: str, job_logger):
        self.settings = settings
        self.room_name = room_name
        self.job_logger = job_logger
        self._last_alert_time: float = 0
        self._flagged_words: list[str] = []
        self._total_flags: int = 0

    def check_text(self, text: str) -> str | None:
        """
        Verifica si el texto contiene lenguaje inapropiado.
        Retorna la palabra detectada o None si es limpio.
        """
        text_lower = text.lower()
        for pattern in _PROFANITY_PATTERNS:
            match = pattern.search(text_lower)
            if match:
                detected = match.group(0)
                self._total_flags += 1
                self._flagged_words.append(detected)
                self.job_logger.info(
                    "Lenguaje inapropiado detectado",
                    extra={"detected": detected, "total_flags": self._total_flags},
                )
                return detected
        return None

    def should_alert(self) -> bool:
        """Retorna True si debemos enviar alerta (respetando cooldown)."""
        now = time.time()
        if now - self._last_alert_time < _ALERT_COOLDOWN_SECONDS:
            return False
        self._last_alert_time = now
        return True

    async def send_behavior_flag(self, detected_word: str, transcript_snippet: str) -> None:
        """Envía flag de comportamiento al backend para notificar a padres."""
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
                    "flagType": "inappropriate_language",
                    "details": {
                        "detectedWord": detected_word,
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
