# OpenMRS LiveKit

Local-first voice AI for OpenMRS encounters.

OpenMRS LiveKit is a hackathon prototype for privacy-preserving clinical
translation and encounter draft generation. It runs beside OpenMRS on clinic
hardware, routes audio through LiveKit, transcribes each turn locally, redacts
PHI-like values, translates clinician-patient speech into clearer language, and
builds clinician-reviewed OpenMRS draft observations.

It is not a medical device, not a diagnosis engine, and not an autonomous scribe.
The system never writes clinical data to OpenMRS without clinician review.

## Why This Exists

Many OpenMRS deployments operate in clinics with unreliable internet, limited
staffing, and language or health-literacy barriers between clinicians and
patients. Cloud-only AI is a poor fit when PHI cannot leave the facility or when
connectivity is unreliable.

OpenMRS LiveKit focuses on a narrow workflow:

1. Capture a clinical conversation through a local LiveKit room.
2. Transcribe clinician and patient turns on local hardware.
3. Redact PHI-like values before AI inference or transcript persistence.
4. Translate clinical speech into patient-facing plain language.
5. Extract candidate OpenMRS facts with evidence and confidence.
6. Keep incomplete or low-confidence items in a review queue.
7. Generate OpenMRS-style draft payloads from approved facts only.

## Architecture

```text
Clinician / patient audio
          |
          v
Local LiveKit room
          |
          v
Local STT provider
whisper.cpp or Vosk
          |
          v
De-identification gateway
          |
          +------------------------------+
          |                              |
          v                              v
Patient-facing translation         Clinical fact extraction
local LLM / rules                  local LLM + JSON schema
          |                              |
          v                              v
Local TTS provider                  EncounterDraft
Piper / sherpa-onnx                 review queue
          |                              |
          v                              v
Patient hears response          OpenMRS draft payload
                                 after clinician approval
```

## OpenMRS Integration

The intended deployment is a standalone local service or container running next
to OpenMRS.

OpenMRS interaction is through REST or FHIR endpoints:

- read patient, visit, encounter type, location, provider, form, and concept
  metadata;
- build local draft encounter and obs payloads;
- submit only clinician-approved observations;
- keep the demo path synthetic and read-only by default.

The current prototype includes an OpenMRS-style payload builder that only emits
approved facts and keeps the rest in a review bundle.

## Local AI Stack

The project is designed to be 100% offline-capable.

Recommended CPU-first stack:

- Audio routing: local LiveKit server.
- STT: `whisper.cpp` with a small multilingual model, or Vosk for a lighter
  streaming mode.
- TTS: Piper Spanish voices, or sherpa-onnx for a unified offline speech stack.
- Parser / structured extraction: `llama.cpp` with a small quantized GGUF model
  such as Qwen3-1.7B Q4 or Qwen3-4B Q4.
- Structured output: JSON grammar, schema validation, and local OpenMRS payload
  generation.

Minimum reliable clinic target:

- modern 8-core CPU;
- 16 GB RAM recommended;
- 20 GB free disk for models and runtime artifacts;
- no GPU required.

A lighter profile can run on an Intel i5-class mini PC or laptop with 8 GB RAM
using Vosk, Piper, and a small quantized parser model.

## Current Demo Capabilities

- Cloud-safe clinical translation prompt with deterministic PHI placeholders.
- Local de-identification for emails, phone numbers, document IDs, dates, UUIDs,
  and known entities.
- Reviewable clinical facts with confidence, evidence, speaker, and status.
- OpenMRS-style encounter draft payloads generated only from approved facts.
- Transcript persistence disabled by default, with redaction before any optional
  save.
- Hackathon submission materials in `docs/`.

## Safety Model

- Human-in-the-loop by default.
- No automatic diagnosis.
- No autonomous prescribing or ordering.
- No automatic OpenMRS writes.
- No production PHI in demos.
- Transcript persistence disabled by default.
- Raw transcript storage requires explicit configuration.
- External AI services should receive only synthetic, redacted, or contractually
  protected data. The target deployment avoids external AI APIs entirely.

## Repository Layout

```text
src/
  agent.py                 LiveKit agent entrypoint
  session.py               AgentSession lifecycle and prompt setup
  clinical_translation.py  Cloud-safe/local-safe translation prompt helpers
  deidentification.py      Deterministic PHI-like redaction helpers
  clinical_facts.py        Reviewable clinical fact primitives
  openmrs_payload.py       OpenMRS-style draft payload builder
  transcript.py            Optional transcript persistence with redaction
docs/
  hackathon-dossier.md
  submission-form-fields.md
  demo-script.md
  security-model.md
  proposal-positioning.md
tests/
  test_deidentification.py
  test_openmrs_payload.py
```

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
```

Use demo or test credentials only.

## Example Local-Only Configuration

```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

STT_PROVIDER=local
TTS_PROVIDER=local
LLM_PROVIDER=local

ENABLE_TRANSCRIPT_SAVE=false
TRANSCRIPT_REDACTION_ENABLED=true
TRANSCRIPT_RAW_STORAGE_ALLOWED=false
```

The `local` providers are the intended next integration point for whisper.cpp,
Piper, and llama.cpp.

## Hackathon Positioning

Recommended short description:

> OpenMRS LiveKit is a fully local clinical interpreter and encounter compiler.
> It runs voice capture, transcription, translation, and structured extraction
> on clinic hardware, de-identifies text before model inference, and produces
> clinician-reviewed OpenMRS draft observations without sending PHI to cloud AI
> services.

Target track: Clinical Track.

Distribution model: fully open source.

License: MIT.

## Status

Working prototype for the OpenMRS AI Hackathon 2026. The repository contains the
LiveKit agent foundation and the first OpenMRS-specific safety primitives. It
still needs production hardening, a review UI, site-specific concept mapping,
and validated local model packaging before clinical use.

## License

MIT.
