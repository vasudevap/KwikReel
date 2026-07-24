# AI Vacation Reel Agent

An **explainable, local-first, human-directed first-draft reel editor** for private family footage. It proposes a transparent first pass at the edit — which clips, in what order, where to trim, where to change speed — each with a plain-language reason. The user reviews everything, overrides anything, and **approves each machine-proposing stage before the next runs.** The AI proposes; the human decides.

Not an autonomous editor, and not a claim of editorial intelligence. The repository name predates this framing; the framing governs.

## Status

**Stage A (Direction) closed; Stage B (Specification) done for M1; pre-ADP course correction applied 2026-07-24** (independent review: [docs/reviews/PRE-ADP-REVIEW-2026-07-24.md](docs/reviews/PRE-ADP-REVIEW-2026-07-24.md)).

**Documents only — no product code, no media, no experiments.** The next gate is the owner approving the M1 Work Order backlog and authorizing an ADP. Nothing may be built before that. See [handoff.md](handoff.md) for the exact state and the owner actions required.

**Accepted decisions:** ADR-002 (privacy), ADR-003 (music/licensing), ADR-005 (local web app; `project.json` canonical), ADR-006 (incremental staged build; per-stage approval; transparency), ADR-007 (AI trim in M1; assists ordered by tractability), ADR-008 (prototype before contract freeze), and the **2026-07-24 course-correction set** — ADR-009 (manual curation in M1), ADR-010 (proposal `disposition`), ADR-011 (local delivery security), ADR-012 (evidence checkpoints), ADR-013 (prototype thumbnails under ADR-002).
**Superseded:** ADR-001 (by ADR-005), ADR-004 (by ADR-006). **Retired:** `docs/specs/VALIDATION-PLAN.md` — no experiment ever ran, no corpus was collected.

## Thesis

Strong AI products are **governed systems**: deterministic where possible, probabilistic where useful, measurable throughout, privacy-aware by default, reversible in their actions, and human-approved at consequential points. Here the human is present at every proposing stage, and every machine proposal is explained and recorded. The differentiator **under test** is transparent, approvable, auditable, local-first assistance — not autonomous judgment, and not a black box.

That incumbents (Apple Photos, Google Photos, CapCut, Quik) already ship free one-tap montage-to-music is treated as **fact**, not a gap to claim. Whether users value explanation and control enough to review a first draft is an **open belief**, tested cheaply and early (ADR-012) rather than assumed.

## Method

Follows the [AI-Parallel Delivery Playbook](../_oversight/DELIVERY-PLAYBOOK.md): Direction → Specification → incremental staged build, with per-stage human approval. Validation-first sequencing and pre-registered kill criteria were retired by ADR-006; per-stage acceptance on real footage plus the lightweight evidence checkpoints in ADR-012 replace them.

## Scope in one line

A **nine-stage pipeline** (ingest · assisted selection/order · trim · speed · timeline · manual edit · finalize · export · save) with **five approval gates** — ingest, selection, trim, speed, finalize. M1 delivers the working pipe **+ manual curation + AI trim**; M2 the selection/order assist; M3 speed ramping. Manual include/exclude/delete/restore is available from M1; the selection/order *assist* is M2.

## Documents

**Direction** — [PROJECT.md](PROJECT.md), [ROADMAP.md](ROADMAP.md), decision records in [docs/decisions/](docs/decisions/)
**Specification (M1)** — [ES-001](docs/specs/ES-001-manual-editor-core.md), [COMPONENT-DECOMPOSITION.md](docs/specs/COMPONENT-DECOMPOSITION.md), [m1-backlog.md](docs/work-orders/m1-backlog.md)
**Evidence & risk** — [EVIDENCE-LEDGER.md](docs/specs/EVIDENCE-LEDGER.md), [risk-register.md](docs/research/risk-register.md), [competitive-landscape.md](docs/research/competitive-landscape.md)
**Review** — [PRE-ADP-REVIEW-2026-07-24.md](docs/reviews/PRE-ADP-REVIEW-2026-07-24.md)

**Pre-pivot, retained for history — do not treat as current** (each carries a banner; `PROJECT.md` governs): `docs/vision/*` (SYSTEM-VISION, INTEGRATION-PLAN, and the two `.html` overviews), `docs/specs/prototype-definition.md`, `docs/specs/sample-media-test-strategy.md`, `docs/NOTION-PROJECTION.md`, and the retired `docs/specs/VALIDATION-PLAN.md` / `docs/work-orders/phase-1-backlog*.md`.

## Commercial posture

Conditional and deferred — a validation and portfolio project first. Auto-assembly and beat sync are commodity; the most-wanted feature (Instagram songs) is legally unavailable to any third party; usage is 2–6 occasions/year. Known headwinds are recorded in the [risk register](docs/research/risk-register.md), not planned against.
