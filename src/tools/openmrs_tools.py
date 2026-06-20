"""OpenMRS FHIR R4 tools for clinical encounter management."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from src.clinical_facts import ClinicalEvidence, ClinicalFact, EncounterDraft
from src.config import Settings


@function_tool(
    name="search_patient",
    description=(
        "Search for a patient in OpenMRS by name. "
        "Returns a list of matching patients with their UUID, name, gender, and birth date. "
        "Use this when the clinician mentions a patient name."
    ),
)
async def search_patient(context: RunContext, name: str) -> str:
    from src.openmrs_client import search_patients

    settings: Settings = context.session.userdata.get("settings")
    results = await search_patients(settings, name)
    if not results:
        return f"No se encontraron pacientes con el nombre '{name}'."
    lines = []
    for p in results:
        lines.append(
            f"- {p['name']} | ID: {p['openmrs_id']} | UUID: {p['uuid']} "
            f"| Sexo: {p['gender']} | Nacimiento: {p['birth_date']}"
        )
    return f"Pacientes encontrados ({len(results)}):\n" + "\n".join(lines)


@function_tool(
    name="record_clinical_fact",
    description=(
        "Record a clinical fact extracted from the conversation. "
        "Call this tool each time a relevant clinical detail is mentioned: "
        "symptoms, vital signs, diagnoses, medications, allergies, or procedures. "
        "The fact is added to the encounter draft for later review."
    ),
)
async def record_clinical_fact(
    context: RunContext,
    kind: str,
    value: str,
    confidence: float = 0.9,
    transcript_excerpt: str = "",
    patient_uuid: str = "",
) -> str:
    draft: EncounterDraft = context.session.userdata.get("encounter_draft")
    if draft is None:
        draft = EncounterDraft(patient_uuid=patient_uuid or None)
        context.session.userdata["encounter_draft"] = draft

    if patient_uuid and not draft.patient_uuid:
        draft.patient_uuid = patient_uuid

    fact = ClinicalFact(
        kind=kind,
        value=value,
        confidence=confidence,
        evidence=ClinicalEvidence(transcript=transcript_excerpt),
    )
    draft.add_fact(fact)

    status_label = "⚠️ requiere revisión" if fact.needs_review() else "✓ registrado"
    total = len(draft.facts)
    return (
        f"Hecho clínico {status_label}: {kind} = {value} (confianza: {confidence:.0%}). "
        f"Total de hechos en el borrador: {total}."
    )


@function_tool(
    name="show_encounter_draft",
    description=(
        "Show the current encounter draft with all recorded clinical facts. "
        "Use this when the clinician asks to review or verify the encounter summary."
    ),
)
async def show_encounter_draft(context: RunContext) -> str:
    draft: EncounterDraft | None = context.session.userdata.get("encounter_draft")
    if draft is None or not draft.facts:
        return "No hay hechos clínicos registrados aún. Continúa la consulta."

    lines = [f"Borrador de encounter | Paciente: {draft.patient_uuid or 'sin asignar'}"]
    lines.append(f"Total de hechos: {len(draft.facts)}")
    lines.append("")

    for i, fact in enumerate(draft.facts, 1):
        review = " ⚠️" if fact.needs_review() else " ✓"
        lines.append(f"{i}. [{fact.kind}] {fact.value} ({fact.confidence:.0%}){review}")

    pending = draft.review_queue()
    if pending:
        lines.append(f"\n{len(pending)} hecho(s) pendientes de revisión.")

    if draft.missing_fields:
        lines.append(f"Campos faltantes: {', '.join(draft.missing_fields)}")

    return "\n".join(lines)


@function_tool(
    name="submit_encounter",
    description=(
        "Submit the encounter draft to OpenMRS. Only call this after the clinician "
        "explicitly approves the encounter summary. Creates a FHIR Encounter with "
        "Observations in OpenMRS."
    ),
)
async def submit_encounter(context: RunContext, patient_uuid: str = "") -> str:
    from src.openmrs_client import create_encounter

    settings: Settings = context.session.userdata.get("settings")
    draft: EncounterDraft | None = context.session.userdata.get("encounter_draft")

    if draft is None or not draft.facts:
        return "No hay hechos clínicos para enviar. Registra hechos primero."

    target_uuid = patient_uuid or draft.patient_uuid
    if not target_uuid:
        return "Falta el UUID del paciente. Busca al paciente primero con search_patient."

    observations = []
    for fact in draft.facts:
        observations.append({
            "code": fact.openmrs_concept_uuid or fact.kind,
            "display": fact.kind,
            "value": fact.value,
        })

    result = await create_encounter(
        settings,
        patient_uuid=target_uuid,
        observations=observations,
    )

    if not result:
        return "Error al crear el encounter en OpenMRS. Revisa la conexión."

    for fact in draft.facts:
        fact.status = "approved"

    enc_uuid = result["encounter_uuid"]
    obs_count = len(result["observation_uuids"])
    context.session.userdata["encounter_draft"] = EncounterDraft()

    return (
        f"Encounter creado exitosamente en OpenMRS.\n"
        f"Encounter UUID: {enc_uuid}\n"
        f"Observaciones creadas: {obs_count}\n"
        f"Paciente: {target_uuid}"
    )


def make_openmrs_tools(settings: Settings) -> list:
    return [search_patient, record_clinical_fact, show_encounter_draft, submit_encounter]
