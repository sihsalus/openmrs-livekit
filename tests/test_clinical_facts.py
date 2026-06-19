from src.clinical_facts import ClinicalEvidence, ClinicalFact, EncounterDraft


def test_encounter_draft_separates_review_queue_from_approved_facts():
    approved_fact = ClinicalFact(
        kind="chief_complaint",
        value="Dolor abdominal",
        confidence=0.94,
        evidence=ClinicalEvidence(transcript="me duele la barriga"),
        status="approved",
    )
    draft_fact = ClinicalFact(
        kind="allergy",
        value="Niega alergias",
        confidence=0.72,
        evidence=ClinicalEvidence(transcript="creo que no tengo alergias"),
    )

    draft = EncounterDraft(patient_uuid="patient-uuid", visit_uuid="visit-uuid")
    draft.add_fact(approved_fact)
    draft.add_fact(draft_fact)

    assert draft.approved_facts() == [approved_fact]
    assert draft.review_queue() == [draft_fact]
    assert draft_fact.needs_review()
