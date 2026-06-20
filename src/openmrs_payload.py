"""OpenMRS draft payload helpers.

These helpers intentionally build review-stage payloads. They do not perform
network writes and only include facts that have already been approved by a
clinician reviewer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.clinical_facts import ClinicalFact, EncounterDraft


@dataclass(frozen=True)
class OpenMRSEncounterContext:
    """OpenMRS identifiers required to assemble an encounter draft."""

    patient_uuid: str
    encounter_type_uuid: str
    location_uuid: str
    provider_uuid: str | None = None
    visit_uuid: str | None = None
    encounter_datetime: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


def build_openmrs_encounter_payload(
    draft: EncounterDraft,
    context: OpenMRSEncounterContext,
) -> dict[str, Any]:
    """Build an OpenMRS-style encounter draft from approved clinical facts."""

    obs = [_fact_to_obs(fact) for fact in draft.approved_facts()]
    payload: dict[str, Any] = {
        "patient": context.patient_uuid,
        "encounterType": context.encounter_type_uuid,
        "location": context.location_uuid,
        "encounterDatetime": context.encounter_datetime.isoformat(),
        "obs": obs,
        "draft": True,
        "reviewRequired": False,
    }
    if context.provider_uuid:
        payload["providers"] = [{"provider": context.provider_uuid}]
    if context.visit_uuid or draft.visit_uuid:
        payload["visit"] = context.visit_uuid or draft.visit_uuid
    return payload


def build_review_bundle(
    draft: EncounterDraft,
    context: OpenMRSEncounterContext,
) -> dict[str, Any]:
    """Return approved payload plus items that still need clinician review."""

    return {
        "openmrsDraft": build_openmrs_encounter_payload(draft, context),
        "reviewQueue": [
            {
                "kind": fact.kind,
                "value": fact.value,
                "confidence": fact.confidence,
                "evidence": fact.evidence.transcript,
                "speaker": fact.evidence.speaker,
                "status": fact.status,
            }
            for fact in draft.review_queue()
        ],
        "missingFields": list(draft.missing_fields),
    }


def _fact_to_obs(fact: ClinicalFact) -> dict[str, Any]:
    if not fact.openmrs_concept_uuid:
        raise ValueError(f"Approved fact lacks OpenMRS concept UUID: {fact.kind}")
    return {
        "concept": fact.openmrs_concept_uuid,
        "value": fact.value,
        "comment": _evidence_comment(fact),
    }


def _evidence_comment(fact: ClinicalFact) -> str:
    evidence = fact.evidence
    pieces = [f"compiler_fact={fact.kind}", f"confidence={fact.confidence:.2f}"]
    if evidence.speaker:
        pieces.append(f"speaker={evidence.speaker}")
    if evidence.start_seconds is not None:
        pieces.append(f"start={evidence.start_seconds:.2f}s")
    if evidence.end_seconds is not None:
        pieces.append(f"end={evidence.end_seconds:.2f}s")
    pieces.append(f"evidence={evidence.transcript[:180]}")
    return " | ".join(pieces)
