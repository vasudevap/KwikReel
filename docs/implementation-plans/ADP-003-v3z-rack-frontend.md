# ADP-003: The v3z Rack Frontend

**Status: DRAFT — NOT AUTHORIZED.** Prepared at ADP-002 closeout, 2026-07-30.
No frontend implementation, harness rerun, spike deletion, branch, push or CI
action is granted until the owner explicitly authorizes §8.

**Program ID:** ADP-003

**Owner:** Repository Owner

**Governing:** [`docs/CONSTRAINTS.md`](../CONSTRAINTS.md) · [`SPEC.md`](../../SPEC.md) · [`docs/DECISIONS.md`](../DECISIONS.md)

**Plan:** [`PLAN-v3z-rebuild.md`](PLAN-v3z-rebuild.md) §4

**Design baseline:** `docs/design-claude/mockup-v3z.html` and generator — local, gitignored, never committed

**Engineering input:** [`WO-124-playback-findings.md`](../specs/WO-124-playback-findings.md)

## 1. Purpose and entry gate

Build the accepted v3z rack as one live React view against the v2 API. The
entry gate is met: ADP-002 is closed; SO-2 and SO-4 are closed; WO-124 measured
the playback engine and the design survived. This document is still only a
proposal until §8 is authorized.

WO-125 runs alone. WO-126 then runs alone to establish the app kernel, typed
module slots and client. After both barriers merge, WO-127 – WO-132 may run in
parallel because their write scopes are disjoint and they consume those frozen
interfaces. WO-127 uses the measured two-video strategy.

## 2. Proposed execution authority

If authorized, the program grants local implementation, tests, typecheck and
build on synthetic/mock data; small local commits; and local merges in the
dependency order below. It grants no push, CI, real-media run, `SPEC.md`
amendment, new dependency, or change outside §4.

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
| **WO-125 · Rack design system** | Extract v3z tokens and primitives: modules, ears, screws, keys, LEDs, seven-segment/VFD/LCD glass, housings, glyphs and embedded fonts. Gate: all primitives render from typed props; the fixed-size causes in `SPEC.md` §10.1 are encoded; token tests, typecheck, build and local-browser smoke pass | `frontend/src/rack/`; `frontend/tests/wo-125/` |
| **WO-126 · App shell, state and client v2** | Six states as one view; typed module-slot interface with honest placeholders; mock/live clients; optimistic PATCH queue; visible 409 revert and Log message; correct the manifest's stale description without touching dependencies or scripts. Gate: queued writes preserve order, conflicts revert visibly, mock/live shapes agree, and the empty shell builds | `frontend/src/app/`; `frontend/src/main.tsx`; `frontend/tests/wo-126/`; `frontend/package.json` description field only |
| **WO-127 · Monitor and Transport** | Dual-video queue, clip scrub, target length, resolution selector and Loop. **Before completion:** rerun the WO-124 harness foregrounded, record the result in the findings, then delete the spike directory. Gate: measured strategy used; preview rate/queue tests, typecheck, build and local-browser smoke pass | `frontend/src/monitor/`; `frontend/tests/wo-127/`; `spike/wo-124-playback/` (rerun, then delete); `docs/specs/WO-124-playback-findings.md` (append result only) |
| **WO-128 · Sound** | Reel-axis music/clip waveforms, two level sliders, cursor, playing wash, music in-point and track picker. Gate: both levels and in-point PATCH correctly; 0/0 remains representable; pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/sound/`; `frontend/tests/wo-128/` |
| **WO-129 · Clip index** | Four-row window, row controls and the three derived out states. Gate: exactly four addressable rows at any clip count; reorder/link/bin/mute actions map to v2 routes; nothing disappears or greys out; pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/index/`; `frontend/tests/wo-129/` |
| **WO-130 · Editor** | Trim handles, speed lane and trim-proposal reject/rerun housing. Gate: crossed handles permit empty trims, source-time speed survives handle motion, user-origin stickiness is preserved, and pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/editor/`; `frontend/tests/wo-130/` |
| **WO-131 · Log** | Three-line visible strip, severity/recency rules, scrolling and standing lines. Gate: warning/fault displacement and standing-line behavior match `SPEC.md` §7; pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/log/`; `frontend/tests/wo-131/` |
| **WO-132 · Reel row and HUD** | Sources/Trim/Speed/Save, derived length, rename, Sources confirmation, LOCAL/nameplate. Gate: controls map to v2 state; fixed-width counters/names satisfy §10.1 causes; pure logic tests, typecheck, build and local-browser smoke pass | `frontend/src/reel/`; `frontend/tests/wo-132/` |

Existing generated `frontend/src/types/contracts.ts` is read-only. Apart from
WO-126's exact description-field correction, package manifests, lockfiles,
Vite config and backend code are read-only under this ADP.

## 5. Dependency graph and lanes

```text
WO-125 rack system
   └── WO-126 app shell/client + typed slots
          ├── WO-127 monitor + harness rerun/delete
          ├── WO-128 sound
          ├── WO-129 clip index
          ├── WO-130 editor
          ├── WO-131 log
          └── WO-132 reel/HUD
```

WO-125 and then WO-126 are serial barriers. Each of WO-127 – WO-132 runs in its
own write-isolated branch/worktree after both are on local `main`. Merge order
after the barriers is WO-127 through WO-132, followed by clean tests,
typecheck, build and local-browser smoke. ADP-004's WO-133/WO-134 owns guards
and end-to-end integration; it is not smuggled into this program.

## 6. Program gates

- From `frontend/`, `node --test --experimental-strip-types
  tests/wo-*/*.test.mjs`, `npm run typecheck` and `npm run build` pass after
  every applicable WO and at convergence. Tests exercise pure state and
  arithmetic modules; no runner dependency or test-script edit is needed.
- Each visual WO passes a local-browser smoke against the v3z baseline using
  mock/synthetic state only. This is implementation QA, not evidence.
- No dependency, script, version, lockfile, generated-contract or backend drift;
  WO-126's declared description-only correction is the sole manifest change.
- No tracked design files, media, private paths or consent artifacts.
- WO-127 records the foreground measurement and deletes the spike code.
- State remains honest: this ADP proves implementation on mock/synthetic data,
  not usability or product quality.

## 7. Closeout

Close when WO-125 – WO-132 are merged locally and the convergence gates pass.
Update the briefing layer and ledger, then draft ADP-004. Real-footage work in
ADP-004 remains held until a consent record exists.

## 8. Authorization

```text
Authorized:            NO
Scope proposed:        WO-125 – WO-132, local mock/synthetic build only
Still withheld:        pushes, CI, real media, new dependencies, SPEC/design changes
Owner action needed:   explicit authorization of this ADP
```
