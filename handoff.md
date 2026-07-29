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
| `backend/contracts/` | **Schema v2 — WO-117, done.** `SPEC.md` §3 as Pydantic models + generated TS types + service Protocols. Contract gate 10/10 |
| `backend/ingest/` | **Proxy recipe v2 — WO-116a, done.** ffprobe → `SourceIndex`, rotation-corrected, 540×960 proxies **carrying stereo AAC**, keyframes ~1 s apart. Still **slow on real footage** — no `-preset`, no hardware encoder, serial scan, and audio encoding adds to that (WO-135's problem, not WO-116a's) |
| `backend/analysis/` | OpenCV per-second signals. The letterbox/exposure fault is **fixed** (WO-116, `3d0d0d6`), with two regression tests |
| `backend/propose/` (trim) | **v2 — WO-118a, done.** `SegmentsProposal.value` is one `Segment`, not a list; the 1.0 s floor is retired (A-6) — a proposal may be sub-second or empty, neither padded nor raised |
| `backend/propose/` (speed) | Still v1/nonexistent. WO-120, unheld since Amendment 2, hasn't started |
| `backend/store/` | Save/load byte-equivalent, optimistic concurrency, origin protection |
| `backend/render/`, `backend/qa/` | FFmpeg render + output QA |
| `backend/api/` | FastAPI, job runner, and the local-delivery security guards, each proven to fail when removed |

Run it: `python -m backend.api.run`. (Use the repo's `.venv`; the system
`python3` has no pytest.)

> **⚠️ The suite is RED, deliberately, and this is not a regression.** WO-117
> froze schema v2 and merged; store, render, QA and API are still speaking v1.
> **45 pass · 10 fail (all in `tests/store/test_store.py`) · 5 modules cannot
> import** (`tests/api`, `tests/guards`, `tests/integration` ×2, `tests/render`
> — all v1-shape import errors, WO-121/122/123/133/134's to clear). Trim
> (WO-118a) and ingest (WO-116a) are clear; run `pytest tests/propose
> tests/analysis tests/contracts` for the green part.
> **If you are reading this and the numbers are worse, that IS a regression.**

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

- **Store, media, speed proposer, render, QA and the API are still v1.**
  Contracts (WO-117), ingest (WO-116a) and the trim proposer (WO-118a) are v2;
  the rest of the ADP-002 fan-out hasn't started.
- **No frontend at all**, and no authorization for one. ADP-003 is not written —
  its content depends on what WO-124 measures.
- **Three things `SPEC.md` does not settle** — its §14 SO-2, SO-3, SO-4: the
  Log's retention and persistence, the playback engine, and the rack layout
  invariant under real data. (SO-1, the speed parameters, closed 2026-07-28.)
- **No media, no corpus, no consent record.** Every ledger claim is `assumed`.
- **No real-footage run.** The two exit gates that need it have never run.

## In flight right now

**Nothing.** WO-118a merged (below).

**WO-124 is done.** [`docs/specs/WO-124-playback-findings.md`](docs/specs/WO-124-playback-findings.md)
— **SO-3 is answered and the v3z design survives.** The Monitor uses **two
`<video>` elements cross-swapped** (0.8 ms at the cut, against 36.3 ms for one
element reloaded — a 45× difference). Seeking is **frame-accurate** despite an
8.3 s GOP; `playbackRate` is exact; a plain `<audio>` music bed holds sync to
within 3.4 ms across a cut. The spike code is throwaway and is deleted at
ADP-002 closeout; the findings document is what survives.

## What happens next

1. **WO-118 store · WO-119 media · WO-120 speed proposer · WO-121 renderer ·
   WO-122 QA · WO-123 API**, in parallel. All are dependency-ready — WO-118a is
   done, and (as of Amendment 2) SO-1 is closed for WO-120.
2. ADP-002 closes when those merge green — **per-WO green, not whole-suite
   green.** `tests/integration/` and parts of `tests/guards/` belong to WO-134
   and WO-133, which are ADP-004's and not authorized. The suite does not go
   fully green inside this ADP, by design.

## The stop-and-asks that were raised, and closed

**No Work Order owned `backend/propose/trim_proposer.py`** — ADP-002 as drafted
gave WO-120 `speed_proposer.py` and nothing else in `backend/propose/`, while
`SPEC.md` §4.1 changes the trim proposer substantially. Found during WO-117,
when the v1 test `test_respects_the_one_second_floor` turned out to assert
behaviour A-6 forbids. **Closed by ADP-002 Amendment 1: WO-118a, unheld.**

**No Work Order owned `backend/ingest/`**, and WO-124 found `make_proxy` passing
`-an` — every proxy silent, which left `SPEC.md` §5's `clip_level` acting on
nothing and §6's preview-matches-export unsatisfiable. **Closed by ADP-002
Amendment 3: WO-116a**, merged. Proxies carry stereo AAC, keyframes are ~1 s
apart, and the proxy path has three tests where it had one vacuous one.

## Owner actions required

1. **Consider the `SPEC.md` §6 amendments** the spike warrants — findings §9 —
   which write the two-element cross-swap, the frame-accurate seek result and
   the proxy-must-carry-audio rule into the spec. All three are recording what
   was measured, not deciding anything.

   > **The §9 QA-tolerance item that was here is withdrawn.** It was raised as a
   > stop-and-ask on the ±0.5 s tolerance, on the strength of a percentage
   > measured at one clip length. Re-measured 2026-07-29: the overshoot is a
   > **fixed 1–2 frames per ramped clip**, so it scales with clip *count*, not
   > ramped seconds, and `-t (kept_duration / rate)` removes it exactly.
   > **§9 stands as written**; the remedy is now a WO-121/WO-122 lane
   > instruction in ADP-002 §4. See findings §3.

2. **Close `SPEC.md` §14 SO-2** — the Log's retention, persistence and pinning
   behaviour. Blocks the Log unit only, not any WO in this ADP. (**SO-1 is
   closed**, 2026-07-28, ADP-002 Amendment 2 — WO-120 is unheld.)
3. **Record an ADR-002-style consent** before anything runs against real footage.
   Nothing under ADP-002 may touch real media without it.
4. **Authorize pushes individually.** As of 2026-07-28 `origin/main` is at `HEAD`
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
