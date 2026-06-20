# Submission Form Fields

## Project Name

OpenMRS LiveKit: Privacy-Preserving Clinical Translation

## Target Track

Clinical Track

## Short Description

A LiveKit-based clinical interpreter for OpenMRS encounters. It translates
clinician-patient conversations in real time, de-identifies PHI-like text before
cloud AI calls, and compiles the encounter into clinician-reviewed OpenMRS draft
observations.

## Repository / License

Repository: https://github.com/sihsalus/openmrs-livekit

License: MIT

## Technical Architecture

Audio enters through a LiveKit room. STT produces clinician and patient turns. A
local de-identification gateway replaces PHI-like values with deterministic
placeholders before translation or transcript persistence. The translation layer
preserves clinical meaning, negation, uncertainty, medication names, dosages,
and placeholders. A clinical facts ledger stores candidate OpenMRS facts with
confidence, speaker, timestamp, evidence, and review status. The current demo
generates OpenMRS-style encounter draft JSON from approved facts only, while
low-confidence or incomplete facts remain in a review queue. A production bridge
can read patient, visit, concept, and form metadata through OpenMRS REST or FHIR
and submit only clinician-approved fields.

## Infrastructure Requirements

Connectivity: Hybrid.

Minimum hardware: clinic laptop or mini PC for the agent/bridge, clinician
browser or mobile device, and patient browser/tablet/ESP32 audio endpoint.

Cloud AI providers are configurable. Synthetic demos can run without storing
transcripts. Production PHI workflows should use local models or contractually
protected vendors.

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

## Video Demo Link

TBD

## Team Members / Contact

TBD
