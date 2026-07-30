# ADP-003: The v3z Rack Frontend

**Status: AUTHORIZED — owner, 2026-07-30, as drafted; amended 2026-07-30 to add
the serial WO-123a frontend-operability correction.** Scope: WO-123a and
WO-125 – WO-132, local implementation, tests, builds and browser smoke on
mock/synthetic state under §2 and §4. Push, CI, real-media, dependency and
design changes remain withheld.

> **Amendment 1, owner, 2026-07-30 — add WO-123a before frontend work.** A
> post-authorization review found that the frozen §8 route table could not
> express four behaviours the already-accepted product requires: §4.3's reject
> and reversible bin transitions; §7's persistent Log and its writers; a
> server-computed music hash and duration before a project exists; and §8.3's
> automatic content-hash link repair. It also found that the binding security
> constraint's `Referer` half had no implementation or guard test.
> [`DECISIONS.md` §5](../DECISIONS.md) chooses explicit server-owned actions and
> `SPEC.md` §8 is amended narrowly. **WO-123a is added, unheld, and runs alone
> before WO-125.** This amendment authorizes that local correction on synthetic
> fixtures; it does not authorize any other backend, dependency, design, push,
> CI or real-media change.

**Program ID:** ADP-003

**Owner:** Repository Owner

**Governing:** [`docs/CONSTRAINTS.md`](../CONSTRAINTS.md) · [`SPEC.md`](../../SPEC.md) · [`docs/DECISIONS.md`](../DECISIONS.md)

**Plan:** [`PLAN-v3z-rebuild.md`](PLAN-v3z-rebuild.md) §4

**Design baseline:** `docs/design-claude/mockup-v3z.html` and generator — local, gitignored, never committed

**Engineering input:** [`WO-124-playback-findings.md`](../specs/WO-124-playback-findings.md)

## 1. Purpose and entry gate

Build the accepted v3z rack as one live React view against the v2 API. The
entry gate is met: ADP-002 is closed; SO-2 and SO-4 are closed; WO-124 measured
the playback engine and the design survived. The owner authorized this program
on 2026-07-30; §8 records the grant. Amendment 1 corrects the live API seam
before any frontend interface is frozen.

WO-123a runs alone. WO-125 then establishes the rack system, and WO-126 runs
alone after it to establish the app kernel, typed module slots and client.
After all three barriers merge, WO-127 – WO-132 may run in parallel because
their write scopes are disjoint and they consume those frozen interfaces.
WO-127 uses the measured two-video strategy.

## 2. Execution authority

The program grants local implementation, tests, typecheck and build on
synthetic/mock data; small local commits; and local merges in the dependency
order below. Amendment 1 additionally grants WO-123a's narrow local backend/API
correction against the already-amended `SPEC.md`. It grants no push, CI,
real-media run, further `SPEC.md` amendment, new dependency, or change outside
§4.

## 3. Stop-and-ask triggers

- Any need to alter `SPEC.md`, the frozen contract, the v3z baseline, or a
  cross-lane interface.
- Any new npm dependency, script, version, or lockfile edit. WO-126 may correct
  `frontend/package.json`'s stale description field only.
- Any real footage, private path, consent record, or committed design asset.
- Any bind beyond `127.0.0.1`, security-control weakening, push or CI action.
- The foreground harness rerun materially contradicts WO-124's recorded result.
- A component cannot fit its fixed geometry without changing the design.

## 4. Work Orders and exhaustive write scopes

| WO | Scope and gate | Owns |
|---|---|---|
| **WO-123a · Frontend-operability API completion** | Implement `DECISIONS.md` §5 and amended `SPEC.md` §4.3, §7 and §8: protected server actions for bin/restore and trim reject; server-owned Log creation/writers/read plus constrained path-scrubbed client-failure append; server-side music probe returning content hash and duration before a project; protected content-hash repair beneath `media_root`; and the missing cross-site `Referer` guard. Gate: each new mutation has a capability-token guard test; bin/restore and reject preserve the store semantics exactly; Log standing lines, proposal detail, warnings, transitions, failures and export summary survive reopen; music probe→peaks works with no project; link repair preserves edit state and never searches outside `media_root`; a v2 synthetic flow covers create→scan→analyze→propose→control actions→export→Log; the known WO-134 legacy failures do not worsen | `backend/api/`; `backend/contracts/interfaces.py`; `backend/store/log_store.py`; `tests/api/`; `tests/guards/test_security.py`; `tests/integration/test_frontend_operability.py` (new) |
| **WO-125 · Rack design system** | Extract v3z tokens and primitives: modules, ears, screws, keys, LEDs, seven-segment/VFD/LCD glass, housings, glyphs and embedded fonts. Gate: all primitives render from typed props; the fixed-size causes in `SPEC.md` §10.1 are encoded; token tests, typecheck, build and local-browser smoke pass | `frontend/src/rack/`; `frontend/tests/wo-125/` |
| **WO-126 · App shell, state and client v2** | Six states as one view; typed module-slot interface with honest placeholders; mock/live clients; optimistic PATCH queue; visible 409 revert and Log message; correct the manifest's stale description without touching dependencies or scripts. Gate: queued writes preserve order, conflicts revert visibly, mock/live shapes agree, and the empty shell builds | `frontend/src/app/`; `frontend/src/main.tsx`; `frontend/tests/wo-126/`; `frontend/package.json` description field only |
| **WO-127 · Monitor and Transport** | Dual-video queue, clip scrub, target length, resolution selector and Loop. **Before completion:** rerun the WO-124 harness foregrounded, record the result in the findings, then delete the spike directory. Gate: measured strategy used; preview rate/queue tests, typecheck, build and local-browser smoke pass | `frontend/src/monitor/`; `frontend/tests/wo-127/`; `spike/wo-124-playback/` (rerun, then delete); `docs/specs/WO-124-playback-findings.md` (append result only) |
| **WO-128 · Sound** | Reel-axis music/clip waveforms, two level sliders, cursor, playing wash, music in-point and track picker. Gate: both levels and in-point PATCH correctly; 0/0 remains representable; pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/sound/`; `frontend/tests/wo-128/` |
| **WO-129 · Clip index** | Four-row window, row controls and the three derived out states. Gate: exactly four addressable rows at any clip count; reorder/link/bin/mute actions map to v2 routes; nothing disappears or greys out; pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/index/`; `frontend/tests/wo-129/` |
| **WO-130 · Editor** | Trim handles, speed lane and trim-proposal reject/rerun housing. Gate: crossed handles permit empty trims, source-time speed survives handle motion, user-origin stickiness is preserved, and pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/editor/`; `frontend/tests/wo-130/` |
| **WO-131 · Log** | Three-line visible strip, severity/recency rules, scrolling and standing lines. Gate: warning/fault displacement and standing-line behavior match `SPEC.md` §7; pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/log/`; `frontend/tests/wo-131/` |
| **WO-132 · Reel row and HUD** | Sources/Trim/Speed/Save, derived length, rename, Sources confirmation, LOCAL/nameplate. Gate: controls map to v2 state; fixed-width counters/names satisfy §10.1 causes; pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/reel/`; `frontend/tests/wo-132/` |

Existing generated `frontend/src/types/contracts.ts` is read-only. Apart from
WO-123a's exact backend/test scope and WO-126's exact description-field
correction, package manifests, lockfiles, Vite config and all other backend
code are read-only under this ADP.

## 5. Dependency graph and lanes

```text
WO-123a corrected live API seam
   └── WO-125 rack system
          └── WO-126 app shell/client + typed slots
                 ├── WO-127 monitor + harness rerun/delete
                 ├── WO-128 sound
                 ├── WO-129 clip index
                 ├── WO-130 editor
                 ├── WO-131 log
                 └── WO-132 reel/HUD
```

WO-123a, WO-125 and WO-126 are serial barriers, in that order. Each of
WO-127 – WO-132 runs in its own write-isolated branch/worktree after all three
are on local `main`. Merge order after the barriers is WO-127 through WO-132,
followed by clean tests, typecheck, build and local-browser smoke. WO-123a owns
only the correction that makes the live frontend possible; ADP-004's broader
WO-133/WO-134 guards and end-to-end integration are not smuggled into this
program.

## 6. Program gates

- From `frontend/`, `node --test --experimental-strip-types
  tests/wo-*/*.test.mjs`, `npm run typecheck` and `npm run build` pass after
  every applicable WO and at convergence. Tests exercise pure state and
  arithmetic modules; no runner dependency or test-script edit is needed.
- WO-123a's focused API, security and frontend-operability integration gates
  pass before WO-125 starts. The whole-suite result may retain only the exact
  legacy WO-134 failures already recorded in `handoff.md`; no new failure or
  collection error is permitted.
- Each visual WO passes a local-browser smoke against the v3z baseline using
  mock/synthetic state only. This is implementation QA, not evidence.
- No dependency, script, version, lockfile or generated-contract drift.
  WO-123a's declared paths are the only backend exception, and WO-126's
  description-only correction is the sole manifest change.
- No tracked design files, media, private paths or consent artifacts.
- WO-127 records the foreground measurement and deletes the spike code.
- State remains honest: this ADP proves implementation on mock/synthetic data,
  not usability or product quality.

## 7. Closeout

Close when WO-123a and WO-125 – WO-132 are merged locally and the convergence
gates pass. Update the briefing layer and ledger, then draft ADP-004.
Real-footage work in ADP-004 remains held until a consent record exists.

## 8. Authorization

```text
Authorized:            2026-07-30 by Repository Owner (via session chat)
Scope granted:         WO-123a and WO-125 – WO-132,
                       local mock/synthetic build only
Still withheld:        pushes, CI, real media, new dependencies,
                       further SPEC changes and design changes
Narrowing / notes:     Authorized as drafted; Amendment 1 (2026-07-30)
                       added WO-123a as the first serial barrier after
                       DECISIONS §5 and SPEC.md §8 closed the operability gap
```
