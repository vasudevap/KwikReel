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
| `backend/ingest/` | ffprobe → `SourceIndex`, rotation-corrected, 540×960 proxies. **Slow on real footage** — no `-preset`, no hardware encoder, serial scan |
| `backend/analysis/` | OpenCV per-second signals. The letterbox/exposure fault is **fixed** (WO-116, `3d0d0d6`), with two regression tests |
| `backend/propose/` | Deterministic trim proposer with reason records |
| `backend/store/` | Save/load byte-equivalent, optimistic concurrency, origin protection |
| `backend/render/`, `backend/qa/` | FFmpeg render + output QA |
| `backend/api/` | FastAPI, job runner, and the local-delivery security guards, each proven to fail when removed |

Run it: `python -m backend.api.run`. (Use the repo's `.venv`; the system
`python3` has no pytest.)

> **⚠️ The suite is RED, deliberately, and this is not a regression.** WO-117
> froze schema v2 and merged, so store, render, QA, API and the trim proposer
> are all still speaking v1. **29 pass · 21 fail · 5 modules cannot import.**
> That is the cost of a contract kernel that runs alone, and the lanes below
> are what clear it. Run `pytest tests/contracts` for the part that is green.
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

- **No backend code against schema v2 yet.** The contract is v2; store, media,
  the proposers, render, QA and the API are all still v1. That is the whole of
  the ADP-002 fan-out, and none of it has started.
- **No frontend at all**, and no authorization for one. ADP-003 is not written —
  its content depends on what WO-124 measures.
- **Three things `SPEC.md` does not settle** — its §14 SO-2, SO-3, SO-4: the
  Log's retention and persistence, the playback engine, and the rack layout
  invariant under real data. (SO-1, the speed parameters, closed 2026-07-28.)
- **No media, no corpus, no consent record.** Every ledger claim is `assumed`.
- **No real-footage run.** The two exit gates that need it have never run.

## In flight right now

**WO-118a, the trim proposer**, in the working tree.

**WO-124 is done.** [`docs/specs/WO-124-playback-findings.md`](docs/specs/WO-124-playback-findings.md)
— **SO-3 is answered and the v3z design survives.** The Monitor uses **two
`<video>` elements cross-swapped** (0.8 ms at the cut, against 36.3 ms for one
element reloaded — a 45× difference). Seeking is **frame-accurate** despite an
8.3 s GOP; `playbackRate` is exact; a plain `<audio>` music bed holds sync to
within 3.4 ms across a cut. The spike code is throwaway and is deleted at
ADP-002 closeout; the findings document is what survives.

## What happens next

1. **WO-118 store · WO-118a trim proposer · WO-119 media · WO-120 speed proposer ·
   WO-121 renderer ·
   WO-122 QA · WO-123 API**, in parallel. All are dependency-ready now that v2
   is merged and (as of Amendment 2) SO-1 is closed.
2. ADP-002 closes when those merge green — **per-WO green, not whole-suite
   green.** `tests/integration/` and parts of `tests/guards/` belong to WO-134
   and WO-133, which are ADP-004's and not authorized. The suite does not go
   fully green inside this ADP, by design.

## ⚠️ Stop-and-ask, open — WO-124 found two things nobody owns

Both are in **`backend/ingest/`**, which ADP-002 §4 assigns to no Work Order.
The plan called ingest "survives", and against `SPEC.md` §3 the *contract* does.
Its **proxy recipe** does not. Full detail in the findings §4 and §6.

1. **Every proxy is silent — `make_proxy` passes `-an`.** This is the serious
   one. The Monitor cannot preview clip audio at all, so `clip_level` has
   nothing to act on, the Sound unit's "the display *is* the mix" describes
   audio that cannot play, and §6's "preview loudness must match export
   loudness" is unsatisfiable when one of them is silent. **Blocks §5 and §6 as
   written.** No test caught it for the same reason the letterbox fault survived
   to WO-116 — analysis tests call `probe_clip`, which never builds a proxy.
2. **The proxy GOP is 8.333 s** (no `-g`). Only an optimisation — seeking is
   already frame-accurate — but `-g 30` would quarter a 45 ms worst case.

## The stop-and-ask that was raised, and closed

**No Work Order owned `backend/propose/trim_proposer.py`** — ADP-002 as drafted
gave WO-120 `speed_proposer.py` and nothing else in `backend/propose/`, while
`SPEC.md` §4.1 changes the trim proposer substantially. Found during WO-117,
when the v1 test `test_respects_the_one_second_floor` turned out to assert
behaviour A-6 forbids. **Closed by ADP-002 Amendment 1: WO-118a, unheld.**

## Owner actions required

1. **Decide the ingest stop-and-ask above.** The silent proxy blocks the Sound
   unit; it needs a Work Order that owns `backend/ingest/`.
2. **Consider four `SPEC.md` §6/§9 amendments** the spike warrants — findings
   §9. The substantive one: `setpts` overshoots duration by up to 1.39 %, so a
   speed-heavy reel can breach §9's ±0.5 s QA tolerance while being correct.
3. **Close `SPEC.md` §14 SO-2** — the Log's retention, persistence and pinning
   behaviour. Blocks the Log unit only, not any WO in this ADP. (**SO-1 is
   closed**, 2026-07-28, ADP-002 Amendment 2 — WO-120 is unheld.)
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
