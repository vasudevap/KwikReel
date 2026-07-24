# System Vision — the Reel Agent and Atlas

> **⚠️ PRE-PIVOT — retained for history (banner added 2026-07-24).** This document predates the 2026-07-23 pivot and the 2026-07-24 course correction. Its present-tense claims — a **local CLI** agent surface, `timeline.json`, ADR-001 as operative, pre-registered thresholds, a held-out day, Phases 1–5 — are **superseded.** The product is a local **web app** (ADR-005) with `project.json` canonical (ADR-010 adds `disposition`); the build is three milestones with **five approval gates.** **`PROJECT.md`, `ROADMAP.md`, `ES-001`, and the ADRs govern.** The Atlas dock remains a deferred, unaccepted projection.

**Status:** Draft · **forward-looking projection** — owner approval required. Introduces **no accepted decision** and relaxes no constraint. The operative decision on Atlas is still [ADR-001](../decisions/ADR-001-prototype-shape.md) (deferral); the real dock decision is a Phase 5 concern under [ROADMAP.md](../../ROADMAP.md).
**Companion:** [reel-atlas-overview.html](reel-atlas-overview.html) is the at-a-glance visual of everything below. [INTEGRATION-PLAN.md](INTEGRATION-PLAN.md) covers *when* and *in what order*.
**Governing:** subordinate to [PROJECT.md](../../PROJECT.md), which remains authoritative for product direction. This document only adds the systems-level view of the two components and their linkage.

---

## What is real (read this first)

So volume is never mistaken for a plan — the honesty discipline of [handoff.md](../../handoff.md) applies here too:

- **The Reel Agent does not exist.** No code, no corpus, no experiments. Stage A, documents only.
- **Atlas is not built by this project.** It is a separate, pre-existing platform (`agent-control-center`) with its own accepted architecture. This project would *integrate with* it, not build it.
- **The linkage between them is a projection.** Every crossing arrow, approval hook, and run-state dock described below is drawn from both repos' real documents but is **not specified in either**. Nothing here is designed, accepted, or authorized.

The two components are **not co-equal deliverables.** This project delivers the Reel Agent. Atlas is an external governance surface it *may* dock into once — and only once — editorial quality is proven.

---

## The organizing idea: two planes, one boundary

A governed system needs the media to stay private *and* the consequential actions to be reviewable and audited. Those pull in opposite directions the moment a control plane could be cloud-hosted. The reconciliation — and the whole reason a clean split is worth drawing — is:

| Plane | Where | Holds | Never holds |
|---|---|---|---|
| **Data plane** | Your Mac (local-first) | Original media, analysis, timeline, render, editorial rationale | — |
| **Control plane** | Atlas (governance) | Approval queue, run state, audit trail, policy | **Original media.** Only a *proposed action + its evidence* crosses. |

The trust boundary between them is the load-bearing element. **Original media never crosses it.** The single narrow exception is the ADR-002 opt-in keyframe experiment — extracted keyframes only, per-run, and itself an approval-gated action.

> **The principle both planes exist to enforce:** the system proposes, a human decides. The Reel Agent produces a proposal; Atlas is where a person accepts or rejects it, with a recorded reason and an audit trail.

---

## Component 1 — The Reel Agent (what this project builds)

A local, deterministic pipeline on Apple Silicon: folder in, one defensible draft plus a plain-language account out. Capabilities below are drawn from [PROJECT.md](../../PROJECT.md) and [prototype-definition.md](../specs/prototype-definition.md); all are **proposed**, none validated.

| Capability | What it delivers | Status |
|---|---|---|
| Import a day | Inventory duration / timestamp / orientation + proxies via FFprobe; originals never modified; corrupt items reported | Proposed (POC) |
| Mark what matters | User marks 3–10 must-include clips; recorded as user-declared, never rejected | Proposed (POC) |
| Quality analysis | Interpretable blur, exposure, shake, duration, near-duplicate signals → `analysis.json` | Proposed (POC) |
| Audio-event salience | Detect laughter / cheering / splashes as a "family moment" signal (YAMNet / PANNs) | Proposed (POC) |
| People presence | Face **detection and counting only — no identity** (Apple Vision) | Proposed · [ADR-002](../decisions/ADR-002-privacy-and-data-posture.md) |
| Candidate + timeline | Cluster by time + similarity; propose subclips; chronological constrained selection under a duration budget → `timeline.json` | Proposed (POC) |
| Beat-aware render | Snap a *subset* of cuts to strong beats; 9:16 H.264/AAC via FFmpeg → `draft.mp4` | Proposed (POC) |
| Explainability | Plain-language selects / rejects / timing rationale, per source; source-to-subclip provenance | Proposed (POC) |
| Assisted review | Lock / remove / restore / regenerate; iterate the edit | Proposed (Phase 3) |
| Cloud keyframe scoring | Optional VLM-on-keyframes scorer to measure the quality/privacy trade-off | Proposed · **experiment**, opt-in ([ADR-002](../decisions/ADR-002-privacy-and-data-posture.md)) |

**Agent-side surface (today's plan):** a **local CLI** plus the report and manifests — *not* a GUI. [ADR-001](../decisions/ADR-001-prototype-shape.md): "No polished review UI in the POC; report/manifest are the review surface." A desktop review app is an addable-later surface, not designed — see [reel-agent-ui-mockup.html](reel-agent-ui-mockup.html) for a labeled projection of both surfaces.

---

## Component 2 — Atlas (the governance surface it may dock into)

Atlas contributes governance the Reel Agent would otherwise have to build itself. Capabilities below are **accepted within Atlas** ([13-human-approvals.md](../../../agent-control-center/docs/architecture/13-human-approvals.md), Approved) — but their *use by this project* is unbuilt and undesigned.

| Atlas capability | What the user gets | For this project |
|---|---|---|
| Approval queue & history (Atlas Web) | See exact action scope + its evidence; approval and execution state shown separately | Projected dock |
| Approve / reject / clarify | Decide with a recorded reason; provenance captured | Projected dock |
| Policy Engine | Determines what needs approval; **denies outright** what may never proceed — approval cannot override a denial | Projected — enforces this project's locks |
| Action Validator | Binds the exact proposed action; revalidates after approval | Projected dock |
| Run Service | Agent run state — active / waiting / continuing | Projected dock |
| Audit Writer | Immutable log of every decision; events are not deleted | Projected — supports withdrawable-consent honoring |
| Single-reviewer constraint | One human reviewer; no delegation, RBAC, or quorum | Fits a single memory-keeper owner |

---

## The linkage (the integration contract this projection assumes)

What the docking would actually mean, stated as a contract so it can later be accepted, revised, or rejected as a whole:

**Crosses the boundary — outward (Agent → Atlas):**
- A *proposed action* (e.g. "export this draft", "score these keyframes in the cloud for this run").
- Its *evidence*: the plain-language rationale, clip counts, and the `timeline.json` summary. **Metadata and reasoning — not media.**

**Crosses the boundary — inward (Atlas → Agent):**
- The *decision*: approve / reject / request-clarification, with reason.
- The *approved continuation* that lets the local run revalidate and execute the exact action.

**Never crosses:**
- Original footage. (Sole exception: ADR-002 opt-in keyframes, per-run, approval-gated.)

**Gated actions — require approval before they happen:**
- Export the reel to a file · turn on cloud keyframe scoring for a run · any consent-gated corpus step.

**Hard denials — policy refuses, no approval overrides** (locked by ADR / [CLAUDE.md](../../CLAUDE.md)):
- Person identification · uploading original media · relaxing a pre-registered threshold · touching the held-out day.

---

## Where the real decision lives

- **Now:** [ADR-001](../decisions/ADR-001-prototype-shape.md) defers Atlas ("apt for governed long-running jobs later; premature before a standalone editorial pipeline exists") and requires the planner interfaces to stay independent so a dock is *possible* later without committing to it.
- **The dock itself:** a **Phase 5** "build / integrate / stop" decision in [ROADMAP.md](../../ROADMAP.md), gated behind all validation, and — if pursued — a future ADR that accepts the boundary contract above. See [INTEGRATION-PLAN.md](INTEGRATION-PLAN.md).

This document asserts no new evidence and is ungraded; it introduces no claim into [EVIDENCE-LEDGER.md](../specs/EVIDENCE-LEDGER.md).
