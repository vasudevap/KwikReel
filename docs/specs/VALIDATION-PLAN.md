# Validation Plan — AI Vacation Reel Agent

**Status:** Draft — owner approval required *before any experiment runs*
**Governing:** `_oversight/DELIVERY-PLAYBOOK.md` Stage B; sequencing locked by ADR-004; data handling governed by ADR-002
**Template:** `_oversight/templates/VALIDATION-PLAN-template.md`

**Stage B trigger met because:** the core value proposition depends on a capability — model-assisted editorial ranking — that has not been demonstrated on representative data, and if it is false, most of the plan becomes pointless.

## Pivotal hypothesis

> **H-PIVOTAL:** Model-assisted cross-clip ranking and subclip selection outperform a transparent metadata/CV heuristic baseline by enough to reduce human corrections meaningfully.

If this fails, the project concludes as a portfolio proof of concept. The deterministic pipeline would still produce a montage, but it would be a worse version of something Apple ships free — with no differentiation left to build on.

## Hypothesis register

Ordered **pivotal-first**. EXP-000 through EXP-002 precede the pivotal experiment only because they are strictly required to run it: EXP-003 cannot measure "beats the baseline" until a corpus, ground truth, and the baseline itself exist.

| ID | Hypothesis | Baseline it must beat | Metric | Threshold (pre-registered) | Cost | If it fails |
|---|---|---|---|---|---|---|
| EXP-000 | A consented, annotated corpus with human reference edits can be assembled | n/a | n/a | 8–10 days, 25–60 clips each, ground truth complete, consent recorded | 2–3 evenings + ~30–40 h annotation | Blocks everything below |
| EXP-001 | Incumbent free tools leave a quality/control gap on the same footage | n/a — this *establishes* the floor | Blind user rating of incumbent outputs, same rubric | If any incumbent scores "would post with minor tweaks", the assumed gap is smaller than claimed | 2–3 days | Premise weakens; revise framing before spending Phase 1 |
| EXP-002 | Deterministic filtering and dedupe reject junk reliably | n/a — this *is* the floor | Must-keep recall / seeded-unusable precision; dupe cluster agreement | ≥95% recall, ≥80% precision, ≥85% dupe agreement | 2–4 days | The pipeline floor is unreliable; foundational problem |
| **EXP-003** | **PIVOTAL — model-assisted ranking beats the heuristic baseline** | **Duration + faces + sharpness + motion heuristic** | **Spearman ρ vs. pooled human ranking; margin over baseline** | **ρ ≥ 0.6 AND a meaningful margin over baseline** | **~1 week** | **Kill criterion 1 fires → conclude as PoC** |
| EXP-004 | Motion + audio-event + VLM window choice finds the good seconds | Uniform midpoint window | Overlap (IoU) with human-chosen windows | ≥70% | ~1 week | Subclip UI becomes mandatory; autonomy claim weakens |
| EXP-007 | A 50-clip day processes locally in acceptable time | n/a | Wall-clock, end to end, Apple Silicon | ≤15 min on M2-class | 2 days, parallel with EXP-003 | Hybrid keyframe-to-cloud becomes the default architecture |
| EXP-005 | Time-gap + GPS clustering matches human event labels | n/a | Cluster agreement with human labels | ≥85% | 1–2 days | Add visual-similarity clustering; cost and complexity rise |
| EXP-006 | The solver assembles a coherent timeline on budget, with beats that read as musical | Every-beat cut; unaligned cut | Duration error; event coverage; blind A/B preference | ≤0.5 s error; ≥80% coverage; blind preference for selective alignment | 3–5 days | Assembly layer needs rework before user testing |
| **EXP-008** | **End-to-end drafts are accepted with few corrections** | n/a — this is the north star | **Median corrections-to-acceptance; "would post" 1–10** | **median ≤5 corrections; ≥7/10** | 1 week + recruiting | **>8 corrections → kill criterion 2 fires → conclude** |
| EXP-009 | Users prefer assisted draft over full automation, and some would pay | Full-automation variant | Stated preference; conversion at price points | ≥30% would pay one-time ~US$29 or ~US$5/reel | 8–10 interviews + landing page | No commercial path; portfolio outcome stands |

**Phase mapping.** EXP-000–004 and EXP-007 close Phase 1. EXP-005–006 close Phase 2. EXP-008 closes Phase 3 and is the ship/kill gate. EXP-009 informs Phase 5.

### Rules carried from the playbook

- **Every probabilistic hypothesis names a deterministic baseline.** EXP-003's baseline is a deliberately dumb heuristic — duration, face count, sharpness, motion energy. Building it well is not optional: a weak baseline makes the model look good and answers nothing.
- **Thresholds above are pre-registered.** Changing one after seeing a result is drift, is logged in the evidence ledger with what moved it, and is a stop-and-ask.
- **Held-out set:** one labelled day, named at corpus assembly, untouched until the final EXP-008 comparison, and excluded from every Phase 1 Work Order's allowed file scope.

## Corpus and ground truth

Governed by ADR-002. Consent is recorded before media is copied, covers children's footage explicitly, and is withdrawable with recorded deletion.

| Set | Purpose | Size | Annotation required | Consent status |
|---|---|---|---|---|
| A — Normal days | Varied: travel, activity, people, food, scenery, evening | 4–5 days, 30–50 clips | Event order, must-keep, coverage, full clip ranking | *not yet collected* |
| B — Adversarial | Blur, obstruction, accidental recordings, duplicates, long static shots, mixed orientation/FPS | 2 days | Usable/reject label and reason | *not yet collected* |
| C — Narrative stress | Repeated activities, out-of-order clocks, multiple locations, missing metadata | 2 days | Ground-truth event clusters, chronology exceptions | *not yet collected* |
| D — Held out | Final comparison only | 1 day | Full ground truth; sealed | *not yet collected* |
| E — Music | Rights-cleared tracks, varied BPM and section structure (ADR-003) | 3 tracks | Beat/downbeat and section labels for a sampled interval | n/a |

Annotation budget ~30–40 hours. **Do not build more ground truth than EXP-003 needs before it reports.** Per-clip full rankings and best-window annotations are expensive; annotate the subset the pivotal experiment consumes, and extend only if it passes.

## Competitive floor

Required by the playbook's Stage A rule and measured in EXP-001. The same day of footage runs through each incumbent, and outputs are scored blind by the same rubric used on this system's drafts.

| Incumbent | Why it matters | Result |
|---|---|---|
| Apple Photos Memory Movies | Free, pre-installed, on-device, improving each OS cycle. The most dangerous competitor and the primary absorption risk. | *not yet measured* |
| Google Photos Highlight Videos | Free, cross-platform, search-driven selection with auto music sync. | *not yet measured* |
| CapCut AutoCut | Free and dominant; the workflow the target user currently abandons. | *not yet measured* |
| GoPro Quik | Closest historical analog to the full vision. | *not yet measured* |
| AidVid | Direct competitor on this exact use case; validates pay-per-render. | *not yet measured* |

"No incumbent produces a reviewable, explainable reel" is a **hypothesis until this table is filled in.** If any incumbent scores "would post with minor tweaks," the gap is smaller than the project assumes and the framing must be revised before Phase 1 proceeds.

## Kill criteria checked at this stage

Verbatim from `PROJECT.md`, locked by ADR-004:

1. **Ranking fails to beat the baseline** (EXP-003) → conclude as portfolio proof of concept.
2. **Median corrections-to-acceptance exceeds 8** (EXP-008) → conclude.
3. **Apple or Google ships reviewable, explainable editorial reels natively** → conclude. Re-measured at every phase close.

## Exit gate

Stage B closes when EXP-003 has a recorded verdict and the kill criteria have been checked against it.

- **Continue** — pivotal hypothesis passed; write the Phase 2 Engineering Specification citing the evidence.
- **Revise** — inconclusive or partial; authorize a named follow-up, narrow scope, or adopt the fallback design (user pre-marking carries selection, model provides rationale only).
- **Stop** — a kill criterion fired. Write up the outcome and close. This is a successful use of the methodology, and the write-up is the portfolio deliverable.
