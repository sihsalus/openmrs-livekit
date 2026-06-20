# 3-5 Minute Demo Script

## 0:00-0:30 - Problem

"In many OpenMRS clinics, the clinician and patient may not share the same
language or clinical vocabulary. Interpretation is scarce, and documentation
still needs to become structured OpenMRS data. This prototype combines real-time
translation with a human-reviewed encounter draft."

## 0:30-1:15 - Architecture

Show the repo and architecture diagram or README.

"Audio enters through LiveKit. STT creates turns. Before cloud AI sees the text,
the de-identification gateway replaces PHI-like values with deterministic
placeholders. The translation prompt preserves medical meaning and placeholders.
The encounter compiler builds facts with evidence, confidence, speaker, and
review status. OpenMRS receives only approved draft data."

## 1:15-2:30 - Live Flow

Use synthetic data.

Doctor: "Dile a Juana que su prueba de glucosa salio alta el 12/06/2026, pero
que no debe duplicar la metformina."

Show:

- redacted safe source text with `<KNOWN_ENTITY_1:...>` and `<DATE_1:...>`;
- translated patient-facing message;
- clinical fact candidates such as elevated glucose and medication caution;
- evidence snippets attached to each fact.

Patient response: "Entiendo. No soy alergica a medicamentos, pero me mareo en
las mananas."

Show:

- translated clinician-facing message;
- extracted allergy denial and symptom;
- missing-fields prompt if onset/duration is missing.

## 2:30-3:30 - OpenMRS Review

Show the review bundle:

"The system does not write automatically. The clinician approves, edits, or
rejects each fact. Only approved observations become OpenMRS-ready payloads.
Low-confidence facts stay in the review queue with their evidence."

## 3:30-4:30 - Safety

"Transcript save is off by default. If enabled, redaction runs first. Raw
storage requires explicit configuration and should only be used under a proper
privacy agreement. The system does not diagnose, order, or prescribe."

## 4:30-5:00 - Community Value

"The reusable contribution is not a single language pair. It is a safe pattern:
LiveKit voice capture, de-identified AI translation, evidence-backed encounter
facts, and OpenMRS human review."
