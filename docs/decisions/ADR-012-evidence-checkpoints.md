# ADR-012 — Pre-ADP and per-milestone evidence checkpoints

**Status:** Accepted — owner-approved 2026-07-24 (pre-ADP course correction).
**Refines:** [ADR-006](ADR-006-incremental-staged-build.md) — adds lightweight, **non-pre-registered** evidence checkpoints to the per-stage acceptance regime. Does **not** restore validation-first sequencing, pre-registered thresholds, the ranking corpus, or PROP-01.
**Relates to:** [PROJECT.md](../../PROJECT.md) success measures, [ROADMAP](../../ROADMAP.md) gates, [EVIDENCE-LEDGER](../specs/EVIDENCE-LEDGER.md), [competitive-landscape](../research/competitive-landscape.md).
**Authorizes nothing.**

## Context

ADR-006 rightly retired the autonomous-ranking validation programme, but the review found it **over-corrected**: the pivot's *new* pivotal belief — that users value explained, approvable assistance enough to review it rather than tap once — is graded `assumed` with **no test scheduled**, and the competitive-floor comparison was retired though it was never autonomy-dependent. The project should not swing from heavy pre-registration to *no* early evidence. The checkpoints below are cheap and — per the review's own caution — **timed to WO-100 / the M1 exit, not as hard ADP blockers.**

## Decision — three checkpoints, none pre-registered, each a recorded honest-outcome check

- **CP-1 · Preference probe (the pivotal belief).** Using the WO-100 clickable prototype (fake data, deliberately-bad proposals), show 1–2 real memory-keepers the review-and-approve flow and record whether they would review explained proposals or just want one tap.
  **Timing: after WO-100 exists, before M1 is called useful.** Not an ADP blocker — it needs the prototype to run against, and it gates *belief*, not *building the prototype*.
- **CP-2 · Competitive-floor comparison.** The owner runs one real vacation day through Apple Photos Memory / Google Photos / CapCut and scores each against "would I post this?", filling the competitive-landscape floor table. Needs no code and no media collection beyond the owner's own footage viewed in those apps.
  **Timing: any time before the M1 exit gate; recommended early** because it can cheaply revise the whole framing. Not an ADP blocker.
- **CP-3 · Performance spike.** Confirm the ES-001 §9 ≤5-min proxy/analysis/render targets are achievable on the target Apple Silicon Mac.
  **Timing: at the M1 internal checkpoint (once ingest + render exist), before the §9 numbers are treated as pass/fail gates — not before ADP.** Justification: a pre-ADP spike would need real/synthetic media and a partial renderer that do not yet exist; the real 50-clip exit gate measures this anyway, and the checkpoint de-risks it one step earlier.

**Blocking calibration (recorded so it is not re-litigated):** none of CP-1/2/3 blocks **ADP authorization.** They block, respectively, calling M1 *useful* (CP-1), the M1 *exit* framing (CP-2), and treating §9 as *gates* (CP-3).

## Consequences

- The belief the whole roadmap rests on gets a near-free early test; the competitive floor stops being assumed; perf risk is caught at the checkpoint rather than at the exit gate.
- None of it re-imposes the retired pre-registration regime or blocks authorizing the fake-data prototype.
- The **binding real-user validation** before the product is called *good* (ADR-006/007) still stands. CP-1 is a cheap early read, **not** that gate.
