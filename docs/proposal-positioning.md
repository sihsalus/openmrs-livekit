# Proposal Positioning

## What The Hackathon Panel Is Likely Optimizing For

- A working AI solution, not only an idea.
- Clear interaction with OpenMRS.
- A practical clinic workflow.
- Human safety boundaries.
- Infrastructure requirements that an implementer can reason about.
- A scale-ready path for the OpenMRS community.

## Recommended Framing

Lead with:

> Real-time clinical interpreter for OpenMRS encounters that de-identifies text
> before AI calls and produces clinician-reviewed OpenMRS draft observations.

Avoid leading with:

> Voice agent from an ESP32 toy project.

The ESP32/LiveKit history is useful as implementation credibility, but it should
be a secondary detail: the team already has low-latency audio experience and can
support edge audio endpoints.

## Strongest Track

Clinical Track.

Reason: the visible user value is point-of-care translation plus safer encounter
capture. The implementer/developer angles are useful secondary benefits, but a
single clear track will score better.

## Demo Must Show

- OpenMRS patient context or synthetic OpenMRS identifiers.
- Doctor utterance.
- Redacted AI-safe text.
- Patient-facing translation.
- Extracted candidate facts with evidence.
- Clinician review queue.
- OpenMRS-style draft payload containing only approved observations.

## What To Cut From The Pitch

- Any claim of SOC 2 compliance.
- Any implication that the model diagnoses or recommends treatment.
- Any promise that the current prototype is production-ready.
- Too much focus on personalities, toys, children, or general voice-agent
  features.

## What To Emphasize

- Language access in low-resource clinics.
- De-identification before cloud AI calls.
- Human-in-the-loop review before OpenMRS writes.
- Evidence-backed facts, not free-form summaries.
- Hybrid deployment and optional local models.
- Reusable OpenMRS pattern: voice turn -> redaction -> translation -> fact ->
  review -> draft payload.
