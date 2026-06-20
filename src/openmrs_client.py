"""Async client for OpenMRS FHIR R4 API."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Any

import aiohttp

from src.config import Settings
from src.logger import get_logger

logger = get_logger("nebu.openmrs")

CONCEPT_MAP: dict[str, tuple[str, str]] = {
    "chief_complaint": ("160531AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Chief complaint (text)"),
    "symptom": ("160531AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Chief complaint (text)"),
    "systolic_bp": ("5085AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Systolic blood pressure"),
    "diastolic_bp": ("5086AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Diastolic blood pressure"),
    "temperature": ("5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Temperature (c)"),
    "height": ("5090AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Height (cm)"),
    "pulse": ("5087AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Pulse"),
    "respiratory_rate": ("5242AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Respiratory rate"),
    "allergy": ("121689AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Allergy"),
    "diagnosis": ("1284AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Coded Diagnosis"),
    "vital_sign": ("5085AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Systolic blood pressure"),
    "medication": ("162169AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Text of encounter note"),
    "note": ("162169AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "Text of encounter note"),
}

NUMERIC_CONCEPTS = {
    "5085AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": "mmHg",
    "5086AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": "mmHg",
    "5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": "DEG C",
    "5090AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": "cm",
    "5087AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": "beats/min",
    "5242AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": "breaths/min",
}

_session: aiohttp.ClientSession | None = None


def _auth_header(settings: Settings) -> str:
    creds = f"{settings.openmrs_username}:{settings.openmrs_password}"
    return "Basic " + base64.b64encode(creds.encode()).decode()


async def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),
            connector=aiohttp.TCPConnector(limit=10, keepalive_timeout=60),
        )
    return _session


async def fhir_request(
    settings: Settings,
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    session = await _get_session()
    url = f"{settings.openmrs_base_url}/ws/fhir2/R4/{path}"
    headers = {
        "Authorization": _auth_header(settings),
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",
    }
    try:
        async with session.request(method, url, headers=headers, json=json, params=params) as resp:
            if resp.status >= 400:
                body = await resp.text()
                logger.error("FHIR error", extra={"status": resp.status, "body": body[:200]})
                return None
            return await resp.json()  # type: ignore[no-any-return]
    except Exception as e:
        logger.error("FHIR request failed", extra={"error": str(e), "path": path})
        return None


async def search_patients(settings: Settings, name: str) -> list[dict[str, Any]]:
    data = await fhir_request(settings, "GET", "Patient", params={"name": name, "_count": "5"})
    if not data or "entry" not in data:
        return []
    results = []
    for entry in data["entry"]:
        r = entry.get("resource", {})
        names = r.get("name", [{}])
        display = names[0].get("text", "") if names else ""
        ids = r.get("identifier", [{}])
        openmrs_id = ids[0].get("value", "") if ids else ""
        results.append(
            {
                "uuid": r.get("id", ""),
                "name": display,
                "openmrs_id": openmrs_id,
                "gender": r.get("gender", ""),
                "birth_date": r.get("birthDate", ""),
            }
        )
    return results


async def get_patient(settings: Settings, uuid: str) -> dict[str, Any] | None:
    data = await fhir_request(settings, "GET", f"Patient/{uuid}")
    if not data:
        return None
    names = data.get("name", [{}])
    display = names[0].get("text", "") if names else ""
    ids = data.get("identifier", [{}])
    openmrs_id = ids[0].get("value", "") if ids else ""
    return {
        "uuid": data.get("id", ""),
        "name": display,
        "openmrs_id": openmrs_id,
        "gender": data.get("gender", ""),
        "birth_date": data.get("birthDate", ""),
        "active": data.get("active", False),
    }


async def create_encounter(
    settings: Settings,
    *,
    patient_uuid: str,
    encounter_type_uuid: str = "0e8230ce-bd1d-43f5-a863-cf44344fa4b0",
    location_uuid: str = "92dbdbdf-17da-4cf0-873c-ad15dfae71cb",
    observations: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    encounter_payload = {
        "resourceType": "Encounter",
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
        },
        "type": [
            {
                "coding": [
                    {
                        "system": "http://fhir.openmrs.org/code-system/encounter-type",
                        "code": encounter_type_uuid,
                    }
                ]
            }
        ],
        "subject": {"reference": f"Patient/{patient_uuid}", "type": "Patient"},
        "location": [
            {
                "location": {
                    "reference": f"Location/{location_uuid}",
                    "type": "Location",
                }
            }
        ],
    }
    result = await fhir_request(settings, "POST", "Encounter", json=encounter_payload)
    if not result:
        return None

    encounter_uuid = result.get("id")
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    created_obs = []
    for obs in observations or []:
        concept_uuid = obs.get("code", "")
        obs_payload = {
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "exam",
                            "display": "Exam",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [{"code": concept_uuid, "display": obs.get("display", "")}],
                "text": obs.get("display", ""),
            },
            "subject": {"reference": f"Patient/{patient_uuid}", "type": "Patient"},
            "encounter": {"reference": f"Encounter/{encounter_uuid}", "type": "Encounter"},
            "effectiveDateTime": now,
        }
        value_raw = obs.get("value", "")
        unit = NUMERIC_CONCEPTS.get(concept_uuid)
        if unit:
            try:
                obs_payload["valueQuantity"] = {"value": float(value_raw), "unit": unit}
            except (ValueError, TypeError):
                obs_payload["valueString"] = value_raw
        else:
            obs_payload["valueString"] = value_raw
        obs_result = await fhir_request(settings, "POST", "Observation", json=obs_payload)
        if obs_result:
            created_obs.append(obs_result.get("id"))

    return {
        "encounter_uuid": encounter_uuid,
        "observation_uuids": created_obs,
        "patient_uuid": patient_uuid,
    }


async def close_session() -> None:
    global _session
    if _session and not _session.closed:
        await _session.close()
    _session = None
