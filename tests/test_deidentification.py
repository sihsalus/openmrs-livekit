from src.clinical_translation import build_translation_prompt, make_demo_translation_turn
from src.deidentification import deidentify_text


def test_deidentify_text_replaces_common_phi_without_retaining_raw_values():
    text = (
        "Paciente Juana Perez, DNI 12345678, telefono +51 987 654 321, "
        "correo juana@example.com, fecha 12/06/2026."
    )

    result = deidentify_text(text, known_entities=("Juana Perez",))

    assert "Juana Perez" not in result.text
    assert "12345678" not in result.text
    assert "987 654 321" not in result.text
    assert "juana@example.com" not in result.text
    assert "12/06/2026" not in result.text
    assert result.redaction_count == 5
    assert all("juana" not in finding.value_hash for finding in result.findings)


def test_translation_prompt_uses_redacted_source_and_preserves_placeholders():
    prompt, result = build_translation_prompt(
        "Dile a Juana Perez que no duplique metformina el 12/06/2026.",
        source_language="es-PE",
        target_language="qu",
        speaker="clinician",
        known_entities=("Juana Perez",),
    )

    assert "Juana Perez" not in prompt
    assert "12/06/2026" not in prompt
    assert result.redaction_count == 2
    assert "Keep placeholders" in prompt


def test_demo_translation_turn_carries_redaction_count():
    turn = make_demo_translation_turn(
        "Paciente 550e8400-e29b-41d4-a716-446655440000 niega alergias.",
        "El paciente dice que no tiene alergias.",
        target_language="es",
        speaker="patient",
    )

    assert "550e8400" not in turn.safe_source_text
    assert turn.redaction_count == 1
