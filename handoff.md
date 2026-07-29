# Handoff

**Updated 2026-07-28**, after the clean cut that preceded the v3z rebuild.

## The one-paragraph version

A complete M1 backend exists and passes 72 tests on synthetic fixtures. The
frontend it was built for has been deleted, because a 26-version design
exploration ended at **v3z** — a materially different product. The documentation
was consolidated: everything superseded moved to `docs/archive/`, the surviving
guardrails were transcribed into `docs/CONSTRAINTS.md`, and the record was
rebuilt forward from v3z as `docs/DECISIONS.md` and then **`SPEC.md`, accepted
2026-07-28**. **ADP-002 is authorized** — the backend rebuild may proceed
locally, on synthetic fixtures, WO-117 – WO-124.

## What exists

**Backend — works, on synthetic fixtures only.**

| Module | State |
|---|---|
| `backend/contracts/` | Pydantic models + generated TS types + service Protocols. Schema v1, which v3z changes substantially |
| `backend/ingest/` | ffprobe → `SourceIndex`, rotation-corrected, 540×960 proxies. **Slow on real footage** — no `-preset`, no hardware encoder, serial scan |
| `backend/analysis/` | OpenCV per-second signals. The letterbox/exposure fault is **fixed** (WO-116, `3d0d0d6`), with two regression tests |
| `backend/propose/` | Deterministic trim proposer with reason records |
| `backend/store/` | Save/load byte-equivalent, optimistic concurrency, origin protection |
| `backend/render/`, `backend/qa/` | FFmpeg render + output QA |
| `backend/api/` | FastAPI, job runner, and the local-delivery security guards, each proven to fail when removed |

Run it: `python -m backend.api.run`. Tests: `pytest` — 73 collected, 72 pass, 1
owner-gated skip. (Use the repo's `.venv`; the system `python3` has no pytest.)

**Frontend — a placeholder.** `frontend/src/` holds only `main.tsx` (a stub that
keeps the build green) and `types/contracts.ts` (generated). The WO-107–110 app
was deleted in the clean cut.

**Design — v3z is frozen, and lives outside the repo.**
`docs/design-claude/mockup-v3z.html`, plus its generator, whose state model is a
partial specification of trim stickiness, speed duration math and the audio mix.
**Gitignored by decision** — the repo is public and the mockups are the
product's look and feel. They exist on the owner's disk only, so this path does
not resolve on GitHub.

## What does not exist

- **No code against schema v2 yet.** `backend/contracts/` is still v1. WO-117 is
  the first thing that changes it, and it runs alone.
- **No frontend at all**, and no authorization for one. ADP-003 is not written —
  its content depends on what WO-124 measures.
- **Four things `SPEC.md` does not settle** — its §14: the speed assist's
  parameters, the Log's retention and persistence, the playback engine, and the
  rack layout invariant under real data.
- **No media, no corpus, no consent record.** Every ledger claim is `assumed`.
- **No real-footage run.** The two exit gates that need it have never run.

## In flight right now

**WO-117, the contract kernel v2** — `SPEC.md` §3 frozen as Pydantic models and
regenerated TS types. It **runs alone**; five backend lanes wait on it.

**WO-124, the playback-engine spike** — throwaway code that answers `SPEC.md` §6
with measurements. It depends on nothing and is the highest risk in the plan:
nothing yet proves a browser can sequence proxies through in/out points with
variable speed and a synced music bed. **It is already late** — it was meant to
run while the spec was being written.

## What happens next

1. **WO-117, alone.** Then WO-118 store · WO-119 media · WO-121 renderer ·
   WO-122 QA · WO-123 API fan out in parallel.
2. **WO-124's numbers** decide whether ADP-003 (the frontend) can be written
   against v3z as drawn, or whether the design changes first.
3. ADP-002 closes when those merge green. See its §9.

## Owner actions required

1. **Close `SPEC.md` §14 SO-1 and SO-2** — the speed parameters and the Log's
   retention. Neither blocks WO-117; SO-1 holds WO-120 and SO-2 holds the Log
   unit. If SO-1 is still open when the rest is green, ADP-002 closes without the
   speed proposer.
2. **Record an ADR-002-style consent** before anything runs against real footage.
   Nothing under ADP-002 may touch real media without it.
3. **Authorize pushes individually.** As of 2026-07-28 `origin/main` is at `HEAD`
   — verified with a live `git fetch`, superseding an earlier handoff that
   claimed four commits were unpushed against a stale tracking ref. Everything
   built under ADP-002 stays local until you say otherwise.

## Things that will bite you

- **The repo is public.** `project.json` holds absolute paths to private
  footage. It is gitignored — keep it that way.
- **`docs/archive/` is not authority.** See `CLAUDE.md`. Several archived
  documents contradict each other by design of their own history.
- **Owner approval is a build gate, not proof the product is good.** Real users
  other than the owner are deferred, not deleted.
- **The design has never been operated.** v3z is six static renders with no
  interaction logic. Everything that reads well as a screenshot is untested as
  behaviour.
