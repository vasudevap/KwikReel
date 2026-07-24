# ADR-008 — Prototype the interface before freezing contracts as code

**Status:** Accepted — owner-approved 2026-07-23
**Relates to:** [ADR-007](ADR-007-build-sequencing.md) (build sequencing — unchanged), [ES-001](../specs/ES-001-manual-editor-core.md)

This adds a step at the start of M1. It does not change the milestone sequence, the pairing rule, or the hardening rule from ADR-007. It does **not** authorize implementation — that still requires an authorized ADP.

## Context

This product's value is reviewing and overriding AI suggestions. Whether that works is a question about a screen, not a schema. You cannot tell whether a trim is good by reading `{"in_s": 3.0, "out_s": 8.0}` — you have to watch the clip.

ES-001 freezes the `project.json` schema and the component contracts. Freezing early is right: it stops M2 and M3 needing migrations. But it was done on paper, and paper hides gaps.

One gap was already found this way. `origin` recorded *whether* a value came from the machine but not *what the machine proposed*, so adjusting an AI trim destroyed the evidence needed to judge the AI at all. It was caught by writing the spec. A working screen would have caught it faster, and would likely find more.

The cost asymmetry is the whole argument. Changing a screen with fake data behind it takes minutes. Changing a schema after eight Work Orders have implemented it is a migration across every saved project.

## Decision

**Build a clickable prototype of the full M1 flow before WO-101 turns any schema into code.**

The prototype is built in **React with fake data** — the same framework being shipped, so it becomes the real frontend shell rather than throwaway work.

Three rules make it honest, and all three are required:

1. **Fake the waiting.** Analysis and rendering each take around five minutes (ES-001 §9). A prototype that responds instantly produces a flow that feels wrong in real use. Artificial delays match the stated targets, so questions like "does *Trim all* need a progress bar?" and "can the user keep working while it runs?" get answered before anything is built.
2. **Make the fake AI wrong on purpose.** Seeded fake data must include bad proposals — a trim that cuts the good part, and a clip where the proposer gives up and returns the full clip. Perfect fake data produces a review screen that is never exercised, and reviewing is the product.
3. **Use real thumbnails.** Frames pulled from actual footage, not grey boxes. A 50-clip timeline made of placeholders cannot tell you whether a 50-clip timeline is readable.

**The prototype produces two outputs:** an agreed flow, and **a written list of gaps in the ES-001 schema.** Anything it finds is amended into ES-001 *before* WO-101 freezes the schema as code.

**It is explicitly not a design exercise.** The job is flow and data. Visual polish — colour, spacing, typography — is out of scope and a stop-and-ask if it starts consuming effort.

## Consequences

- Schema gaps are found when they cost minutes instead of a migration.
- The prototype is not throwaway; it becomes the frontend shell that later Work Orders fill in.
- **The frontend stops waiting on the backend.** It develops against the prototype's fake data and is wired to the real API when that lands, so the interface is never the last thing built.
- M1 starts slower. The first work produces no functioning software, which is the cost of finding out what to build before building it.
- ES-001 is Accepted, so any gap the prototype finds is a recorded amendment to an accepted spec — visible in the history, not a quiet edit.
- The risk is polish creep. Rule 3 above and the stop-and-ask are the mitigation; a prototype that drifts into visual design has stopped doing its job.
