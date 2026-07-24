# Roadmap — AI Vacation Reel Agent

**Status:** **Accepted — owner-approved 2026-07-23.** Re-sequenced per ADR-007.
**Governing:** `_oversight/DELIVERY-PLAYBOOK.md` (normal Direction → Specification → build flow); build method **ADR-006**; sequencing **ADR-007**; form factor **ADR-005**.

## What changed, and why

The previous roadmap was validation-first: a pivotal ranking experiment gated everything. The 2026-07-23 pivot removed that autonomy — every assist is now a proposal the user approves — so ADR-006 retired validation-first along with `VALIDATION-PLAN.md`. **No experiment ever ran.**

ADR-006 then sequenced the build manual-first: three milestones of hand-editing before any AI. **ADR-007 corrects that.** For a project whose whole value is AI-proposed edits under human control, a manual-only first increment is strictly worse than CapCut — infrastructure dressed as a deliverable. Assists are now ordered by **tractability**, and each ships with the controls that override it.

## Milestones

Each milestone ships **a usable product to the owner**, who is the sole user at this stage. There is no release bundling and no packaging work in scope.

| M | You get | AI proposes | Exit gate |
|---|---|---|---|
| **M1** | Import from a chosen folder, in order → **AI trim** (per-clip button and "trim all"; adjust or remove any suggestion) → timeline → render → export **with and without music** | In/out points per clip, each with a plain-language reason | Import a real day, AI-trim it, export a reel worth keeping; save → reopen identical |
| **M2** | **+ AI sequence** — one "Organize timeline" action, **undoable wholesale**; include/exclude, reorder, delete, restore | Which clips are in, and their order — reasons for picks **and** rejections | Reviewing the proposal beats ordering from scratch |
| **M3** | **+ AI speed** — per-segment rate controls | Speed ramps: faster through low-interest spans, slower on key moments, beat-aligned on opt-in | Proposed ramps kept on most clips |

**Every exit gate additionally requires the milestone to work on a real full day of footage (~50 clips), not a curated subset** (ADR-007). Hardening is folded into each milestone; there is no trailing hardening phase.

## M1 starts with a prototype

Per **ADR-008**, the first work in M1 is a clickable prototype with fake data — real thumbnails, faked waiting times, and deliberately bad AI suggestions. It produces two things: an agreed flow, and a list of gaps in the ES-001 schema. Those gaps are amended before any schema becomes code.

It is not a design exercise. Changing a screen with fake data behind it takes minutes. Changing a schema after eight Work Orders have implemented it is a migration across every saved project.

## The internal checkpoint inside M1

M1 is the largest and riskiest milestone — it carries the media pipeline *and* the first assist. Within it, the pipeline must work first: **import → timeline → render → export**, proving FFmpeg concat and 9:16 crop, *before* the trim proposer is layered on.

This is a **build checkpoint, not a release.** Nothing ships at the checkpoint. Its purpose is that the renderer and the trim proposer are never debugged at the same time.

## Two properties this sequence preserves

**Every assist arrives with its own override controls, in the same milestone.** M1 ships AI trim *and* trim adjustment. M2 ships AI sequencing *and* delete/restore/reorder. You never receive a proposal you cannot overturn — the pairing rule from ADR-007, and the thing the pivot was actually protecting.

**Each assist is individually disposable.** M1 leaves a working pipe underneath. If AI trim proves bad, it de-scopes to manual trimming (still transparent, still gated) and M2 proceeds regardless. The product survives the loss of any assist, or of all three.

## Stop / de-scope triggers

From `PROJECT.md`, locked by ADR-006, checked at every milestone close:

1. **No convenience win.** Finishing a reel takes as long as the manual CapCut evening → conclude as a portfolio piece.
2. **An assist is net-negative** → de-scope that stage to manual. Stage-level, not project-level. Evidence is readable directly from `origin` in `project.json`: proposals kept versus discarded.
3. **Absorption.** A platform ships this same transparent, approvable, clip-by-clip staged flow → reassess differentiation. More platform *automation* is explicitly not a trigger.

## Deferred, not deleted

- **Real-user validation.** ADR-006 makes it binding that real users exercise the tool before it is called *good*. It no longer gates the build — the owner is the sole user at this stage — and returns when the question becomes "is this good?" rather than "is this useful to me?"
- **Packaging and distribution**, per-clip audio retention and ducking, filters, ML-based interestingness, saliency reframing, NLE export. Each requires its own decision; none is authorized here.

## The drift risk this roadmap carries

Validation-first guarded against apparatus quietly becoming product. That risk is gone; another replaces it. **Owner approval is the acceptance gate at every milestone, and approving one's own work reliably overestimates its quality** (ADR-006). While the owner is the only user this is acceptable and explicit. It stops being acceptable the moment anyone claims the product is good — at which point the deferred real-user check is owed, not optional.
