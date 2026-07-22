# Roadmap — AI Vacation Reel Agent

**Status:** Draft — owner approval required
**Governing methodology:** `_oversight/DELIVERY-PLAYBOOK.md`. The Validation stage (PROP-01) is piloting on Vacation Reel Stage B only per MD-001; general acceptance pending MD-002.

**Sequencing change from the previous draft.** Model-based editorial experiments were formerly Phase 4, behind the rule-based POC *and* the review loop. That ordering built three phases of machinery before testing the assumption that determines whether any of it matters. Under the playbook's pivotal-first rule, validation now runs first and the pivotal ranking experiment gates everything downstream. Recorded and locked by **ADR-004**.

## Phases

| Phase | Stage | Scope | Exit criteria | Gate outcome |
|---|---|---|---|---|
| **0. Direction** | A | Problem framing, primary user, kill criteria, enabling ADRs (privacy posture, licensing posture, sequencing), validation plan. | Owner accepts `PROJECT.md`, this roadmap, ADR-001 through ADR-004, and `VALIDATION-PLAN.md` with its pre-registered thresholds. | continue / revise |
| **1. Validation** | B | Corpus and ground truth; competitive-floor measurement; deterministic filtering and clustering; **the pivotal ranking experiment**; subclip selection; local throughput. Builds *evaluation apparatus*, not product. | EXP-000 through EXP-004 and EXP-007 reported with honest verdicts; kill criteria checked. | **continue / revise / stop** |
| **2. First-draft generator** | C–D | End-to-end folder → one defensible draft: must-include marking, selection, timeline optimization, beat alignment, 9:16 render, selects/rejects manifest with reasons. | EXP-005 and EXP-006 pass; a draft is produced end to end on the held-out day; corrections instrumented from the first run. | continue / revise / stop |
| **3. Assisted review** | C–D | Lock, remove, restore, regenerate; provenance display; subclip adjustment; section regeneration. The review path is the product. | **EXP-008: median corrections-to-acceptance ≤5 and ≥7/10 "would post" across 5 real users on their own footage.** | **continue / revise / stop** |
| **4. Editorial quality** | C–D | Improved subclip extraction (audio events, denser sampling), event-balance tuning, opt-in cloud-VLM comparison under ADR-002. | Measurable reduction in corrections-to-acceptance against the Phase 3 figure on the same corpus. | continue / revise / stop |
| **5. Productization decision** | E | Packaging, retention/security, operational cost, positioning, willingness-to-pay signal. | EXP-009 reports; competitive floor re-measured; build / integrate / stop decision backed by evidence and an accepted architecture spec. | continue / stop |

No phase authorizes the next until its exit criteria are evidenced and accepted. Every gate may return **stop**, and stopping on evidence is a successful outcome.

## Phase 1 is apparatus, not product

The pivotal experiment compares model-assisted ranking against a heuristic baseline, so the baseline must exist before it can be beaten. That makes some code unavoidable in a validation phase, and creates an obvious drift risk: apparatus quietly becomes product, and the project ships the harness it was supposed to throw away.

Guardrails, enforced through Work Order file scopes:

- Phase 1 code is **evaluation apparatus**. It is permitted to be ugly, throwaway, and CLI-only.
- **No interface work, no packaging, no polish.** These are stop-and-ask, not judgment calls.
- Apparatus that survives into Phase 2 does so by an explicit decision recorded in the Engineering Specification, not by inertia.
- The held-out day is untouched until the final comparison, and is excluded from every Phase 1 Work Order's allowed file scope.

## Kill criteria at each gate

Restated from `PROJECT.md`, locked by ADR-004, checked at every phase close rather than only when convenient:

1. **Ranking fails to beat the heuristic baseline** (checked at Phase 1) → conclude as portfolio proof of concept.
2. **Median corrections-to-acceptance exceeds 8** (checked at Phase 3) → the review workflow costs what manual editing costs; conclude.
3. **Apple or Google ships reviewable, explainable editorial reels natively** (re-measured at every phase close) → differentiation is gone; conclude.

## Competitive-floor re-measurement

The Phase 1 incumbent baseline is re-run on the same input at every phase close. Absorption by a platform vendor is a kill-criteria event, not a backlog item. Recording it late is the failure mode this rule exists to prevent.
