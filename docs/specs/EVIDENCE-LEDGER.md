# Evidence ledger

**Status:** Initialized 2026-07-20. **No experiment has run. Every claim below is graded `assumed`.**
**Governing:** `_oversight/DELIVERY-PLAYBOOK.md` Stage B, artifact 6. Reviewed at every phase gate.

Grades: **measured** (an EXP reported it) · **estimated** (derived from measured data) · **assumed** (believed, untested) · **refuted** (an EXP disproved it).

The purpose of this table is to make it impossible to forget which of the project's load-bearing beliefs are actually known. A claim used in an ADR, an ES, or a pitch must be traceable to a row here.

## Load-bearing claims

| # | Claim | Grade | Moved by | Notes |
|---|---|---|---|---|
| C-01 | Model-assisted ranking beats a transparent heuristic baseline by a meaningful margin | **assumed** | EXP-003 | **Pivotal.** Kill criterion 1. The project's entire differentiation rests here. |
| C-02 | Incumbent free tools leave a real quality/control gap | **assumed** | EXP-001 | Competitive landscape reads vendor docs, not measured output |
| C-03 | Users accept a draft with ≤5 corrections | **assumed** | EXP-008 | North-star metric. Kill criterion 2 |
| C-04 | Deterministic filtering reliably rejects junk without losing must-keeps | **assumed** | EXP-002 | The floor the whole pipeline stands on |
| C-05 | Motion + audio + model window selection finds the good seconds | **assumed** | EXP-004 | Hardest ranked technical problem |
| C-06 | A 50-clip day processes locally in ≤15 min on Apple Silicon | **assumed** | EXP-007 | If false, hybrid keyframe architecture becomes default |
| C-07 | Time-gap + GPS clustering matches human event labels | **assumed** | EXP-005 | |
| C-08 | Selective beat alignment reads better than every-beat cutting | **assumed** | EXP-006 | |
| C-09 | Users prefer an assisted draft to full automation | **assumed** | EXP-009 | Drives product shape, not just marketing |
| C-10 | Someone would pay for this | **assumed** | EXP-009 | Weakest assumption in the project. 2–6 uses/year is hostile to subscriptions |
| C-11 | Apple/Google will not absorb this capability during the project's life | **assumed** | re-measured each phase close | Kill criterion 3. Cannot be settled once — it decays |

## Implementation reality

Separate from claims, per the playbook's *committed is not shipped* discipline.

| Item | State |
|---|---|
| Product code | **none** |
| Evaluation apparatus | **none** |
| Test corpus | **not collected** — consent workflow does not exist yet (WO-002) |
| Ground-truth annotations | **none** |
| Experiment results | **none** |
| Accepted ADRs | **ADR-001–004 all Accepted** — ADR-001/002/004 owner-approved 2026-07-22, ADR-003 on 2026-07-23 (Essentia dropped for its AGPLv3 licence; librosa/ISC only) |
| Git history | Initial documentation commit `e234a12` (`Initialize project direction artifacts`); no remote or published branch — see `handoff.md` |

## Log

| Date | Change |
|---|---|
| 2026-07-20 | Ledger initialized alongside the Stage B validation plan. All claims graded `assumed`. |
| 2026-07-22 | ADR-001 (prototype shape) accepted by owner. No claim grades changed; no implementation or media authorized. |
| 2026-07-22 | ADR-002 (privacy/data posture) and ADR-004 (validation-first sequencing) accepted by owner. ADR-003 held pending resolution of the Essentia (AGPLv3) vs distribution-restriction contradiction. No claim grades changed; no media collected. |
| 2026-07-23 | ADR-003 (music/licensing) accepted by owner. Essentia's AGPLv3 licence verified; B-5 resolved — Essentia dropped, beat detection uses librosa (ISC) only. Stage A ADR set complete; PROP-01 pilot launched. No claim grades changed; no media collected. |
