# ADR-009 — Manual curation in M1; reachable exit gate

**Status:** Accepted — owner-approved 2026-07-24 (pre-ADP course correction; input: [PRE-ADP-REVIEW-2026-07-24](../reviews/PRE-ADP-REVIEW-2026-07-24.md)).
**Amends:** [ADR-007](ADR-007-build-sequencing.md) — the **M1 milestone contents and exit gate only.** The pairing rule, tractability ordering, hardening rule, and internal checkpoint stand unchanged. Read the two together.
**Relates to:** [ADR-006](ADR-006-incremental-staged-build.md), [ES-001](../specs/ES-001-manual-editor-core.md) (§1, §5.5, §10), [ROADMAP](../../ROADMAP.md).
**Authorizes nothing** — implementation still requires an authorized ADP.

## Context

ADR-007 fixed M1 = working pipe + AI trim, and placed include/exclude, delete, and restore in **M2**, alongside the AI selection assist. The pre-ADP review found this makes M1's exit gate — "export a reel worth keeping" — **unreachable**: AI trim removes dead air *within* a clip but cannot remove a *clip*, and M1 has no manual way to drop one. A real 50-clip day therefore renders as a 150–250 s concatenation of every clip in capture order — the commodity "everything montage" `PROJECT.md` explicitly says is not the product — and `target_duration_s` has no consumer.

The error was treating include/exclude/delete/restore as belonging to the M2 *assist*. They are the *manual controls*. ADR-007's pairing rule requires each assist to ship with the controls that override it; it does **not** require those controls to be withheld until the assist exists.

## Options considered

1. **Add manual curation to M1; keep the AI selection/order *assist* in M2 (recommended).**
2. Downgrade M1's exit gate to "a correctly trimmed, correctly rendered full-day sequence + lossless round-trip," moving reel quality to M2. Honest, but concedes M1 has no product value — the exact ADR-006 problem ADR-007 killed.
3. Move the whole selection *assist* into M1. Rejected: selection is the least-certain signal (ADR-007), highest-risk as a first assist, and unnecessary — manual curation suffices.

## Decision

Adopt option 1.

- M1 gains **manual** include/exclude, delete, and restore, operating on the **already-frozen** schema fields `included`, `deleted`, and their `origin`. These are flag toggles plus a list affordance, not a new subsystem — low marginal cost on M1.
- The **AI selection/ordering assist stays M2.** M1 has no proposer for inclusion or order; `proposals.included` / `proposals.order` remain `null` in M1.
- **Why this does not violate the M2 selection-assist boundary.** M2's boundary is the *assist* — a proposer that emits include/exclude + order with reasons and a wholesale undo. M1 ships only the *manual controls*. When the M2 assist arrives it **proposes into these same controls**, and the user overrides with them — exactly the pairing rule (an un-overridable proposal never reaches the user). Shipping the override controls early *satisfies* the pairing rule; it does not pre-empt the assist. No proposer, no counting, no identity — the M2/ADR-002 lines are untouched.
- **Exit gate, calibrated (per the review's own caution — do not overclaim).** M1's gate becomes: import a real day → manually curate to a short set → AI-trim the keepers → export → and judge the result **against that day's Apple Photos Memory, recording specifically why not if it falls short.** The bar is that M1 becomes **evaluable against the free alternative and plausibly worth keeping** — *not* that it is proven superior. Superiority is a real-user question, deferred (ADR-006/007).
- `target_duration_s` becomes a **displayed reference** (the timeline shows running total vs target); no optimizer, no enforcement. It stops being a dead field without adding selection logic.

## Consequences

- M1's exit gate is reachable and M1 can produce a short reel a person can actually assess.
- M1 grows slightly; the marginal cost is low (flag toggles on frozen fields), and the internal checkpoint (pipeline before proposer) is unchanged.
- The ES-001 §12 ambiguity ("undo history *beyond* delete/restore," which implied delete/restore was already in M1) is resolved: delete/restore **are** in M1, manually.
- ROADMAP's "M2 ships delete/restore/reorder" is corrected: those *manual controls* ship in M1; M2 ships the *assist* that proposes into them.
- ADR-007 is amended, not superseded. Anyone reading it must read this record alongside it.
