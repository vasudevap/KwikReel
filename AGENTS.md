# AI Vacation Reel Agent — session instructions

Read `../_oversight/DELIVERY-PLAYBOOK.md`. We follow it for this project.

This file mirrors `CLAUDE.md` so that Codex, Antigravity, and Claude Code sessions operate under identical constraints. If the two ever diverge, `CLAUDE.md` is authoritative and this file is stale — say so rather than picking one.

## Where the project is

**Stage A closed; Stage B specification done for M1; pre-ADP course correction applied 2026-07-24.** `PROJECT.md`, `ROADMAP.md`, `ES-001` (as amended), and **eleven ADRs** (002/003/005/006/007/008 + the 2026-07-24 set 009–013) are accepted following the **2026-07-23 pivot** to a human-directed, approval-gated editor. M1 now includes **manual curation** (ADR-009); proposals carry a **`disposition`** (ADR-010); local delivery is **origin-guarded + capability-token protected** (ADR-011). The M1 Work Order backlog is drafted and awaiting approval.

**Still documents only — no code and no media exist.** Nothing may be built until the owner approves the backlog and authorizes an ADP. When that happens, **the first work is WO-100: a clickable prototype with fake data** (ADR-008), not backend code. Read `handoff.md` before assuming anything exists.

**Accepted:** ADR-002 (privacy), ADR-003 (music/licensing), ADR-005 (local web app form factor), ADR-006 (incremental staged build), ADR-007 (AI trim in M1), ADR-008 (prototype before contract freeze), ADR-009 (manual curation in M1), ADR-010 (proposal disposition), ADR-011 (local delivery security), ADR-012 (evidence checkpoints), ADR-013 (prototype thumbnails under ADR-002).
**Superseded:** ADR-001 (by ADR-005), ADR-004 (by ADR-006).
**Retired:** `docs/specs/VALIDATION-PLAN.md` — no experiment ever ran, no corpus was collected.

## Framing

An **explainable, local-first, human-directed first-draft reel editor** for private family footage — not a claim of autonomous editorial intelligence. The repository name predates this framing; the framing governs.

The system proposes a transparent first pass at the whole edit — **which clips, in what order, where to trim, where to change speed** — and the human reviews it, overrides anything, and **approves each machine-proposing stage before the next runs — five approval gates (ingest, selection, trim, speed, finalize) across the nine-stage pipeline.** The AI proposes; the human decides.

## Hard constraints

Locked by ADR and may not be relaxed by an agent's own judgment. Each is a stop-and-ask.

- **No implementation is authorized until the owner authorizes an ADP.** ADR-005 and ADR-006 fix the shape and the method; neither authorizes building.
- **No media collection before consent is recorded.** ADR-002 governs; consent precedes any copying of footage.
- **Never commit media, consent records, or any identity map.** See `.gitignore`. Git history persists after deletion, and consent under ADR-002 is withdrawable — a commit makes that impossible to honour. Prototype thumbnails follow ADR-013: only `fixtures/synthetic/` (no real people) is committed; real-footage thumbnails stay local and untracked.
- **No face recognition or person identification, at any phase.** Detection and counting without identity only.
- **Original media never leaves the device.** Read in place, never modified. Cloud processing of originals is out of scope under `PROJECT.md`.
- **No assist may act without user approval.** Selection, ordering, trim, and speed are *proposals*; nothing advances a stage without the user's explicit approval (ADR-006).
- **A stage that cannot explain its proposals is not complete.** Every proposal carries a plain-language reason, is overridable, and its rationale persists in `project.json` (ADR-006).
- **No `madmom`** or any dependency whose licence would restrict distribution (ADR-003).
- **Local delivery is origin-guarded and capability-token protected (ADR-011).** Binding to `127.0.0.1` is necessary but not sufficient; binding beyond it is a stop-and-ask. No permissive CORS; absolute media paths are scrubbed from errors and logs.
- **Every proposal carries a `disposition` (ADR-010).** Kept-versus-discarded is read from `disposition`, not binary `origin`; proposal history is bounded and deferred to M2, never an unbounded log.

## Working discipline

- Preserve the distinction between **proposed**, **accepted**, and **implemented**. Documents describing a thing are not the thing.
- **Owner approval is a build gate, not evidence of product quality.** ADR-006 makes this binding: subjective judgment of one's own output reliably overestimates quality, so real users must exercise the tool before it is called good.
- **Assists earn their place.** An assist that costs more to review and correct than to do by hand is de-scoped to manual at the stage level — recorded honestly, not argued around.
- A check that could not run is recorded with the exact command and the reason — never silently skipped.
- Stop / de-scope triggers are real (ADR-006). Firing one is a successful outcome, not a problem to argue around.
- Load-bearing claims are graded in `docs/specs/EVIDENCE-LEDGER.md`. If you rely on a claim, check its grade.

## Authorization-required consequential actions

- Creating or changing a public remote repository is consequential and requires a review gate. Before acting, present the repository owner, name, visibility, exact command or payload, expected effect, and rollback path.
- Once the owner explicitly authorizes that exact action, execute it and record the result. Do not treat authorization as standing permission for later pushes, visibility changes, repository settings, or other external writes.

## GitHub Actions posture

- Do not add or run GitHub Actions before an ADP authorizes implementation.
- Do not introduce a workflow merely because implementation is being discussed.
- Once implementation is authorized, run the Work Order's focused and full checks locally before the first push. GitHub Actions, if separately authorized, provides final evidence rather than failure discovery.
- Do not change workflows, required checks, runner selection, or branch protection without explicit owner authorization.
