"""Clinical translation primitives for the OpenMRS AI Hackathon prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.deidentification import DeidentificationResult, deidentify_text


SpeakerRole = Literal["clinician", "patient", "caregiver", "interpreter", "unknown"]


@dataclass(frozen=True)
class TranslationTurn:
    """One translated clinical utterance with redaction metadata."""

    source_language: str
    target_language: str
    speaker: SpeakerRole
    source_text: str
    safe_source_text: str
    translated_text: str
    redaction_count: int


def build_translation_prompt(
    source_text: str,
    *,
    source_language: str,
    target_language: str,
    speaker: SpeakerRole,
    known_entities: tuple[str, ...] = (),
) -> tuple[str, DeidentificationResult]:
    """Build a cloud-safe translation prompt and return redaction metadata."""

    redacted = deidentify_text(source_text, known_entities=known_entities)
    prompt = (
        "You are a clinical interpreter for an OpenMRS encounter.\n"
        f"Speaker: {speaker}\n"
        f"Translate from {source_language} to {target_language}.\n"
        "Preserve clinical meaning, medication names, dosages, negations, and uncertainty.\n"
        "Do not add diagnoses, advice, or facts not present in the source.\n"
        "Keep placeholders such as <DATE_1:abcd1234> unchanged.\n\n"
        f"Source:\n{redacted.text}"
    )
    return prompt, redacted


def make_demo_translation_turn(
    source_text: str,
    translated_text: str,
    *,
    source_language: str = "es-PE",
    target_language: str = "qu",
    speaker: SpeakerRole = "clinician",
    known_entities: tuple[str, ...] = (),
) -> TranslationTurn:
    """Create a deterministic turn for offline demos and unit tests."""

    _prompt, redacted = build_translation_prompt(
        source_text,
        source_language=source_language,
        target_language=target_language,
        speaker=speaker,
        known_entities=known_entities,
    )
    return TranslationTurn(
        source_language=source_language,
        target_language=target_language,
        speaker=speaker,
        source_text=source_text,
        safe_source_text=redacted.text,
        translated_text=translated_text,
        redaction_count=redacted.redaction_count,
    )
