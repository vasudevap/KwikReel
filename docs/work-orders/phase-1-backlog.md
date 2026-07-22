# Phase 1 backlog — Validation apparatus

**Status:** Draft backlog. **These are not yet approved Work Orders.** File scopes, validation gates, and execution packets must be frozen before an ADP is authorized.
**Governing:** `docs/specs/VALIDATION-PLAN.md`; sequencing locked by ADR-004.

**Resequenced 2026-07-20.** The previous backlog mapped WOs to the old roadmap, where model-based editorial work sat at Phase 4 behind a review loop. Under ADR-004 the pivotal ranking experiment moves to Phase 1 and gates everything downstream.

## What authorizes this phase

Phase 1 is **Stage B (Validation)**, not Stage C (Specification). The work is authorized by the validation plan rather than by an Engineering Specification, because the ES cannot honestly be written until EXP-003 reports — its architecture would be specified around an unproven claim.

Phase 1 Work Orders still carry full WO discipline: scope, allowed file scope, exclusions, validation gates, dependencies, stop-and-ask triggers. What they do not carry is product authority.

**Everything here is evaluation apparatus.** It is permitted to be ugly, CLI-only, and throwaway. Interface work, packaging, and polish are stop-and-ask. Apparatus survives into Phase 2 only by explicit decision in the Phase 2 ES, never by inertia.

## Phase 1 — Validation apparatus

| ID | Outcome | Serves | Depends on |
|---|---|---|---|
| WO-001 | Repository bootstrap, reproducible local environment, fixture manifest, **media-never-in-Git guard verified by a test** | all | ADR-001, ADR-004 accepted |
| WO-002 | Consent record and deletion workflow; synthetic-ID mapping stored separately from corpus | EXP-000 | **ADR-002 accepted** |
| WO-003 | Corpus assembly and annotation tooling; held-out day sealed and excluded from all later file scopes | EXP-000 | WO-002 |
| WO-004 | Competitive-floor harness: run the same day through each incumbent, capture outputs, blind scoring rubric | EXP-001 | WO-003 |
| WO-005 | Media inventory and proxy generation with non-destructive source index | EXP-002 | WO-001 |
| WO-006 | Technical quality and near-duplicate analysis with audit schema | EXP-002 | WO-005 |
| WO-007 | **Heuristic baseline ranker** — duration, face count, sharpness, motion energy. Built deliberately well; a weak baseline invalidates EXP-003 | EXP-003 | WO-006 |
| WO-008 | **Model-assisted ranker** — rubric-scored, temperature 0, batch rank-normalized, pairwise comparison on borderline candidates | EXP-003 | WO-006 |
| WO-009 | **Ranking comparison harness** — Spearman vs. pooled human ranking, margin over baseline, held-out discipline enforced in code | EXP-003 | WO-007, WO-008 |
| WO-010 | Subclip window proposal: motion peaks, audio events, face saliency; IoU scoring against human windows | EXP-004 | WO-006 |
| WO-011 | Apple Silicon throughput benchmark, instrumented end to end | EXP-007 | WO-005 |
| WO-012 | **Integration verification:** run the full apparatus on the corpus, publish evidence, update the evidence ledger | all | WO-004, WO-009, WO-010, WO-011 |

## Deferred until validation reports

Not scheduled, and deliberately not decomposed. Specifying them now would mean designing around an unproven claim.

| Phase | Outcome | Unblocked by |
|---|---|---|
| 2 | Event clustering, constrained chronological selector, timeline schema v1, beat-aware timing, planner-to-renderer integration, 9:16 render, selects/rejects manifest | EXP-003 passes → Phase 2 ES |
| 3 | Review path: lock, remove, restore, regenerate, provenance display, subclip adjustment | Phase 2 exit |
| 4 | Improved subclip extraction, event-balance tuning, opt-in cloud-VLM comparison | EXP-008 passes; ADR-002 governs the cloud arm |
| 5 | Packaging, NLE interchange decision, cost/privacy and productization assessment | EXP-009; competitive floor re-measured |

## Proposed lanes

Lane partitioning is valid only once file scopes are disjoint and the WO graph is acyclic. Proposed shape:

```text
WO-001 → WO-002 → WO-003 → ┬→ WO-004 ─────────────┐
                            │                      │
WO-001 → WO-005 → WO-006 → ┼→ WO-007 → WO-009 ────┼→ WO-012
                            ├→ WO-008 ─────────────┤
                            └→ WO-010 ─────────────┤
WO-001 → WO-005 → WO-011 ─────────────────────────┘
```

WO-007 and WO-008 are the natural parallel pair — the baseline and the model ranker are independent implementations scored by a common harness. They must have **disjoint file scopes** and neither may write to the comparison harness, or the lock is broken.

WO-012 is the required convergence verification.

## Definition of ready for Phase 1

- ADR-001 (prototype shape), **ADR-002 (privacy and data posture)**, ADR-003 (music and licensing), and ADR-004 (validation-first sequencing) all Accepted.
- `VALIDATION-PLAN.md` accepted **with its thresholds pre-registered** — no experiment starts against an unset bar.
- Each WO declares scope, allowed file scope, exclusions, validation gates, dependencies, and stop-and-ask triggers.
- WO-007, WO-008, and WO-009 additionally satisfy `_oversight/templates/ai-component-gate-checklist.md`, since their output is probabilistic and standard gates cannot express "beats the baseline."
- The held-out day is named and excluded from every WO's allowed file scope.
- Owner explicitly authorizes an ADP. Until then this is planning only.

## Standing stop-and-ask triggers for this phase

Beyond the playbook defaults, an implementing agent must stop and ask if it finds itself:

- relaxing or reinterpreting a pre-registered threshold;
- reading, scoring against, or tuning on the held-out day;
- sending original media, audio, or full video anywhere off-device (ADR-002 permits extracted keyframes only, under per-run opt-in, in EXP-003's cloud arm alone);
- building interface, packaging, or polish work;
- adding a dependency whose licence would restrict distribution (ADR-003).
