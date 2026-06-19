# OpenMRS Encounter Compiler

LiveKit agent foundation for turning a clinical conversation into structured, reviewable OpenMRS draft data.

This repository starts from the real development history of the Nebu LiveKit voice agent and narrows that foundation toward an OpenMRS AI Hackathon prototype. It is not a clinical product and does not write to OpenMRS without human review.

## Direction

The goal is not another ambient scribe. The target is a real-time encounter state machine:

- listen to a consultation through LiveKit;
- build a timestamped clinical facts ledger;
- keep evidence snippets for every extracted fact;
- identify missing fields while the encounter is still happening;
- produce OpenMRS-ready draft payloads;
- require a clinician to approve every field before anything is saved.

## Safety Model

- Human-in-the-loop by default.
- Read-only OpenMRS access unless an approved draft is submitted.
- No automatic diagnosis or autonomous ordering.
- No production PHI in demos.
- External AI services must receive synthetic, redacted, or contractually protected data.

## Planned Modules

- `livekit-agent`: existing voice agent runtime and provider abstraction.
- `clinical-facts-ledger`: typed facts with confidence, evidence, speaker, and timestamp.
- `openmrs-tools`: patient, visit, encounter, obs, and form draft tools.
- `deidentification-gateway`: deterministic redaction before cloud model calls.
- `review-ui-events`: events for an OpenMRS ESM side panel.

## Current State

This first public baseline contains the extracted LiveKit agent foundation. Clinical OpenMRS-specific tools will be layered on top in small commits so reviewers can see the project evolve.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
```

## Environment

See `.env.example`. Use demo or test credentials only.

## OpenMed Reference

OpenMed is a useful reference for local-first healthcare AI, PII detection, de-identification, FHIR, and MCP ideas. This repository does not vendor OpenMed code. If OpenMed code is added later, it should be integrated explicitly under its Apache-2.0 license with attribution.

Reference: https://github.com/maziyarpanahi/openmed

## License

MIT.
