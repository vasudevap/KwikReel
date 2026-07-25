# Handoff

**Updated:** 2026-07-24. Direction pivoted (2026-07-23), Stage A closed, M1 specified, the backlog approved, and **[ADP-001](docs/implementation-plans/ADP-001-m1-working-pipe-and-trim.md) authorized 2026-07-24** (course-correction ADR-009–013 landed; [pre-ADP review](docs/reviews/PRE-ADP-REVIEW-2026-07-24.md)). **WO-100 (prototype) and WO-101 (contract kernel) complete 2026-07-24**; ES-001 amended with the prototype's ten schema gaps (§4.5). The first product code exists: the **frozen contracts**, the **backend compute lanes** (WO-102 ingest · WO-103 store · WO-104 render · WO-105 qa), and the **HTTP API** (WO-106) with its ADR-011 security guards (WO-113 partial). The **ES-001 §10 internal checkpoint is proven end-to-end** on synthetic fixtures, the **trim assist (WO-111/112)** is built and explained, and the **real frontend (WO-107–110)** is done — a mock + live `ReelClient`, **verified live in the browser** (import→curate→AI-trim→export against the running backend). **67 tests pass (1 owner-gated skip); the frontend typechecks and builds clean.** **Every M1 code lane is complete on synthetic fixtures**; the two remaining ES-001 §10 exit gates need the owner's real footage + a recorded ADR-002 consent.

## What this is

An explainable, local-first, human-directed reel editor for private family footage. It runs as a **local web app on a Mac**.

The AI proposes a first pass at the edit — which clips, in what order, where to trim, where to change speed — each with a plain-language reason. The user reviews everything, can override anything, and **approves each machine-proposing stage before the next runs — five approval gates across the nine-stage pipeline.** The AI proposes; the human decides.

Renamed to KwikReel 2026-07-24; the repository directory is `kwikreel`.

## Where the project is

**Stage A (Direction) is closed. Stage B (Specification) is complete for M1.** A **pre-ADP course correction was applied 2026-07-24** (ADR-009–013): manual curation added to M1, proposal `disposition` added, local delivery security specified, evidence checkpoints added, and prototype thumbnails reconciled with ADR-002.

**The M1 backlog is approved and [ADP-001](docs/implementation-plans/ADP-001-m1-working-pipe-and-trim.md) is authorized (2026-07-24).** WO-100 and WO-101 are complete (local, unpushed). The grant is *local build only*: pushes to the public repo, CI/Actions, and any run against real footage remain separately gated (ADP-001 §3).

## What is real

- **Eleven accepted ADRs:** ADR-002 (privacy), ADR-003 (music/licensing), ADR-005 (local web app; `project.json` canonical), ADR-006 (staged build; per-stage approval; transparency), ADR-007 (AI trim in M1), ADR-008 (prototype before contract freeze), and the **2026-07-24 course-correction set** — ADR-009 (manual curation in M1), ADR-010 (proposal `disposition`), ADR-011 (local delivery security), ADR-012 (evidence checkpoints), ADR-013 (prototype thumbnails under ADR-002).
- **`PROJECT.md`, `ROADMAP.md`, and `ES-001` are accepted** (owner-approved 2026-07-23).
- **Three milestones**, each shipping something the owner can use: **M1** working pipe + AI trim · **M2** AI selection and ordering · **M3** AI speed ramping.
- **`ES-001` freezes** the `project.json` schema, `SourceIndex`, `analysis.json`, `ReasonRecord`, the HTTP contract, and the trim proposer's signals and rules.
- **A GitHub remote exists** — `origin` → `https://github.com/vasudevap/KwikReel`, and **it is PUBLIC**. Everything in this repository is visible to anyone.
- **As of 2026-07-24, the first code exists:** the WO-100 clickable prototype (`frontend/`, fake data) and the WO-101 **contract kernel** — Pydantic models + generated TS types + service interfaces (`backend/contracts/`, `frontend/src/types/contracts.ts`), with a green round-trip + drift-guard test suite. Everything else is still documents.

## What does not exist

- **M1 is functionally complete on synthetic fixtures.** WO-102–106 + WO-111/112 (backend pipe + explainable trim assist) and WO-107–110 (the real frontend — mock + live client, verified live in the browser) are all built against the WO-101 interfaces. The whole loop — import → curate → AI-trim (explained) → finalize → export, with ADR-011 security — runs locally end to end. Run it: `python -m backend.api.run` after `npm --prefix frontend run build`.
- **No media.** No corpus, no consent records, no annotations.
- **No experiment ever ran.** Every claim in `docs/specs/EVIDENCE-LEDGER.md` is graded `assumed`.
- What remains needs **real footage + a recorded ADR-002 consent**: the ES-001 §10 real-~50-clip-day run and the Apple Photos Memory comparison — the only two exit gates left. All guard/integration code is done (WO-113 guards + the synthetic-runnable WO-114 §10 checks pass). Still deferred (code, low priority): the 50-clip timeline-responsiveness perf gate. The branch is **unpushed** — a push to the public `origin` needs owner authorization.
- **Noted during the real-footage review, not yet actioned:** `FFmpegIngest.make_proxy` ([backend/ingest/ffmpeg_ingest.py](backend/ingest/ffmpeg_ingest.py)) is slow on real clips — no `-preset` (libx264 defaults to `medium`), full-duration transcode, no hardware encoder, and the scan job ([backend/api/app.py](backend/api/app.py) `scan`) builds proxies sequentially, one clip at a time. Not spec-locked (ES-001 says "generate preview proxies," not how fast). Candidate fixes, independent of each other: `-preset veryfast`/`ultrafast`, macOS `h264_videotoolbox` hardware encoder, parallelize proxy builds across a small pool. Do this after the current review finishes.

## What is only proposed

- **`docs/work-orders/m1-backlog.md`** — 15 Work Orders for M1. **Approved 2026-07-24; execution authorized via [ADP-001](docs/implementation-plans/ADP-001-m1-working-pipe-and-trim.md)** (no longer merely proposed).
- `docs/specs/COMPONENT-DECOMPOSITION.md` — forward-looking design. Unlocks nothing.

## What happens first when building is authorized

**WO-100: a clickable prototype with fake data** — not backend code. ADR-008 requires it, and it has three rules that are not optional:

1. Fake the real waiting times (~5 min analysis, ~5 min render), so the flow is designed against real latency.
2. Seed **deliberately bad AI suggestions**, so the review screen actually gets exercised. Reviewing is the product.
3. Use **real thumbnails** for readability testing — but per **ADR-013**, committed fixtures are synthetic/rights-cleared only (`fixtures/synthetic/`), and real-footage thumbnails are the owner's own, local, untracked (`fixtures/local/`), behind a self-consent + lifecycle note recorded before extraction. No real footage or thumbnail is ever committed.

It produces an agreed flow and **a list of gaps in the ES-001 schema.** Those gaps are amended into ES-001 *before* WO-101 turns any schema into code. Changing a screen takes minutes; changing a schema after eight Work Orders have implemented it is a migration across every saved project.

Then WO-101 freezes the contracts, and six lanes run in parallel.

## Owner actions required

1. **Per-push authorization.** ADP-001 keeps every push to the public `origin` a separate decision — commits stay local until you say push.
2. **Record ADR-002 consent before real-media WOs run.** WO-102 / WO-111 / WO-114 and WO-104's centre-crop check can be *built* against synthetic fixtures now, but cannot *run against real footage* until a consent + lifecycle record exists.
3. **Register the project in `_oversight/STATUS.md`** so status and drift passes can see it.
4. ~~Walk the WO-100 prototype and review its schema-gap list before WO-101.~~ **Done 2026-07-24** — flow approved, all ten gaps resolved into ES-001 §4.5, WO-101 froze the contracts. Next owner decision: **authorize the WO-102+ six-lane parallel phase** (some lanes touch real footage → need the ADR-002 consent record, owner action #2).

## Things that will bite you

- **The repo is public.** `project.json` will contain absolute paths to private footage. It is gitignored — keep it that way.
- **Stale documents:** `README.md`, `docs/specs/EVIDENCE-LEDGER.md`, and `docs/research/risk-register.md` were **rewritten to the pivot on 2026-07-24**. `docs/vision/*`, `docs/specs/prototype-definition.md`, `docs/specs/sample-media-test-strategy.md`, and `docs/NOTION-PROJECTION.md` now carry **pre-pivot banners** and are retained for history. `docs/specs/COMPONENT-DECOMPOSITION.md` was reconciled to ES-001.
- **Retired, kept for history:** `VALIDATION-PLAN.md`, `phase-1-backlog.md`, `phase-1-backlog-deltas.md`. ADR-001 and ADR-004 are superseded; their original text is retained with a note on top.
- **ADR-006 is amended by ADR-007** on sequencing only. Read both together.
- **Owner approval is a build gate, not proof the product is good.** ADR-006 makes this binding. Real users other than the owner are deferred, not deleted — that requirement returns when the question becomes "is this good?" rather than "is this useful to me?"

## Deferred

Phone access (running the editor from a phone browser — test whether iOS preserves capture timestamps through a browser upload before revisiting) · packaging and distribution · per-clip audio retention · filters · ML-based interestingness · saliency reframing · NLE export.
