from datetime import datetime, timezone

import pytest

from src.clinical_facts import ClinicalEvidence, ClinicalFact, EncounterDraft
from src.openmrs_payload import OpenMRSEncounterContext, build_review_bundle


def test_build_review_bundle_only_writes_approved_facts():
    approved = ClinicalFact(
        kind="allergy_denial",
        value="No known drug allergies",
        confidence=0.96,
        evidence=ClinicalEvidence(
            transcript="No soy alergica a medicamentos",
            speaker="patient",
            start_seconds=12.4,
            end_seconds=15.0,
        ),
        status="approved",
        openmrs_concept_uuid="concept-allergy-denial",
    )
    needs_review = ClinicalFact(
        kind="dizziness",
        value="Morning dizziness",
        confidence=0.74,
        evidence=ClinicalEvidence(transcript="me mareo en las mananas", speaker="patient"),
        status="needs_review",
        openmrs_concept_uuid="concept-dizziness",
    )
    draft = EncounterDraft(patient_uuid="patient-uuid", visit_uuid="visit-uuid")
    draft.add_fact(approved)
    draft.add_fact(needs_review)
    draft.missing_fields.append("dizziness onset")

    bundle = build_review_bundle(
        draft,
        OpenMRSEncounterContext(
            patient_uuid="patient-uuid",
            visit_uuid="visit-uuid",
            encounter_type_uuid="encounter-type-uuid",
            location_uuid="location-uuid",
            provider_uuid="provider-uuid",
            encounter_datetime=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
        ),
    )

    payload = bundle["openmrsDraft"]
    assert payload["patient"] == "patient-uuid"
    assert payload["visit"] == "visit-uuid"
    assert payload["obs"] == [
        {
            "concept": "concept-allergy-denial",
            "value": "No known drug allergies",
            "comment": (
                "compiler_fact=allergy_denial | confidence=0.96 | speaker=patient | "
                "start=12.40s | end=15.00s | evidence=No soy alergica a medicamentos"
            ),
        }
    ]
    assert bundle["reviewQueue"][0]["kind"] == "dizziness"
    assert bundle["missingFields"] == ["dizziness onset"]


def test_approved_fact_requires_openmrs_concept_uuid():
    draft = EncounterDraft(patient_uuid="patient-uuid")
    draft.add_fact(
        ClinicalFact(
            kind="chief_complaint",
            value="Abdominal pain",
            confidence=0.91,
            evidence=ClinicalEvidence(transcript="dolor abdominal"),
            status="approved",
        )
    )

    with pytest.raises(ValueError, match="lacks OpenMRS concept UUID"):
        build_review_bundle(
            draft,
            OpenMRSEncounterContext(
                patient_uuid="patient-uuid",
                encounter_type_uuid="encounter-type-uuid",
                location_uuid="location-uuid",
            ),
        )
