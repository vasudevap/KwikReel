# Handoff

**Updated:** 2026-07-23. Direction pivoted, Stage A closed, M1 specified, and the M1 Work Order backlog drafted. **No code exists.**

## What this is

An explainable, local-first, human-directed reel editor for private family footage. It runs as a **local web app on a Mac**.

The AI proposes a first pass at the edit — which clips, in what order, where to trim, where to change speed — each with a plain-language reason. The user reviews everything, can override anything, and **approves each stage before the next runs.** The AI proposes; the human decides.

The repository name predates this framing. The framing governs.

## Where the project is

**Stage A (Direction) is closed. Stage B (Specification) is complete for M1.**

The next gate is the owner approving the M1 backlog and authorizing an ADP. **Nothing may be built before that.**

## What is real

- **Six accepted ADRs:** ADR-002 (privacy, 2026-07-22), ADR-003 (music/licensing), ADR-005 (local web app; `project.json` canonical), ADR-006 (incremental staged build; per-stage approval; transparency), ADR-007 (build sequencing — AI trim in M1), ADR-008 (prototype before contract freeze). The last five are all 2026-07-23.
- **`PROJECT.md`, `ROADMAP.md`, and `ES-001` are accepted** (owner-approved 2026-07-23).
- **Three milestones**, each shipping something the owner can use: **M1** working pipe + AI trim · **M2** AI selection and ordering · **M3** AI speed ramping.
- **`ES-001` freezes** the `project.json` schema, `SourceIndex`, `analysis.json`, `ReasonRecord`, the HTTP contract, and the trim proposer's signals and rules.
- **A GitHub remote exists** — `origin` → `https://github.com/vasudevap/ai-vacation-reel-agent`, and **it is PUBLIC**. Everything in this repository is visible to anyone.
- Documents only. That is the complete list.

## What does not exist

- **No product code.** No UI, no backend, no renderer, no `project.json` implementation.
- **No media.** No corpus, no consent records, no annotations.
- **No experiment ever ran.** Every claim in `docs/specs/EVIDENCE-LEDGER.md` is graded `assumed`.
- No approved Work Order and no ADP.

## What is only proposed

- **`docs/work-orders/m1-backlog.md`** — 15 Work Orders for M1, with file scopes, dependencies, lanes, and stop-and-ask triggers. **Needs owner approval.**
- `docs/specs/COMPONENT-DECOMPOSITION.md` — forward-looking design. Unlocks nothing.

## What happens first when building is authorized

**WO-100: a clickable prototype with fake data** — not backend code. ADR-008 requires it, and it has three rules that are not optional:

1. Fake the real waiting times (~5 min analysis, ~5 min render), so the flow is designed against real latency.
2. Seed **deliberately bad AI suggestions**, so the review screen actually gets exercised. Reviewing is the product.
3. Use **real thumbnails** from actual footage, not grey boxes.

It produces an agreed flow and **a list of gaps in the ES-001 schema.** Those gaps are amended into ES-001 *before* WO-101 turns any schema into code. Changing a screen takes minutes; changing a schema after eight Work Orders have implemented it is a migration across every saved project.

Then WO-101 freezes the contracts, and six lanes run in parallel.

## Owner actions required

1. **Approve `m1-backlog.md`, then authorize an ADP.** This is the last gate before code.
2. **Push, if wanted.** Commits are local. Each push to the public repo is its own decision — prior authorization does not carry forward.
3. **Register the project in `_oversight/STATUS.md`.** Still absent from the overseer roster, so status and drift passes cannot see it.

## Things that will bite you

- **The repo is public.** `project.json` will contain absolute paths to private footage. It is gitignored — keep it that way.
- **Stale documents, not yet reviewed against the pivot:** `docs/specs/prototype-definition.md`, `sample-media-test-strategy.md`, `docs/vision/*`, `docs/research/*`, `docs/NOTION-PROJECTION.md`, `EVIDENCE-LEDGER.md`. Treat their claims as pre-pivot.
- **Retired, kept for history:** `VALIDATION-PLAN.md`, `phase-1-backlog.md`, `phase-1-backlog-deltas.md`. ADR-001 and ADR-004 are superseded; their original text is retained with a note on top.
- **ADR-006 is amended by ADR-007** on sequencing only. Read both together.
- **Owner approval is a build gate, not proof the product is good.** ADR-006 makes this binding. Real users other than the owner are deferred, not deleted — that requirement returns when the question becomes "is this good?" rather than "is this useful to me?"

## Deferred

Phone access (running the editor from a phone browser — test whether iOS preserves capture timestamps through a browser upload before revisiting) · packaging and distribution · per-clip audio retention · filters · ML-based interestingness · saliency reframing · NLE export.
