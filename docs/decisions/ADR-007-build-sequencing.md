# ADR-007 — AI trim in the first milestone; assists ordered by tractability

**Status:** Accepted — owner-approved 2026-07-23
**Amended by:** ADR-009 (2026-07-24) — manual curation added to M1's contents and the exit gate recalibrated to *evaluable, plausibly worth keeping*; the three audio modes are in ES-001 §8.2. Read the two together.
**Amends:** ADR-006 — **the sequencing clause only.** Every other clause of ADR-006 stands unchanged: the approval gate, the transparency requirement, "assists earn their place," and the stop/de-scope triggers are untouched.
**Governing:** [PROJECT.md](../../PROJECT.md), [ADR-005](ADR-005-editor-form-factor.md), [ADR-006](ADR-006-incremental-staged-build.md)

The milestone sequence, the pairing rule, and the hardening rule below are now binding, relaxable only by a new ADR. This does **not** authorize implementation — that still requires an authorized ADP.

## Context

ADR-006 fixed a build sequence: the mechanically simpler stages first — ingest, trim, timeline and manual edit, finalize, export, save — with the assisted selection/ordering stage sequenced late. Its rationale was sound on its own terms: build a working manual product first so every assist has a baseline to be judged against, keep each assist individually disposable, and leave the most ambitious cross-clip judgment until last.

In practice that sequence produced **three milestones of manual-only editing before any AI ran.** For a project whose entire value is AI-proposed edits under human control, the first usable increment was a manual editor competing directly with CapCut and iMovie — free, mature, and better. It was strictly worse than tools the owner already has.

Two facts about this project's actual situation were not reflected in ADR-006:

- **The owner is the sole user for the foreseeable term.** Marketing to others is explicitly deferred, so "release" means *a testable product the owner can use.* Under that definition a manual-only milestone has near-zero standalone value — it is infrastructure wearing the costume of a deliverable.
- **The pairing requirement is narrower than the sequence implied.** What actually matters is that **each assist ships with the controls that override it** — an un-overridable proposal is precisely the black box the 2026-07-23 pivot rejected. That is a pairing rule between an assist and its controls. It is not a mandate to complete *all* manual capability before *any* assist.

ADR-006 over-applied a narrow pairing rule into a broad manual-first sequence.

## Options considered

1. **Merge the pipe and AI trim into one first milestone; order assists by tractability (recommended).** First delivery is import → AI trim → export: immediately more useful than the free alternatives. Selection/ordering second, speed third.
2. **Retain ADR-006's sequence.** It optimizes for a de-risking benefit — an established manual baseline per assist — that the owner-only context does not need, at the cost of delaying all value by three milestones.
3. **Manual-first for every stage, then all assists.** A stronger form of option 2; rejected for the same reason, more so.
4. **Build all three assists concurrently on a minimal pipe.** Rejected: three assists in flight with no working reference product is exactly the concurrency ADR-006 rightly warned against.

## Proposed decision

Adopt option 1.

**Three milestones, each shipping a usable product to the owner:**

| M | Delivers |
|---|---|
| **M1** | Working pipe **+ AI trim.** Import from a user-specified folder in order; timeline; render; export with and without music. AI trim per clip and in bulk, every suggestion adjustable and removable |
| **M2** | **AI selection & ordering.** One action, undoable wholesale; include/exclude, reorder, delete, restore |
| **M3** | **AI speed ramping.** Per-segment rate controls; beat-aligned on opt-in |

**Assists are ordered by tractability, not deferred wholesale.** Trim is the most tractable signal and addresses the grind the owner named first — scrubbing every clip for its usable seconds. Selection and ordering follow. Speed is last because interest detection is the least certain signal of the three.

**The pairing rule replaces the manual-first rule.** Each assist ships in the same milestone as the controls that override it. No proposal reaches the user without the means to adjust or reject it. This preserves what ADR-006 was actually protecting.

**An internal checkpoint inside M1.** The media pipeline — import → timeline → render → export — must work before the trim proposer is layered on top. This is a *build checkpoint, not a release*: it preserves ADR-006's de-risking intent without spending a whole milestone on it, and it means the renderer and the trim proposer are never debugged simultaneously.

**Hardening is folded into every milestone.** Each milestone's exit gate requires it to work on a **real full day of footage (~50 clips), not a curated subset.** There is no trailing hardening milestone: a deferred-quality bucket is where quality goes to be deferred indefinitely.

**Real-user validation is deferred, not deleted.** ADR-006's requirement that real users exercise the tool before it is called good **stands**. It no longer gates the build, because the owner is the sole user at this stage. It returns whenever the question becomes *"is this good?"* rather than *"is this useful to me?"*

## Consequences

- The first delivery is genuinely better than the free alternatives rather than strictly worse. Value arrives at milestone 1 instead of milestone 4.
- **M1 becomes the largest and riskiest milestone**, carrying the media pipeline and the first assist together. The internal checkpoint is the mitigation and is not optional.
- ADR-006's "manual capability is the baseline for each assist" benefit is **weakened, and this is accepted.** The owner's manual behaviour is still available for comparison — trim controls ship alongside the trim assist — but it is no longer established across a complete manual product first. The assists-earn-their-place trigger still fires on the same evidence: proposals kept versus discarded, readable from `origin` in `project.json`.
- Speed moves from the middle of the sequence to last. Its schema fields were frozen in ES-001 §4, so the deferral costs no migration.
- Three milestones instead of five, with no release bundling and no packaging work in scope.
- ADR-006 is amended, not superseded. Anyone reading it must read this record alongside it.
