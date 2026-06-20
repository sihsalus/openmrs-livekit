"""Deterministic de-identification helpers for clinical demo transcripts.

This module is intentionally conservative and local. It does not claim to be
a complete PHI detector; it provides a predictable redaction boundary before
text leaves the clinic-side runtime for cloud AI services or review events.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Iterable, Literal


FindingType = Literal[
    "email",
    "phone",
    "document_id",
    "date",
    "uuid",
    "known_entity",
]


@dataclass(frozen=True)
class DeidentificationFinding:
    """A redacted PHI-like span without retaining the raw source value."""

    token: str
    kind: FindingType
    value_hash: str
    start: int
    end: int


@dataclass(frozen=True)
class DeidentificationResult:
    """Redacted text and metadata safe for audit logs."""

    text: str
    findings: tuple[DeidentificationFinding, ...] = field(default_factory=tuple)

    @property
    def redaction_count(self) -> int:
        return len(self.findings)


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?51[\s.-]?)?(?:9[\d\s.-]{8,}|(?:\d[\s.-]){8,}\d)(?!\d)"
)
_DOCUMENT_RE = re.compile(
    r"\b(?:dni|documento|doc\.?|id|hc|historia(?:\s+clinica)?)\s*[:#-]?\s*([A-Z0-9-]{6,18})\b",
    re.IGNORECASE,
)
_DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})\b"
)
_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


def deidentify_text(
    text: str,
    *,
    known_entities: Iterable[str] | None = None,
    salt: str = "openmrs-livekit",
) -> DeidentificationResult:
    """Return text with PHI-like values replaced by stable opaque tokens.

    `known_entities` should be populated from trusted local context, for
    example the patient display name, clinician name, or local facility name.
    The returned findings contain only salted hashes and offsets from the
    original text; the raw values are intentionally not preserved.
    """

    spans: list[tuple[int, int, FindingType, str]] = []
    spans.extend(_regex_spans(_EMAIL_RE, text, "email"))
    spans.extend(_regex_spans(_PHONE_RE, text, "phone"))
    spans.extend(_regex_spans(_DOCUMENT_RE, text, "document_id"))
    spans.extend(_regex_spans(_DATE_RE, text, "date"))
    spans.extend(_regex_spans(_UUID_RE, text, "uuid"))
    spans.extend(_known_entity_spans(text, known_entities or ()))

    selected = _select_non_overlapping(spans)
    if not selected:
        return DeidentificationResult(text=text)

    parts: list[str] = []
    findings: list[DeidentificationFinding] = []
    cursor = 0
    counters: dict[FindingType, int] = {}

    for start, end, kind, value in selected:
        counters[kind] = counters.get(kind, 0) + 1
        digest = _digest(value, salt)
        token = f"<{kind.upper()}_{counters[kind]}:{digest[:8]}>"
        parts.append(text[cursor:start])
        parts.append(token)
        findings.append(
            DeidentificationFinding(
                token=token,
                kind=kind,
                value_hash=digest,
                start=start,
                end=end,
            )
        )
        cursor = end

    parts.append(text[cursor:])
    return DeidentificationResult(text="".join(parts), findings=tuple(findings))


def _regex_spans(
    pattern: re.Pattern[str],
    text: str,
    kind: FindingType,
) -> list[tuple[int, int, FindingType, str]]:
    spans: list[tuple[int, int, FindingType, str]] = []
    for match in pattern.finditer(text):
        start, end = match.span(1) if match.lastindex else match.span()
        spans.append((start, end, kind, text[start:end]))
    return spans


def _known_entity_spans(
    text: str,
    entities: Iterable[str],
) -> list[tuple[int, int, FindingType, str]]:
    spans: list[tuple[int, int, FindingType, str]] = []
    for entity in entities:
        entity = entity.strip()
        if len(entity) < 3:
            continue
        pattern = re.compile(rf"(?<!\w){re.escape(entity)}(?!\w)", re.IGNORECASE)
        spans.extend((m.start(), m.end(), "known_entity", m.group(0)) for m in pattern.finditer(text))
    return spans


def _select_non_overlapping(
    spans: list[tuple[int, int, FindingType, str]],
) -> list[tuple[int, int, FindingType, str]]:
    """Prefer earlier and longer spans when detectors overlap."""

    ordered = sorted(spans, key=lambda s: (s[0], -(s[1] - s[0])))
    selected: list[tuple[int, int, FindingType, str]] = []
    occupied_until = -1
    for span in ordered:
        if span[0] < occupied_until:
            continue
        selected.append(span)
        occupied_until = span[1]
    return selected


def _digest(value: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{value.lower()}".encode("utf-8")).hexdigest()
