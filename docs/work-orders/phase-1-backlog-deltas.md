# Phase-1 backlog — proposed deltas

**Status:** Draft addendum · **proposed** — owner approval required. Does **not** modify the accepted-track [phase-1-backlog.md](phase-1-backlog.md); it proposes changes to it. Introduces no accepted decision and relaxes no constraint.
**Origin:** the architecture review / three-way triangulation (independent design ↔ project decisions ↔ generic reel-agent best-practice). Companion design: [../specs/COMPONENT-DECOMPOSITION.md](../specs/COMPONENT-DECOMPOSITION.md).
**Governing:** [ADR-004](../decisions/ADR-004-validation-first-sequencing.md), [VALIDATION-PLAN.md](../specs/VALIDATION-PLAN.md), [ADR-002](../decisions/ADR-002-privacy-and-data-posture.md), [ADR-003](../decisions/ADR-003-music-and-licensing-posture.md).

Two kinds of delta. **Part A** proposes build items (proto-WOs) buildable only after the ADR/validation/ADP gates. **Part B** proposes corrections to owner-gated documents — several are **stop-and-ask** (they touch pre-registered experiments, thresholds, or held-out discipline) and are therefore listed for owner ratification, **not applied here**.

---

## Part A — proposed build deltas

### Δ1 · Extend WO-001 — freeze the Plane-0 contracts
- **Outcome:** the artifact schemas, `ReasonRecord`, the `Scorer` interface, and the `run.json` provenance stamp (§1 of the decomposition) are frozen before any lane starts. These are the only coordination points; freezing them is what makes the lanes parallelizable.
- **Serves:** all. **Depends on:** ADR-001, ADR-004 accepted.
- **Allowed file scope:** contract/schema definitions + validators only. **Exclusions:** no signal logic, no scorers, no renderer.
- **Validation gate:** round-trip schema validation on fixtures; a media-never-in-Git guard test (already in WO-001).
- **Stop-and-ask:** any field that would carry media, GPS coordinates, or a person identity across a component boundary.

### Δ2 · New WO-009b — thin rank→manifest slice + early corrections read *(closes the proxy-gap risk)*
- **Outcome:** `emit_timeline` in **rank → manifest** mode (no render) turns the model ranker's output into a correctable manifest; an annotator records **edits-to-acceptance** on it for 1–2 **dev** days.
- **Why:** the pivotal gate (EXP-003, Spearman) sits two phases upstream of the north star (EXP-008, corrections). This gives an early, *directional* read on whether ranking quality translates to correction cost — using artifacts Phase 1 already emits, with no generator (C-7 full) and no review UI (C-12).
- **Serves:** de-risks the EXP-003 → EXP-008 transfer. **Depends on:** WO-009, C-11 in manifest mode.
- **Allowed file scope:** a manifest emitter + an annotation-capture script. **Exclusions:** no renderer, no beat alignment, no UI.
- **Validation gate:** manifest is human-readable and round-trips edits; corrections counted per the *count* definition (Part B-3).
- **Stop-and-ask / labelling:** this is a **directional pre-read, NOT EXP-008** and must never be reported as the Phase-3 gate; and it **must not touch the held-out day** — dev days only.

### Δ3 · Extend WO-008 — faithfulness gate on model reasons
- **Outcome:** every `ReasonRecord` the ModelScorer (and C-11) emits must cite `evidence_refs` that **actually moved the score**; a test rejects a reason whose cited features are non-causal (e.g. ablating them doesn't change the ranking).
- **Why:** the differentiator is *honest* explanation. Free-text model narration that sounds plausible but isn't causal is the one failure mode that makes the product worse than an honest montage. Selection is already protected (model can't bypass constraints); this protects the *rationale*.
- **Serves:** EXP-003 credibility + the north-star review path. **Depends on:** WO-008, Δ1 (`ReasonRecord`).
- **Allowed file scope:** ModelScorer reason-emission + a faithfulness test. **Exclusions:** no change to the scoring model itself.
- **Validation gate:** faithfulness test passes on fixtures; unfaithful reasons fail the WO.

### Δ4 · Extend WO-012 — golden-set / EDL-regression harness
- **Outcome:** fixed input clips → expected EDLs (`timeline.json`), asserted on every run; catches prompt/model/FFmpeg/library drift. This is also the mechanism for the **every-phase-close competitive-floor re-run** (kill criterion 3) — otherwise "we re-ran the floor" is not reproducible evidence.
- **Why:** the project iterates ranker prompts and re-measures incumbents at each gate; without a regression fixture, drift is silent.
- **Serves:** all; reproducibility and kill-criterion-3 hygiene. **Depends on:** WO-009, WO-012, `run.json` (Δ1).
- **Allowed file scope:** the regression harness + golden fixtures (fixtures are derivative artifacts — **not** committed; see `.gitignore`). **Exclusions:** the held-out day is never a golden fixture.
- **Validation gate:** a deliberate prompt/model bump is caught by the harness.
- **Note on determinism:** prioritise **decision/EDL determinism** (temp-0, pinned model, prompt hash, seeds) over bit-exact *render* determinism — the EDL is the load-bearing evidence, and multithreaded encoders fight bit-exactness for little gain.

**Revised lane note.** Δ2 attaches after WO-009; Δ4 folds into WO-012 convergence. WO-007/WO-008 remain the disjoint-scope parallel pair; Δ3 lives inside WO-008's scope; neither may write the comparison harness.

---

## Part B — proposed corrections to owner-gated docs *(flagged, not applied)*

Each names the file, the issue, and the proposed fix. Items marked **STOP-AND-ASK** change a pre-registered experiment, a threshold, or held-out discipline and require explicit owner ratification before EXP-003 runs.

| # | File | Issue | Proposed fix | Class |
|---|---|---|---|---|
| B-1 | `VALIDATION-PLAN.md` (EXP-003) + `ADR-002` | EXP-003 carries two questions — *model beats heuristic* and *frontier-cloud beats local* — and leaves "**which** model must beat the baseline for the project to live" unresolved at the kill gate. | Split: **EXP-003** = local-model vs heuristic (**gates kill criterion 1**); **EXP-003b** = cloud-keyframe vs local (informs architecture/privacy, **non-gating**). Define kill-criterion-1 "model" = **local**. | **STOP-AND-ASK** (experiment definition) |
| B-2 | `VALIDATION-PLAN.md` (EXP-003), `PROJECT.md`, `ADR-004` | The pivotal threshold is "ρ ≥ 0.6 **AND a meaningful margin**"; ρ is pre-registered but *the margin — the actual differentiation claim — is not a number*. | Pre-register a concrete margin before EXP-003 runs, e.g. **Spearman Δρ ≥ 0.10 over baseline AND pairwise win-rate ≥ 60% on borderline pairs** (owner sets the bar; the point is it must be numeric and fixed beforehand). | **STOP-AND-ASK** (threshold) |
| B-3 | `PROJECT.md` vs `sample-media-test-strategy.md` | North star is operationalised two ways: corrections **count** (median ≤5) and correction **time** (median <10 min). They are not interchangeable. | Make **count canonical**; demote time to a diagnostic. Fix the "Human quality" row in `sample-media-test-strategy.md`. | Doc integrity |
| B-4 | `VALIDATION-PLAN.md` vs `sample-media-test-strategy.md` | Corpus **set-label collision**: plan has D=held-out, E=music; the strategy table has D=music and omits the held-out set. A WO scoping "Set D" could reference the wrong set. | Align to `VALIDATION-PLAN.md` (D=held-out, E=music), which already wins by its own precedence rule; add the held-out row to the strategy table. | **STOP-AND-ASK** (held-out discipline) |
| B-5 | `ADR-003`, `prototype-definition.md` | `madmom` is excluded for its GPL licence, but "librosa **or Essentia**" is offered as the approved beat-detector — and Essentia is **AGPLv3**, *more* distribution-restrictive than GPL. Same rule that excludes madmom excludes it. | Drop Essentia from the approved path (**librosa / ISC only**) or mark it commercial-licence-required. Verify Essentia's exact licence before ratifying. **Resolved 2026-07-23 — AGPLv3 verified; Essentia dropped (librosa/ISC only); ADR-003 + `prototype-definition.md` corrected and ADR-003 accepted.** | Doc integrity — resolved |

---

**Nothing in Part B is applied in this addendum, except B-5 (resolved 2026-07-23 at ADR-003's ratification).** Each is an owner decision; the STOP-AND-ASK items must be settled before EXP-003 runs, since ADR-004 forbids reinterpreting a pre-registered experiment under an agent's own judgment. **Part A builds only after** the ADR → validation-plan → ADP gates, and its Phase-2-touching pieces only after EXP-003 reports.
