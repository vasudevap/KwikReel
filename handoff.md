# Handoff

**Updated 2026-07-28**, after the clean cut that preceded the v3z rebuild.

## The one-paragraph version

A complete M1 backend exists and passes 67 tests on synthetic fixtures. The
frontend it was built for has been deleted, because a 26-version design
exploration ended at **v3z** — a materially different product. The documentation
was consolidated: everything superseded moved to `docs/archive/`, the surviving
guardrails were transcribed into `docs/CONSTRAINTS.md`, and the next document to
write is a single `SPEC.md` cut forward from v3z. **No implementation is
authorized.**

## What exists

**Backend — works, on synthetic fixtures only.**

| Module | State |
|---|---|
| `backend/contracts/` | Pydantic models + generated TS types + service Protocols. Schema v1, which v3z changes substantially |
| `backend/ingest/` | ffprobe → `SourceIndex`, rotation-corrected, 540×960 proxies. **Slow on real footage** — no `-preset`, no hardware encoder, serial scan |
| `backend/analysis/` | OpenCV per-second signals. **Carries a correctness bug being fixed now** — see below |
| `backend/propose/` | Deterministic trim proposer with reason records |
| `backend/store/` | Save/load byte-equivalent, optimistic concurrency, origin protection |
| `backend/render/`, `backend/qa/` | FFmpeg render + output QA |
| `backend/api/` | FastAPI, job runner, and the local-delivery security guards, each proven to fail when removed |

Run it: `python -m backend.api.run`. Tests: `pytest` — 67 pass, 1 owner-gated skip.

**Frontend — a placeholder.** `frontend/src/` holds only `main.tsx` (a stub that
keeps the build green) and `types/contracts.ts` (generated). The WO-107–110 app
was deleted in the clean cut.

**Design — v3z is frozen.** `docs/design-claude/mockup-v3z.html`, plus its
generator, whose state model is a partial specification of trim stickiness,
speed duration math and the audio mix.

## What does not exist

- **No `SPEC.md`.** The single normative product + contract document has not been
  written. Until it exists there is nothing legitimate to code against.
- **No decisions on the v3z departures.** Gates, `disposition`, displayed
  reasons, speed-in-M1, the audio model, the retired trim floor — all open.
- **No media, no corpus, no consent record.** Every ledger claim is `assumed`.
- **No real-footage run.** The two exit gates that need it have never run.
- **Nothing pushed.** The branch is well ahead of the public `origin`.

## In flight right now

**The letterbox / exposure fix.** `backend/ingest/ffmpeg_ingest.py:152`
letterboxes every proxy into 540×960, and `backend/analysis/opencv_analysis.py:47`
analyses that padded proxy. Exposure is computed as the fraction of clipped
pixels (`<= 8` or `>= 247`), and black bars are 0 — so a 16:9 clip is **0.683
bars against an `exposure_ceiling` of 0.50**, and **every landscape clip fails on
every second and is labelled `OVEREXPOSED` before any content is considered.**

No test caught it: the analysis unit tests never build a proxy, and the one
exposure assertion uses a deliberately black *portrait* clip, which letterboxes
to nothing. The integration test asserts only that a proposal carries *a*
reason, never that the reason is right.

This compromises evidence-ledger claim **C-03**.

## What happens next

1. **The decision session** — the v3z departures, recorded once. See
   [PLAN-v3z-rebuild.md §1](docs/implementation-plans/PLAN-v3z-rebuild.md).
2. **`SPEC.md`**, written forward from v3z. The only document that gates code.
3. **The contract kernel**, alone, then the backend and frontend lanes fan out.

Two things run in parallel with all of that, because neither depends on any v3z
decision: the **letterbox fix** (above) and the **playback-engine spike**, which
is the highest-risk unknown in the plan — nothing yet proves a browser can
sequence proxies through in/out points with variable speed and a synced music
bed.

## Owner actions required

1. **Hold the decision session.** Everything downstream is blocked on it.
2. **Choose the letterbox remedy's blast radius** — the minimal fix is landing
   now; whether proxies should stop letterboxing altogether is a separate call.
3. **Record an ADR-002-style consent** before anything runs against real footage.
4. **Authorize pushes individually.** The branch is unpushed and the repo is
   public.

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
