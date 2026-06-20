# Security And Privacy Model

## Demo Boundary

- Use synthetic patients only.
- Do not record production PHI in the hackathon video.
- Keep `ENABLE_TRANSCRIPT_SAVE=false` unless the backend is a local synthetic
  demo store.

## Data Flow Controls

- Audio is scoped to a LiveKit room.
- STT output is treated as sensitive.
- `deidentification.py` redacts common PHI-like values before cloud AI prompts
  or transcript persistence.
- Findings store salted hashes, token type, and offsets, not raw PHI.
- Translation prompts instruct the model to preserve placeholders unchanged.

## SOC 2-Aligned Controls To Describe

This prototype is not SOC 2 certified. The intended deployment pattern maps to
common SOC 2 control themes:

- Security: service-to-service secret for the backend bridge, no public write
  path to OpenMRS, least-privilege OpenMRS credentials.
- Confidentiality: redaction before external AI calls, raw transcript storage
  disabled by default, synthetic demo data.
- Processing integrity: human approval required before writes, confidence and
  evidence on every candidate fact.
- Availability: provider fallback settings for LLM/STT/TTS and hybrid
  deployment support.
- Privacy: no autonomous diagnosis or order entry, explicit consent and local
  policy required for recording or transcript retention.

## Production Hardening Checklist

- Replace regex-only redaction with local NER plus site-specific dictionaries.
- Add per-site salt management through a secrets manager.
- Encrypt transcript and draft stores at rest.
- Add immutable audit events for approval, rejection, and OpenMRS writes.
- Use vendor contracts/BAA or local models for any PHI-bearing workflow.
- Add retention policies and deletion workflows.
- Add role-based access control for review UI events.
