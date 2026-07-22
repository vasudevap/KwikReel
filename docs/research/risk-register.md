# Risk register

**Status:** Draft — owner approval required. Ratings are assessments, not measurements.

Three rows below are **kill criteria** rather than risks to mitigate: they are pre-committed stopping conditions locked by ADR-004 and can only be relaxed by a new ADR. The distinction matters — a risk gets managed, a kill criterion ends the project.

| Risk | Type | Likelihood / impact | Mitigation / stop condition |
|---|---|---|---|
| Weak editorial judgment produces bland or incoherent drafts | Quality | High / High | Start with labelled corpus and human rubric; compare baselines; do not productize before credibility gate passes. |
| Quality heuristics discard a meaningful low-quality family moment | Quality | Medium / High | “Flag, do not delete”; give must-keep/lock priority; measure must-keep recall. |
| Incorrect chronology due to timestamp/timezone metadata | Technical | Medium / Medium | Preserve raw metadata, allow offset/group corrections, use visual/event clustering as supporting evidence only. |
| Near-duplicate detection collapses meaningful variations | Quality | Medium / Medium | Threshold calibration and restore-able decisions; retain alternative candidates. |
| Local hardware/codec variability causes slow or failed renders | Technical | Medium / Medium | Pin FFmpeg capability checks, proxy first, record hardware, test VideoToolbox fallback. |
| Multimodal model hallucination or bias mislabels private family media | Quality/privacy | Medium / High | Treat labels as uncertain scores, require provenance/confidence, no identity recognition without consent, human approval remains final. |
| Private footage, location, children, or travel documents leak to cloud | Privacy | Medium / Critical | Local-first POC; cloud only explicit per-run opt-in with data map, encryption, retention deletion, and no training terms confirmed. |
| Originals or metadata are deleted/altered | Privacy/safety | Low / Critical | Read-only ingest, separate derived-output directory, audit log, explicit deletion workflow only. |
| Music use infringes platform/commercial terms | Legal | High / High | Use local royalty-free test tracks; support timing-plan/no-audio export for Instagram’s in-app music; obtain legal review before any licensing claim. |
| **Platform absorption: Apple/Google ship reviewable editorial reels natively** | Product | **High / Critical** | **Largest product risk.** Both ship free, pre-installed, on-device, improving each OS cycle at zero acquisition cost. Measure the floor in EXP-001; re-measure at every phase close. **This is kill criterion 3, not a backlog item.** |
| **Pivotal claim fails: model ranking does not beat the heuristic baseline** | Quality | **Medium / Critical** | **Largest technical risk.** If selection is not clearly better than a transparent heuristic, the review burden equals manual editing and the product has no reason to exist. Tested early and cheaply by EXP-003. **Kill criterion 1.** |
| **Usage frequency too low to sustain a business** | Commercial | **High / High** | 2–6 reel-worthy occasions per year makes subscription retention implausible; month-two churn is the default. Do not plan against subscription revenue. Plausible models are one-time purchase or pay-per-render; test in EXP-009. The engine is occasion-agnostic (birthdays, sports days, year-in-review), which is the durable frame — but build no variant before the wedge passes EXP-008. |
| **Correction burden equals manual editing** | Product | Medium / Critical | If median corrections-to-acceptance exceeds 8, the review workflow costs what CapCut costs. Instrument corrections from the first working version, not retrofitted. **Kill criterion 2.** |
| Competitive tools close the remaining gap | Product | High / Medium | Differentiate through explainability, local privacy, chronology, and controlled review rather than generic AutoCut. Two live entrants (AidVid, Reelful) confirm the space is being entered now. |
| Scope expands into a polished consumer editor too soon | Delivery | High / High | Enforce ADR-001; UI work waits for objective POC editorial gates. |
| Cost/latency makes cloud workflow unacceptable | Product | Medium / High | Profile end-to-end runs; set explicit upload/inference budgets; retain local fallback. |

## Privacy baseline

The prototype processes originals locally, stores derived data beside the project under a user-controlled location, performs no automatic upload/publishing/deletion, and only uses consented sample media. This is a design constraint, not a claim of production compliance.
