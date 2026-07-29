# Sample-media testing strategy

> **⚠️ PRE-PIVOT — retained for history (banner added 2026-07-24).** This references `VALIDATION-PLAN.md` (retired) as authoritative for thresholds and lists pre-registered gates (≥95% recall, etc.) — a regime **retired by ADR-006.** Per-stage acceptance on real footage plus the ADR-012 checkpoints replace it. The **corpus shape and consent handling** below remain a useful reference under ADR-002/013; the **thresholds and held-out discipline do not apply.**

**Status:** Draft — owner approval required.
**Relationship to other artifacts:** this document defines the corpus shape and evaluation *protocol*. `docs/specs/VALIDATION-PLAN.md` is authoritative for **which experiments run, in what order, and against which pre-registered thresholds**. Where the two disagree on a threshold, the validation plan wins.
**Consent and data handling are governed by ADR-002.** No media may be collected before it is accepted.

## Corpus

Create consented, local-only test days; do not commit media to Git. The `.gitignore` enforces this, and a test in WO-001 verifies the guard actually holds.

| Set | Purpose | Required annotation |
|---|---|---|
| A: Normal day | 30–50 varied clips: travel, activity, people, food, scenery, evening. | Event order, must-keep, acceptable alternatives, people/activity coverage. |
| B: Adversarial | Blur, lens obstruction, accidental recordings, duplicates, long static shots, mixed orientation/FPS. | Usable/reject label and reason. |
| C: Narrative stress | Repeated activities, out-of-order clocks, multiple locations, missing metadata. | Ground-truth event clusters and chronology exception notes. |
| D: Music stress | Three royalty-free tracks with different BPM/sections. | Beat/downbeat and section labels for a sampled interval. |

Use synthetic IDs and a separate encrypted/local annotation store. Faces of children require explicit consent; disable any identity-level analysis.

## Evaluation protocol

1. Freeze a corpus manifest and annotations before each planner comparison.
2. Run the same input/settings through the POC and each benchmark product.
3. Have two reviewers independently score the output blind where feasible.
4. Record tool/model versions, run time, hardware, settings, manifest, render hash, and reviewer disagreements.

## Metrics and gates

| Area | Measure | Gate |
|---|---|---|
| Technical filtering | Recall of must-keep usable clips; precision of rejected unusable clips. | ≥95% must-keep recall; ≥80% seeded-unusable precision. |
| Duplicate control | Duplicate pairs represented more than once without annotation justification. | ≤10%. |
| Chronology | Correct adjacent event transitions. | ≥90%, excluding labelled deliberate reorders. |
| Coverage | Must-keep events and requested people represented. | 100% of locks/must-keeps; no unlabelled person-balance claim. |
| Duration | Absolute error from requested target. | ≤0.5 seconds unless an explicitly recorded shorter decision. |
| Music | Eligible cuts near an allowed beat. | ≥70% within 150 ms; no requirement to cut every beat. |
| Human quality | “Credible first draft” rating and correction time. | ≥2/3 drafts; median <10 minutes. |

Failures are evidence, not reasons to tune against the held-out set. Keep one day held out for final comparison.
