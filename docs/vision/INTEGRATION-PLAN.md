# Integration Plan — docking the Reel Agent into Atlas

**Status:** Draft · **forward-looking projection** — owner approval required. Authorizes nothing. The integration described here is **deferred and conditional**; it does not begin until validation succeeds and a future ADR accepts the boundary contract.
**Companion:** [SYSTEM-VISION.md](SYSTEM-VISION.md) is the *what*; this is the *when and in what order*. [reel-atlas-overview.html](reel-atlas-overview.html) is the visual.
**Governing:** [ROADMAP.md](../../ROADMAP.md) (phase gates), [ADR-001](../decisions/ADR-001-prototype-shape.md) (deferral + independent interfaces).

---

## What is real (read this first)

- **No integration work is authorized.** [CLAUDE.md](../../CLAUDE.md): "No implementation or interface work is authorized" until the ADRs are accepted, the validation plan is approved, and the owner authorizes an ADP.
- **This is not a committed sequence.** It is the order the dock *would* take if — after Phases 1–4 — the owner chooses "integrate" at Phase 5. Every step below is contingent on the one before, and on evidence that does not yet exist.
- **Kill criteria come first.** If the pivotal ranking experiment or the correction-burden gate fires ([PROJECT.md](../../PROJECT.md) kill criteria), there is no product to dock and this plan is moot. That is a successful outcome, not a failure.

---

## Where the dock sits in the roadmap

Atlas is the **"integrate"** branch of the Phase 5 decision — nothing earlier.

| Phase | What happens re: Atlas |
|---|---|
| **1 · Validation** | Nothing. Evaluation apparatus only, CLI-only. Interfaces kept renderer-independent per ADR-001 so a dock stays *possible*. |
| **2 · First-draft generator** | Nothing. `timeline.json` becomes the stable, renderer-independent contract — the seam a dock would later attach to. |
| **3 · Assisted review** | Nothing. The local review loop (lock/remove/restore/regenerate) is proven as the product. This is what makes the agent worth governing at all. |
| **4 · Editorial quality** | The ADR-002 opt-in cloud-keyframe experiment runs. This is the **first** action whose governance (approval + audit) Atlas is genuinely apt for — and the first honest test of the boundary. |
| **5 · Productization** | The **build / integrate / stop** decision. "Integrate" = adopt Atlas as the control plane, behind an accepted architecture spec and a new ADR. |

No phase authorizes the next until its exit criteria are evidenced and accepted ([ROADMAP.md](../../ROADMAP.md)).

---

## Preconditions before any Atlas work begins

All must hold — none is satisfied today:

1. ADR-001 through ADR-004 accepted; validation plan approved with pre-registered thresholds.
2. Editorial quality **validated** — the pivotal ranking experiment beats the heuristic baseline; corrections-to-acceptance clears the Phase 3 gate.
3. A **boundary ADR** accepted (see below) — the dock is a locked architectural decision, not drift.
4. Owner authorizes a Phase 5 ADP scoping the integration.

---

## Open decisions to resolve first

These are the questions the boundary ADR must answer. They are unanswered on purpose — recording them is the point.

| # | Open decision | Why it is load-bearing |
|---|---|---|
| D1 | **Boundary ADR** — accept (or reject) the data-plane / control-plane split and the crossing contract in [SYSTEM-VISION.md](SYSTEM-VISION.md). | Everything else depends on it. Without it the dock is a projection, not a plan. |
| D2 | **Evidence class that crosses** — exactly what rationale/metadata Atlas may receive, and proof media never rides along. | This is where the local-first guarantee is either kept or quietly broken. |
| D3 | **Hosting & auth of the control plane** — local vs cloud Atlas; how a single owner authenticates. | A cloud control plane touching a local-first product is the central tension; ADR-002 governs any egress. |
| D4 | **Single-reviewer mapping** — Atlas's one-reviewer rule onto the memory-keeper owner. | Fits naturally, but must be stated, not assumed. |
| D5 | **Consent withdrawal via audit** — how ADR-002 withdrawable consent + retention is honored through Atlas's immutable audit. | "Immutable audit" and "withdrawable consent" must be reconciled explicitly. |

---

## Projected dock sequence (illustrative, not authorized)

*If* Phase 5 chooses integrate, the least-risky order — each step shippable and reversible on its own:

1. **Keep the seam clean** (already the ADR-001 stance): planner emits `timeline.json`; renderer and any orchestrator attach to it, never the reverse.
2. **Accept the boundary ADR** (D1–D5 resolved).
3. **Approval hook for export** — the smallest real gate: the local "export" action raises an Atlas approval carrying rationale + counts; nothing leaves the Mac until approved.
4. **Run state + audit** — surface run status and write decisions to the immutable audit.
5. **Governance for the keyframe experiment** — route the ADR-002 opt-in through the same approval + audit path.

Each step is a candidate Work Order with a frozen file scope, not a licence to build ahead of the gate.

---

## Risks and tensions carried forward

- **Local-first vs. cloud control plane** — the defining tension; unresolved until D3. Media staying local is a hard constraint, not a preference.
- **Documentation volume as false signal** — these vision/plan docs describe a *deferred* integration; they must not read as an accepted roadmap. Hence the status banners.
- **Apparatus-becomes-product drift** — the same risk [ROADMAP.md](../../ROADMAP.md) flags for Phase 1 applies to a premature dock. Building governance before there is something worth governing is the failure mode this sequencing prevents.
- **Immutable audit vs. withdrawable consent** — reconciled only by D5.

This document is ungraded and introduces no claim into [EVIDENCE-LEDGER.md](../specs/EVIDENCE-LEDGER.md). Firing a kill criterion retires this plan cleanly.
