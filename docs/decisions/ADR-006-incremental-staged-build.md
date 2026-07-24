# ADR-006 — Incremental staged build with per-stage human approval

**Status:** Accepted — owner-approved 2026-07-23
**Amended by:** ADR-007 (2026-07-23) — **the sequencing clause only.** AI trim moves into the first milestone and assists are ordered by tractability. Every other clause below — the approval gate, the transparency requirement, "assists earn their place," and the stop/de-scope triggers — stands unchanged. Read the two records together.
**Refined by:** ADR-010 (2026-07-24) — the *assists-earn-their-place* evidence mechanism reads `disposition`, not binary `origin` — and ADR-012 (2026-07-24) — pre-ADP/per-milestone evidence checkpoints. Neither relaxes a clause below.
**Supersedes:** ADR-004 — Validation-first sequencing and kill criteria
**Relates to:** PROP-01 / MD-001 — the Validation-stage pilot was authorized for this project contingent on its ADRs. This ADR **withdraws this project from that pilot.** General acceptance of PROP-01 remains a separate MD-002 matter and is unaffected by this decision.

The sequencing, the approval gate, the transparency requirement, and the stop/de-scope triggers below are now binding, relaxable only by a new ADR stating what changed. This does **not** authorize implementation — Work Orders additionally require an authorized ADP.

## Context

ADR-004 adopted validation-first sequencing for one reason, stated plainly in that record: the project's entire reason to exist rested on an unproven capability applied **autonomously** — that model-assisted cross-clip ranking could out-select a human. If that claim were false, everything downstream became pointless, so it had to be tested before any specification was written.

The 2026-07-23 pivot removes the autonomy, not the capability. Selection and ordering, trim, and speed are all retained — but each is now a **proposal, presented transparently with its reasons, requiring the user's review and approval before the next stage runs.** The user can override any of them, and finishes the edit on the timeline regardless.

That change dissolves the risk structure ADR-004 was built to manage. There is no longer a single pivotal capability whose failure makes the rest pointless: **a weak assist produces a worse starting point, not a broken product.** The human still reaches a finished reel.

Consequently the machinery ADR-004 mandated — a pivotal experiment, an annotated corpus with pooled human reference rankings, pre-registered thresholds as a locked regime, and a ranking kill criterion — is now apparatus for a question the product no longer asks in that form. Retaining it would spend the most expensive part of the plan (roughly 30–40 hours of annotation, a held-out corpus, and a week-long pivotal experiment) validating an autonomy claim that has been withdrawn.

## Options considered

1. **Incremental staged build with per-stage approval (recommended).** Return to the playbook's normal Direction → Specification → build flow. Build the nine stages in dependency order; the owner's approval of each stage on real footage is the acceptance gate; each assist must earn its place or is de-scoped to manual.
2. **Retain ADR-004 as written.** Honest assessment: it would pre-validate an autonomous ranking claim the product no longer makes.
3. **Reduced formal validation on the assists only** — measure trim/speed/selection quality against a small labelled set before building the editor. Defensible, but it front-loads measurement apparatus ahead of the interaction surface whose value is the genuinely open question, and the approval gate already surfaces bad proposals immediately and cheaply.
4. **Drop governance entirely and build.** Rejected — it loses the honest-outcome and written-stopping-condition discipline that makes a negative result usable rather than embarrassing.

## Proposed decision

Adopt option 1.

**Sequencing.** The playbook's normal flow. Stages are built in dependency order, with the mechanically simpler, higher-certainty stages first — ingest, trim, timeline and manual edit, finalize, export, save — and the **assisted selection/ordering stage sequenced late**, because the user can select manually until that assist earns its place. This preserves a working product at every point in the build.

**The approval gate is the acceptance gate.** A stage is accepted when the owner uses it on real footage and approves its output. This replaces pre-registered thresholds as the primary evidence mechanism. The product-acceptance goals in `PROJECT.md` are checked at each stage boundary as goals, not as locked pivotal thresholds.

**Transparency is a standing requirement, not a feature.** Every machine proposal — selection, rejection, trim, speed — must carry a plain-language reason, must be overridable, and its rationale must persist in `project.json`. **A stage that cannot explain its proposals is not complete.** This is a stop-and-ask, not a judgment call an implementing agent may make.

**Assists earn their place.** If any assist is wrong often enough that reviewing and correcting it costs more than performing that step by hand, that stage ships manual-only — still transparent, still gated — and the AI is dropped from it. This is a recorded de-scope, not a project kill, and not something to argue around.

**Stop / de-scope triggers**, replacing ADR-004's kill criteria. Checked at stage boundaries:

1. **No convenience win.** If finishing a reel with the tool takes as long as the manual CapCut evening on real footage → conclude as a portfolio piece.
2. **An assist is net-negative** → de-scope that stage to manual. Stage-level, not project-level.
3. **Absorption.** If a platform ships this same transparent, approvable, clip-by-clip staged flow → reassess differentiation. More platform *automation* is explicitly **not** a trigger; it is the opposite of this product.

**What is withdrawn.** Validation-first sequencing; the pivotal experiment (EXP-003) and its ranking corpus; pre-registered thresholds as a locked regime; the ranking kill criterion; and this project's participation in the PROP-01 pilot. `VALIDATION-PLAN.md` is retired and replaced by light per-stage acceptance checks. The annotated ranking corpus is not built.

**What is retained from ADR-004.** Honest outcomes — a check that could not run is recorded with the exact command and the reason, never silently skipped. Written stopping conditions. The graded evidence discipline (fact / hypothesis / TBD). And the rule that a constraint recorded in an ADR changes only by a new ADR, never by drift.

## Consequences

- Something usable exists far sooner, and a working product exists at every point in the build sequence.
- The largest risk ADR-004 guarded against — building several phases on a false premise — is retired **by the pivot itself** rather than by an experiment.
- Evidence now arrives from real use at each gate rather than from a pre-registered experiment. That is weaker as measurement and stronger as product signal. The trade is deliberate and recorded here so it is not rediscovered as a surprise.
- The corpus and annotation programme shrinks dramatically. ADR-002 still governs any footage used — consent recorded before media is copied — but the 30–40 hour annotation effort is not built.
- **The drift risk moves, it does not disappear.** ADR-004 guarded against apparatus quietly becoming product. The new risk is **approving one's own work**: ADR-004's option-4 warning — that subjective judgment of one's own output reliably overestimates quality — now applies to the owner at every approval gate. Mitigation is binding: the one-sitting completion signal must be measured on real footage, and a small number of real users must exercise the tool before the product is called good. Owner approval alone is a build gate, not evidence of product quality.
- ADR-004's dependency on PROP-01 dissolves for this project; the MD-002 outcome no longer affects this project's sequencing.
