"""Typed clinical draft primitives for OpenMRS encounter review.

These models intentionally represent draft data only. A separate human review
step must approve facts before an OpenMRS encounter or observation is written.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

FactStatus = Literal["detected", "needs_review", "approved", "rejected"]


@dataclass(frozen=True)
class ClinicalEvidence:
    """Trace from a structured fact back to a source transcript span."""

    transcript: str
    start_seconds: float | None = None
    end_seconds: float | None = None
    speaker: str | None = None


@dataclass
class ClinicalFact:
    """A single candidate fact extracted from the encounter."""

    kind: str
    value: str
    confidence: float
    evidence: ClinicalEvidence
    status: FactStatus = "detected"
    openmrs_concept_uuid: str | None = None

    def needs_review(self, threshold: float = 0.85) -> bool:
        return self.confidence < threshold or self.status == "needs_review"


@dataclass
class EncounterDraft:
    """Reviewable encounter draft assembled from clinical facts."""

    patient_uuid: str | None = None
    visit_uuid: str | None = None
    facts: list[ClinicalFact] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)

    def approved_facts(self) -> list[ClinicalFact]:
        return [fact for fact in self.facts if fact.status == "approved"]

    def review_queue(self) -> list[ClinicalFact]:
        return [fact for fact in self.facts if fact.status in ("detected", "needs_review")]

    def add_fact(self, fact: ClinicalFact) -> None:
        self.facts.append(fact)
