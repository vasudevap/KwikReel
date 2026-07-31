# Handoff

**Updated 2026-07-30**, WO-125 merged locally; WO-126 is next.

## The one-paragraph version

The M1 backend is realigned to **`SPEC.md`, accepted 2026-07-28** — the
spec written forward from **v3z**, the design a 26-version exploration ended at,
and a materially different product from the one M1 was built for. That old
frontend is deleted; the superseded record lives in `docs/archive/`; the
surviving guardrails are `docs/CONSTRAINTS.md`; the departures are decided in
`docs/DECISIONS.md`. **ADP-002 closed 2026-07-30** after all eleven Work Orders
met their synthetic gates. Amendment 7 narrowly retains the WO-124 harness
through WO-127 because accepted `SPEC.md` §6.7 requires one foreground rerun
before the Monitor ships. **ADP-003 was authorized 2026-07-30 and amended the
same day** after a contract audit found that reject, reversible binning, the
persistent Log, music probing and automatic link repair had no complete
frontend-to-server path. `DECISIONS.md` §5 and amended `SPEC.md` §8 make those
server-owned actions; ADP-003 Amendment 1 adds **WO-123a as the first serial
barrier**, before WO-125. **WO-123a is now implemented and merged locally**:
the corrected actions, persistent Log wiring, music probe, root-confined repair
and `Referer` guard pass their focused and synthetic end-to-end gates.
**WO-125 has now established the frontend's typed v3z rack design system**:
fixed geometry, modules, hardware controls, displays, housings, glyphs and
embedded fonts. The app shell and product surfaces have not begun. The suite is
deliberately partly red across the schema seam (the box below).

## What exists

**Backend — its ADP-002 module gates and WO-123a operability gate pass on
synthetic fixtures.**

| Module | State |
|---|---|
| `backend/contracts/` | **Schema v2 — WO-117, done.** `SPEC.md` §3 as Pydantic models + generated TS types + service Protocols. Contract gate 10/10 |
| `backend/ingest/` | **Proxy recipe v2 — WO-116a, done.** ffprobe → `SourceIndex`, rotation-corrected, 540×960 proxies **carrying stereo AAC**, keyframes ~1 s apart. Still **slow on real footage** — no `-preset`, no hardware encoder, serial scan, and audio encoding adds to that (WO-135's problem, not WO-116a's) |
| `backend/analysis/` | OpenCV per-second signals. The letterbox/exposure fault is **fixed** (WO-116, `3d0d0d6`), with two regression tests |
| `backend/propose/` (trim) | **v2 — WO-118a, done.** `SegmentsProposal.value` is one `Segment`, not a list; the 1.0 s floor is retired (A-6) — a proposal may be sub-second or empty, neither padded nor raised |
| `backend/propose/` (speed) | **v2 — WO-120, done.** Deterministic dull-stretch proposals in source time, retained for reversibility; the completion tests cover the threshold, duration, rate and trim-stability boundaries |
| `backend/store/` | **Schema v2 — WO-118, done.** Four modules: `project_store` (lossless save/load, optimistic concurrency, the §3 invariants), **`derive`** (§3.1's `effective_trim`/`effective_speed` and §3.4's membership, precedence, played duration and reel length — **what renders is derived here, never read off `clip.segment`**), `edits` (§4.3's bin/restore and hand edits, §4.5's disposition writers) and `log_store` (§7.3's `log.json`) |
| `backend/media/` | **v2 — WO-119, done.** Cached JPEG thumbnails and waveform peaks in a separate local cache; music peaks are content-hash keyed before a project exists; native folder/file pickers return a path or clean cancellation |
| `backend/render/` | **v2 — WO-121, done.** One H.264/AAC export from originals and the derived timeline: effective trims and speed ranges, chained `atempo`, arithmetic duration clamps, project-selected resolution, weighted clip/music mix, out-of-reel skips, explicit upscale refusal, and source metadata stripping |
| `backend/qa/` | **v2 — WO-122, done.** Checks the derived reel against the project's own resolution and audio levels; blocks bad exports with stated reasons, including a valid silent AAC requirement at a 0/0 mix |
| `backend/api/` | **v2 core — WO-123, done; operability correction — WO-123a, done.** The API now exposes server-owned bin/restore, trim reject, pre-project music probe, root-confined hash repair and persistent Log read/append paths. Known server events populate the sidecar, client-observed failures are constrained and scrubbed, every mutation is capability-protected, and foreign `Origin`/`Referer` plus invalid `Host` are rejected |

Run it: `python -m backend.api.run`. (Use the repo's `.venv`; the system
`python3` has no pytest.)

> **⚠️ The suite is partly red, deliberately, and this is not a regression.**
> **168 pass · 3 fail · 1 module cannot import · 1 owner-gated skip.** API,
> renderer, QA and WO-123a gates
> pass. The remaining `tests/integration/test_internal_checkpoint.py` cannot
> import its retired v1 shapes, while the three failures in
> `tests/integration/test_full_flow_api.py` assert removed approval and
> audio-mode routes. Those tests are owned by withheld WO-134, not this ADP.
> They were previously masked by the API's v1 import error; their exposure is a
> scope finding, not a WO-123 regression. **Nothing in an authorized lane fails**:
> WO-118 cleared
> the ten `tests/store/test_store.py` failures that stood here and added 58
> tests. A bare `pytest` halts at the one collection error — add
> `--continue-on-collection-errors` for the whole-suite count.
> **If you are reading this and the numbers are worse, that IS a regression.**

**Frontend — rack foundation only.** `frontend/src/rack/` is the WO-125 typed
design system extracted from v3z: frozen geometry tokens, modules/ears/screws,
physical keys and state lamps/rings, seven-segment/VFD/LCD glass, locked
housings, CSS-drawn glyphs and embedded local fonts. Its 13 contract tests,
typecheck, production build and browser smoke pass; the browser gate confirmed
465 px monitor geometry and 26 px keys, plus a fixed 960 px rack with horizontal
overflow rather than reflow below the minimum. `main.tsx` remains a stub and
`types/contracts.ts` remains generated; WO-126 owns the app shell and client.

**Design — v3z is frozen, and lives outside the repo.**
`docs/design-claude/mockup-v3z.html`, plus its generator, whose state model is a
partial specification of trim stickiness, speed duration math and the audio mix.
**Gitignored by decision** — the repo is public and the mockups are the
product's look and feel. They exist on the owner's disk only, so this path does
not resolve on GitHub.

## What does not exist

- **No remaining ADP-002 implementation lane.**
  Contracts (WO-117), ingest (WO-116a), the trim proposer (WO-118a), the store
  (WO-118), reject semantics (WO-118b), media services (WO-119), and the speed
  proposer (WO-120), renderer (WO-121), output QA (WO-122), and API (WO-123)
  are v2.
- **No frontend app yet. ADP-003 is authorized and amended once.** WO-123a and
  WO-125 cleared the first two serial barriers. The rack foundation exists;
  WO-126's app shell, state and client have not begun.
- **`SPEC.md` owes nothing.** All four §14 items are closed: SO-1 2026-07-28,
  SO-2/SO-3/SO-4 2026-07-29. Two things the closures leave open are tracked as
  correction-pass risks rather than spec gaps — the unmeasured black-frame
  duration (§6.7) and whether one three-line strip can carry the Log's eight
  jobs (§7.2).
- **No frontend Log surface yet.** The backend sidecar is now complete:
  standing lines, ingest/proposal/assist/disposition/export events, warnings and
  job failures persist and survive reopen; the constrained client-failure route
  neither changes `project.updated_at` nor accepts `info`. WO-131 still owns the
  three-line visible strip and its severity/recency behavior.
- **No media, no corpus, no consent record.** Every ledger claim is `assumed`.
- **No real-footage run.** The two exit gates that need it have never run.

## In flight right now

**Nothing.** WO-125 is merged locally and its branch gate is clear. WO-126 is
the next serial barrier. The harness rerun and deletion still belong later to
WO-127.

**WO-124 is done.** [`docs/specs/WO-124-playback-findings.md`](docs/specs/WO-124-playback-findings.md)
— **SO-3 is answered and the v3z design survives.** The Monitor uses **two
`<video>` elements cross-swapped** (0.8 ms at the cut, against 36.3 ms for one
element reloaded — a 45× difference). Seeking is **frame-accurate** despite an
8.3 s GOP; `playbackRate` is exact; a plain `<audio>` music bed holds sync to
within 3.4 ms across a cut. The spike code is throwaway and is deleted at
WO-127 closeout. Amendment 7 retains it only long enough to satisfy `SPEC.md`
§6.7's required foreground rerun; WO-127 records that result before deletion.

## What happens next

1. **WO-126 is the next serial barrier** and freezes the app kernel/client
   against the corrected live API. WO-127 – WO-132 fan out only after all three
   barriers merge.
2. The legacy integration suite remains withheld to WO-134. Its visible v1
   failures are recorded in the suite box above and are not frontend work.

## The stop-and-asks that are open

**None.** The newest one was closed as follows.

**Closed 2026-07-30 — the frozen HTTP seam could not operate the frozen
frontend.** Raised by the post-authorization project review. The store already
had correct reject and bin primitives and the Log sidecar, and the media service
already had a music probe, but `SPEC.md` §8 and WO-123 exposed no route that let
the frontend use them. The Log also had no readers or production writers,
automatic content-hash repair had no action, and the binding cross-site
`Referer` guard had no implementation or test. The owner directed the
recommended correction to proceed. `DECISIONS.md` §5 makes these explicit
server-owned actions; `SPEC.md` §4.3, §7 and §8 are amended; ADP-003 Amendment 1
adds unheld WO-123a as the first serial barrier. The gap is **decided and
authorized, and WO-123a implemented it locally with focused security/API gates
and a synthetic create→scan→analyze→propose→control→export→Log flow.**

**Closed 2026-07-30 — §4.5's `dismissed` writer now has an owner decision.**
Raised by WO-118, 2026-07-29. `SPEC.md` §4.3 says reject (✕) *"discards this
clip's proposal — `disposition: "dismissed"`. The clip reverts to whole (or to
the user's own trim, if there is one)."* But §3.1's derivation reads any
retained proposal while the toggle is on, whatever its disposition — so a
rejected proposal still renders and the clip does **not** revert. At least three
readings close the gap and they are not equivalent:

1. **Reject nulls the proposal.** Matches §4.3's word *discards* and needs no
   amendment — but it deletes the very count A-3 kept `disposition` to produce,
   so a dismissal becomes unmeasurable and C-03 loses the denominator.
2. **The derivation skips dismissed proposals.** Keeps the count, and is an
   amendment to a frozen §3.1 — an owner decision by construction.
3. **Reject writes the whole clip as a user segment.** Satisfies both sections
   as written, and locks the trim assist out of that clip permanently, which
   may be intended ("I rejected this, stop proposing") or may not.

The owner chose reading (2): retain the proposal for audit, but skip it in
derivation. `DECISIONS.md` §4 and `SPEC.md` are amended; Amendment 6 unheld
WO-118b, which is now implemented and covered by store regression tests.

> **A smaller thing to know when reading the C-03 number, not a blocker.**
> §4.5 read literally makes a **binned** clip's untouched proposal `accepted` at
> export, because binning is §4.3's own control and not the handle move §4.5
> names. So *"Kept 14 of 19 AI trims"* counts proposals the user did not
> overrule, not proposals that reached the export. Implemented as written and
> recorded in the ledger's C-03 note rather than quietly corrected.

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

**`SPEC.md` §14 is empty.** Every item that stood here — the four §6 amendments,
SO-1, SO-2, SO-3, SO-4 — is closed. Two owner actions remain:

1. **Record an ADR-002-style consent** before anything runs against real
   footage. No closed or authorized program grants that run. **This now gates
   the end of the whole programme**: ADP-004's real-footage validation is the
   only thing that can move a ledger claim off `assumed`, and every claim is
   still `assumed`.
2. **Authorize pushes individually.** As of 2026-07-29 `origin/main` sits at
   `d64b256` — the last pre-acceptance commit — and everything since (the
   accepted spec, ADP-002, every Work Order merge) is local only. Nothing built
   under ADP-002 or ADP-003 is pushed until you say otherwise, one push at a
   time.

> **Withdrawn, and recorded so it does not come back.** A §9 QA-tolerance
> stop-and-ask stood here, raised on a percentage measured at one clip length.
> Re-measured 2026-07-29: the overshoot is a fixed 1–2 frames per ramped clip,
> scaling with clip *count* rather than ramped seconds, and
> `-t (kept_duration / rate)` removes it exactly. **§9 stands as written**; the
> remedy is a WO-121/WO-122 lane instruction in ADP-002 §4. See findings §3.

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
- **`frontend/package.json` has one known stale sentence.** Its description
  still says ADP-003 waits on WO-124. The entry gate is now met, but the file
  remains untouched until its authorized owner runs; WO-126 owns the
  description-only correction.
