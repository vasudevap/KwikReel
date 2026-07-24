# ADR-010 — Proposal provenance: `disposition` over binary `origin`; bounded history

**Status:** Accepted — owner-approved 2026-07-24 (pre-ADP course correction).
**Refines:** [ADR-006](ADR-006-incremental-staged-build.md) — the **evidence mechanism** of *assists earn their place* (from binary `origin` to `disposition`). ADR-006's approval gate, transparency requirement, and stop/de-scope triggers stand unchanged; this makes the second trigger actually measurable.
**Relates to:** [ADR-008](ADR-008-prototype-before-contract-freeze.md) (§4 amendments expected before WO-101), [ES-001](../specs/ES-001-manual-editor-core.md) §4/§5.
**Authorizes nothing.**

## Context

The review tested whether `origin` (`proposed|user`) plus the single retained "last proposal" can distinguish the five states a proposal passes through — accepted, adjusted, dismissed, rerun, superseded — and found it distinguishes only **two**:

- **Adjusted** and **dismissed** are both `origin=user` with the proposal retained, separable only by "is the result the full clip?" — which collides with a legitimate adjust-to-full and with the §5.2.5 full-clip fallback.
- **Rerun** and **superseded** are not representable: a re-run overwrites the prior proposal.

ADR-006 and ROADMAP both claim the assists-earn-their-place trigger is "readable directly from `origin` … kept vs discarded." Binary `origin` conflates a 0.2 s accepted nudge (assist succeeded) with a total re-do (assist failed), so the trigger is **under-determined by the very field said to make it a query.** ADR-008 added `proposals` (the last proposal) but stopped short of recording the user's terminal action — so it caught half the gap.

## Decision

- Add a per-field **`disposition`** to each retained proposal: `pending | accepted | adjusted | dismissed`, set by the user's terminal action. `pending` is promoted to `accepted` when the stage is approved (approving the stage accepts untouched proposals).
- **Refined "assists earn their place" metric.** Read `disposition` across clips at the **trim-stage approval snapshot**: `accepted` and `adjusted-within-tolerance` count as **kept**; `dismissed` and `adjusted-beyond-tolerance` count as **not kept**. Tolerance (how far a hand-tuned in/out may sit from the proposal and still count as kept) is a config/UI value, **not pre-registered** (ADR-006 retired that regime). This is the evidence that fires ADR-006's stage-level de-scope, now a real query rather than an inference.
- **Proposal history is deferred to M2 and bounded when it arrives.** M1 keeps only the **latest** proposal per field plus its `disposition` (O(1) per field). The metric snapshots terminal disposition at stage approval, so intermediate re-runs need not be retained to compute it. When M2's re-run/supersession-heavy flows arrive, history is a **bounded** record (last-N, or last-per-field-per-stage, with a hard cap) — **never an unbounded append-only log.**
- **Retention / privacy (why bounded, not an audit log).** `disposition` and the single retained proposal are O(1) per field; `reasons` carry signal ranges and human-readable text — **no media and no identity** (M1 has no `people_count`). All of it lives only in `project.json`, which is gitignored and never committed. An unbounded event log would grow without limit inside a file that embeds absolute private paths; a bounded record preserves the audit value without that retention hazard. The `disposition` model is therefore the correction, **not** a general append-only history.

## Consequences

- All five proposal states are distinguishable — accepted/adjusted/dismissed directly; rerun via the fresh `pending` + a new `at`; superseded handled by bounded M2 history.
- The de-scope trigger becomes defensible and cheap; `PROJECT.md`'s "kept or minor-adjusted" measures resolve to a query over `disposition`.
- Small schema addition (one enum per proposal); no unbounded growth; no new privacy surface.
- ES-001 §4/§5 are amended accordingly **before WO-101 freezes contracts** (ADR-008's amendment path). WO-101/103/110 code the field and its invariants.
