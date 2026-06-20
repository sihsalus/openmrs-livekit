# OpenMRS AI Hackathon 2026 Dossier

## Project Name

OpenMRS LiveKit: Privacy-Preserving Clinical Translation

## Target Track

Clinical Track

Secondary fit: Implementer Track, because the same pipeline can support
localization and low-resource clinic workflows.

## Problem

Many clinics serve patients whose preferred language, health literacy, or local
terms do not match the clinician's documentation language. Real-time
interpretation is often unavailable, and after the visit the clinician still
needs structured OpenMRS data. Generic ambient scribes introduce privacy and
clinical safety risk if they stream raw PHI to cloud models or write directly to
the EMR.

## Proposed Solution

The prototype uses LiveKit to listen to a clinical conversation, translates each
turn between clinician and patient, de-identifies the text before external AI
calls, and compiles the same encounter stream into a reviewable OpenMRS draft.
Each candidate fact keeps evidence, confidence, speaker, and timestamp metadata.
The clinician approves or rejects each field before anything is written.

## Architecture

- LiveKit room captures audio from clinician and patient devices.
- STT converts speech to text using configured providers.
- De-identification gateway replaces emails, phone numbers, IDs, dates, UUIDs,
  and known local entities with deterministic placeholders.
- Translation prompt preserves clinical meaning, negation, uncertainty,
  medication names, dosages, and redaction placeholders.
- Clinical facts ledger stores candidate facts with evidence and review status.
- OpenMRS payload builder prepares draft encounter and obs JSON from approved
  facts only.
- Human review UI receives draft events and performs the final approval step.

## OpenMRS Interaction

Demo interaction model:

- Use synthetic OpenMRS patient, visit, encounter type, location, provider, and
  concept UUIDs.
- Generate OpenMRS-style draft encounter payloads locally.
- Include only approved facts in `obs`.
- Keep low-confidence or incomplete facts in the review queue.
- Keep the default demo path read-only and synthetic.

Production interaction model:

- Read patient, visit, encounter type, concept, and form metadata through
  OpenMRS REST or FHIR APIs.
- Submit approved observations only after clinician review.

## Infrastructure Requirements

Connectivity mode: Hybrid.

Minimum demo hardware:

- Clinic laptop or mini PC running the LiveKit agent and OpenMRS bridge.
- Browser or mobile device for clinician audio.
- Browser, tablet, or ESP32/edge audio endpoint for patient audio.
- Optional local network only mode for synthetic demos.

Cloud dependencies are configurable by provider. The privacy boundary is the
de-identification gateway; production deployments should use local models or
contractually protected vendors when PHI may be present.

## Safety And Privacy

- Transcript persistence is disabled by default.
- Redaction is enabled before transcript persistence.
- Raw transcript storage requires explicit configuration.
- No autonomous diagnosis, prescribing, or order placement.
- No automatic OpenMRS writes.
- Every extracted fact must remain traceable to an evidence snippet.
- Demo data must be synthetic.

## Distribution

Repository: MIT-licensed open-source prototype.

Distribution model: containerized LiveKit agent plus OpenMRS sidecar service.
The OpenMRS UI integration can be delivered as an ESM side panel for review and
approval.

## Community Impact Statement

OpenMRS is used in clinics where language access, bandwidth, and staffing vary
widely. This project focuses on a narrow but high-value workflow: helping a
clinician and patient understand each other in real time while producing a
reviewable OpenMRS encounter draft. It avoids the unsafe pattern of a black-box
ambient scribe writing directly to the EMR. Instead, it keeps a human in the
loop, de-identifies text before cloud AI calls, preserves evidence for every
clinical fact, and supports hybrid or local deployment. The result is a reusable
foundation for translation, documentation assistance, and structured encounter
capture in low-resource settings without forcing clinics to choose between AI
assistance and patient privacy.
