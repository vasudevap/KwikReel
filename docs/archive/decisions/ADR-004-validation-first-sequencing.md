# ADR-004 — Validation-first sequencing and kill criteria

**Status:** Superseded by ADR-006 (2026-07-23). Previously Accepted — owner-approved 2026-07-22.
**Supersedes:** the phase ordering in the previous `ROADMAP.md` draft, which placed model-based editorial experiments at Phase 4.

**Why superseded:** the 2026-07-23 pivot removed the *autonomy* from model-assisted ranking — selection, trim, and speed are now transparent proposals requiring user approval before the next stage runs. That dissolves the single pivotal capability this record was built to pre-validate. **No experiment ever ran and no corpus was collected.** Retained for history; the text below is the original record, unedited.
**Depends on:** the Validation-stage pilot authorized in MD-001 (PROP-01, piloting on KwikReel Stage B only). That authorization is contingent on this project's ADRs being accepted; general acceptance of the Validation stage is deferred to MD-002. If PROP-01 is rejected at MD-002, this ADR must be revised rather than silently retained.

**On acceptance:** validation-first sequencing and the three kill criteria below are locked, relaxable only by a new ADR stating what changed. Two pre-registration items from `docs/work-orders/phase-1-backlog-deltas.md` — the EXP-003 local-vs-cloud split (B-1) and a numeric differentiation margin for kill criterion 1 (B-2) — remain to be settled **before EXP-003 runs**; they do not gate this acceptance.

## Context

Roughly 60% of this pipeline is well-understood computer vision and signal processing: metadata extraction, blur and exposure measurement, perceptual hashing, scene detection, beat detection, FFmpeg rendering. The implementation risk there is low and the engineering is boring by design.

The project's entire reason to exist rests elsewhere — on an unproven claim: that model-assisted cross-clip ranking and subclip selection outperform a transparent metadata/CV heuristic baseline by enough to reduce human correction meaningfully. If that claim is false, the deterministic pipeline still runs, still renders, and still produces a montage — and it is a worse version of something Apple gives away free.

The previous roadmap placed that experiment at Phase 4, behind a rule-based POC and a review loop. That ordering would have built three phases of machinery before testing the assumption that decides whether any of it matters. It was not a project error: the governing methodology had no validation stage, so there was nowhere else to put an experiment.

There was also no written condition under which the project stops. Every gate asked "may we proceed?"; none asked "should we stop?"

## Options considered

1. **Validation-first with pre-committed kill criteria (recommended).** Resolve the pivotal uncertainty before spending specification machinery.
2. Keep the original ordering. Produces a demo sooner and a decision later; risks discovering the core claim is false after the review loop is built.
3. Build the deterministic pipeline as a product first, treat model ranking as a later enhancement. Defensible engineering, but it ships a commodity montage generator and defers the only question that distinguishes the project.
4. Skip validation, build the MVP, judge it subjectively. Fastest to something demonstrable, and the reason most projects of this shape fail quietly — subjective judgment of one's own output reliably overestimates quality.

## Proposed decision

Adopt option 1.

**Sequencing.** Validation (Phase 1) precedes specification. The pivotal experiment — model-assisted ranking versus heuristic baseline versus human reference — runs before the first-draft generator is specified, and its result gates the Engineering Specification.

Experiments are ordered **pivotal-first**: by "if this fails, what else becomes pointless?", descending. Prerequisites precede a pivotal experiment only where strictly required to run it. Building the heuristic baseline qualifies; building a review interface does not.

**Apparatus is not product.** Phase 1 code is evaluation apparatus: CLI-only, permitted to be throwaway. Interface work, packaging, and polish during Phase 1 are stop-and-ask. Apparatus survives into Phase 2 only by explicit decision in the Engineering Specification, never by inertia.

**Pre-registration.** Every threshold in `VALIDATION-PLAN.md` is recorded before the corresponding experiment runs. Relaxing a threshold after seeing a result is drift: it is a stop-and-ask, it is logged in the evidence ledger with what moved it, and it may not be done by an implementing agent under its own judgment.

**Held-out data.** One labelled day is reserved and untouched until the final comparison, and is excluded from every Phase 1 Work Order's allowed file scope.

**Kill criteria (hard constraints, locked here).** Relaxable only by a new ADR stating what changed:

1. **Ranking fails to beat the baseline.** If model-assisted ranking cannot outperform the transparent heuristic by a meaningful margin (EXP-003), the differentiating claim is false → conclude as a portfolio proof of concept.
2. **Correction burden stays high.** If median corrections-to-acceptance exceeds 8 on real users' own footage (EXP-008) → the review workflow costs what manual editing costs → conclude.
3. **Platform absorption.** If Apple or Google ships reviewable, explainable editorial reels natively → differentiation is gone → conclude. Re-measured at every phase close.

**Firing a kill criterion is a successful outcome**, not a failure to be argued around. The project is explicitly authorized to conclude that its central claim is false, and to write that conclusion up as the deliverable.

## Consequences

- The most decision-relevant evidence arrives first, and the largest wasted-effort risk is retired early. A false core claim costs roughly the validation phase rather than four phases.
- Nothing demonstrable exists until Phase 2. There is no impressive artifact to show during Phase 1, and the pressure to build one anyway is the main drift risk this ADR guards against.
- The project can now end deliberately rather than drifting. That is the point.
- The methodology dependency is real: this ADR assumes the playbook's Validation stage (PROP-01) exists. It was drafted alongside that proposal and stands or falls with it — if PROP-01 is rejected at MD-002, this ADR is revised.
