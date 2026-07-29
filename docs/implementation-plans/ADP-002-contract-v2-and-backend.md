# ADP-002: Contract v2 and Backend Realignment

**Status:** **AUTHORIZED — owner, 2026-07-28, as drafted; amended same day to add
WO-118a.** Scope: WO-117 – WO-119, **WO-118a**, and WO-121 – WO-124, under the §2
grant (local build to green on synthetic fixtures). WO-120 remains held per §3.
Pushes, CI and real-media runs stay separately gated in §3.

> **Amendment 1, owner, 2026-07-28 — WO-118a added.** As drafted, this ADP gave
> WO-120 `speed_proposer.py` and left **`trim_proposer.py` owned by nothing**,
> while `SPEC.md` §4.1 changes it substantially: the v2 segment shape, and the
> retirement of the 1.0 s floor (A-6). Found during WO-117, when the v1 test
> `test_respects_the_one_second_floor` turned out to assert behaviour the spec
> now forbids. Left unowned, A-6 would have been a decision that was made and
> never implemented. **WO-118a is unheld** — it depends on nothing SO-1 blocks.
**Program ID:** ADP-002
**Type:** Autonomous Delivery Program
**Owner:** Repository Owner
**Created:** 2026-07-28
**Execution Window:** From authorization until WO-123 merges green and WO-124
reports its measurements, or until a stop-and-ask in §3 applies.
**Governing docs:** [CONSTRAINTS.md](../CONSTRAINTS.md) · [SPEC.md](../../SPEC.md)
(accepted 2026-07-28) · [DECISIONS.md](../DECISIONS.md) (decided 2026-07-28)
**Plan of record:** [PLAN-v3z-rebuild.md](PLAN-v3z-rebuild.md) §4

---

## 1. Purpose

Turn the accepted `SPEC.md` into code: schema v2, and the backend realigned to
it. This is the artifact that moves the rebuild from "specified" to "authorized
to build."

**Its predecessor's gates are met.** ADP-001's blocking condition for a contract
freeze was ADR-008's prototype-before-freeze rule; v3a→v3z *was* that prototype
and DECISIONS A-8 closed it. `SPEC.md` §3 is the frozen contract. There is
nothing further to decide before WO-117 starts.

### A departure from ADP-001's shape, stated rather than hidden

ADP-001 pointed at a separate approved backlog document for per-WO scope and
gates. **This ADP carries them itself, in §4.** No `v3z-backlog.md` is written.

The reason is the failure mode `CLAUDE.md` names: this repository has repeatedly
had far more specification than code. Eight more WO documents restating §4 in
longer form would be the same mistake in a new folder. §4 is the scope authority
for its Work Orders, and each row's *Owns* column is the file-scope rule that
makes the lanes safe — the discipline inherited from `m1-backlog.md`.

## 2. Execution Authority (what this ADP grants)

Under this ADP the assistant may proceed **locally** and without voluntary
pauses through the WO sequence in §5:

- implement WO scope on a short-lived per-WO branch, within that WO's *Owns*
  file scope and no wider;
- run the WO's completion gate in §4;
- write and update the WO's docs and review records in the same change;
- commit to the branch and merge to **local** `main` when the gate passes;
- start the next dependency-ready WO.

That is the whole grant: **local build to green, on synthetic fixtures.**

## 3. Withheld — stop-and-ask, not judgment calls

**Per-action owner authorization required:**
- **Every push to the public `origin`.** Prior authorization never carries to the
  next push. As of 2026-07-28 `origin/main` is at `HEAD`; every commit made under
  this ADP is local until a named, per-push authorization.
- **Adding or running GitHub Actions / any CI.** None exists and it is not to be
  introduced ambiently.

**Blocked until a prior gate clears:**
- **Running anything against real footage.** Requires an ADR-002-style consent
  and lifecycle record first. Code may be written and tested against synthetic
  fixtures before then; it may not be *run against real media* until that record
  exists. This is what holds WO-135 out of this ADP entirely.
- **WO-120, the speed proposer**, until `SPEC.md` §14 **SO-1** is closed. Its
  rules are not yet specified to the point of determinism, and guessing
  thresholds in code is how an unspecified decision gets made by an agent. See
  §6.
- **Any frontend work.** ADP-003 is a separate authorization gated on WO-124's
  numbers.

**New governance (a new decision, a `SPEC.md` amendment, or a new WO):**
- Amending `SPEC.md` — including closing SO-1 – SO-4. Acceptance froze it; an
  agent proposes amendments, an owner accepts them.
- Any dependency not pre-declared by WO-117's manifest.
- Every guardrail in [CONSTRAINTS.md](../CONSTRAINTS.md), unchanged and binding:
  person identification, writes beneath `media_root`, outbound network from the
  media path, relaxing local-delivery security, committing real footage or
  thumbnails or the mockups.

## 4. Work Order set and completion gates

`SPEC.md` section references are the scope authority for each row.

| WO | Scope | Owns | Completion gate |
|---|---|---|---|
| **WO-117 · Contract kernel v2** | `SPEC.md` §3 frozen as code: Pydantic models, regenerated TS types, updated service Protocols, the dependency manifest | `backend/contracts/`, `frontend/src/types/`, `pyproject.toml`, `package.json` | Models validate a §3.2 example; save→load byte-equivalent; `origin`/`proposals` retained across a round trip; TS and Pydantic are one source of truth. **Runs alone** |
| **WO-118 · Store v2** | Drop `stage_approvals` and `included`; **retain `disposition`** (A-3) with its three writers; add `stashed_segment`, `AudioMix`, output resolution, the music in-point. The §3.1 derivation — `effective_trim` / `effective_speed` — lives here | `backend/store/` | An assist never changes a field whose `origin` is `"user"` (§4.4), **with its own tests** — this is a correctness requirement, not a behaviour; toggle off restores exactly, hand-edits untouched; bin→restore exact; `out_s <= in_s` reads as out-of-reel with no `included` field anywhere |
| **WO-118a · Trim proposer v2** | `SPEC.md` §4.1 as code against the v2 shapes: one `Segment`, not a list. **Remove the 1.0 s floor** (DECISIONS A-6) and emit the sub-second and empty cases the Log has to warn about | `backend/propose/trim_proposer.py` | Proposals carry a single `Segment`; a clip whose best window is under a second **gets it**, and one where nothing clears the floors gets `NO_CLEAR_WINDOW` on the whole clip; an empty proposal is returned, not raised. The floor test is rewritten to assert A-6's behaviour rather than the rule it retired |
| **WO-119 · Media services** | Thumbnails and peaks on demand + cached; music probe and peaks **keyed by content hash**, working with no project in existence (§8 `GET /api/music/peaks`); `pick-file` via `osascript … choose file`, serving both track selection and relink | `backend/media/` (new) | Peaks for a track chosen before any project exists; cache hit on second call; picker returns a path or a clean cancel |
| **WO-120 · Speed proposer** | `SPEC.md` §4.2 as code: multiple `SpeedRange`s per clip in **source time**, retained proposals for reversibility | `backend/propose/speed_proposer.py` | **HELD — see §3 and §6.** Gate: deterministic on a fixture; ranges survive a trim-handle move (§3.2); the assist never proposes above 2.0× |
| **WO-121 · Renderer v2** | `amix` weighted by the two levels, replacing three non-composable mode branches. `setpts` + chained `atempo` per effective speed range. Skip out-of-reel clips. Resolution from the setting — `TARGET_W`/`TARGET_H` stop being constants | `backend/render/` | Duration ±0.5 s of computed reel length; **upscaling past the source refused or flagged, never silent**; every-clip-out fails with a stated reason, not an empty concat; GPS and identifying metadata stripped |
| **WO-122 · QA v2** | `resolution_ok` against the *setting*, not a hardcoded 1080×1920. `audio_ok` re-derived from the levels | `backend/qa/` | `music_level > 0` ⇒ output not silent; both at zero ⇒ silent **and** still a valid AAC track; a bad render is blocked **with its reason stated** |
| **WO-123 · API v2** | Delete `approve/{stage}` and every gate read. Add the §8 PATCH surface, relink, `download` with no `audio_mode`, thumb/peaks/pick-file. §8.2's optimistic-save failure path | `backend/api/` | Every §8 route present and no others; **each new mutating route has its own capability-token guard test that fails when the guard is removed**; 409 on `updated_at` mismatch; no path leaks |
| **WO-124 · Playback engine spike** | **Throwaway code, deleted afterwards.** Answers `SPEC.md` §6 / §14 SO-3 with measurements, not opinion | a scratch directory, deleted at closeout | A written record of: transition gap at a cut, seek error against the proxy's keyframe interval, whether `playbackRate` preview matches rendered `setpts`, how pitch is handled preview-vs-export, and how the music bed holds sync across a transition and a seek. **A number for each, or a stated reason it could not be measured** |

**Not in this ADP:** WO-125 – WO-132 (frontend, ADP-003) · WO-133 – WO-135
(verification and real footage, ADP-004) · WO-115a/115b (absorbed into WO-135).

## 5. Sequence and gates

```
WO-124 (spike) ──────────────────────────────► [numbers in hand] ──► gates ADP-003
   starts immediately, parallel to everything

WO-117 (alone, contract freeze) ── DONE, merged
   │
   ├── WO-118  store
   ├── WO-118a trim proposer
   ├── WO-119  media
   ├── WO-121  renderer ─┐
   ├── WO-122  QA ───────┤
   └── WO-123  API       │
                         └─► [ADP-002 closes: all merged green on fixtures]

WO-120 speed proposer ····· HELD on SPEC.md §14 SO-1
```

**Two gates interrupt autonomy by design:**

1. **WO-117 runs alone.** Nothing else starts until the contract is merged, for
   the same reason WO-101 did: six lanes editing a schema in parallel is how a
   contract stops being one.
2. **WO-120 does not start** until SO-1 is closed by an owner-accepted `SPEC.md`
   amendment. If SO-1 is still open when everything else is green, **this ADP
   closes without WO-120** and the speed proposer moves to its own authorization.
   DECISIONS A-5a — speed built last, de-scopable to manual — is what makes that
   safe.

**WO-124 depends on nothing in this ADP** and should start on the day it is
signed. It is the highest risk in the plan and the only item whose failure
invalidates work that has not been done yet.

## 6. Why WO-120 is held rather than dropped or guessed

`SPEC.md` §4.2 gives the rule — ramp dull stretches to 1.5×–2.0× — and then says
in its own words that the thresholds, the minimum ramp length and the merge rule
must be fixed before implementation. They are not fixed.

Three options were available and the middle one is taken:

- **Guess them in code.** Rejected. An agent choosing a dullness threshold is an
  unrecorded product decision, and §4.2's own naming defect is a standing example
  of what those cost later.
- **Hold the WO.** Taken. Everything else proceeds; one lane waits.
- **Block the ADP.** Rejected as disproportionate — SO-1 touches one file.

## 7. Execution rules (per WO)

- Branch `wo-NNN-<slug>` off local `main`; keep changes within the WO's *Owns*
  scope.
- Add a dependency only if WO-117's manifest pre-declared it — otherwise
  stop-and-ask.
- Run the §4 completion gate before merging to local `main`.
- Merge to **local** `main` when the gate passes; **do not push** without a
  per-push authorization (§3).
- Record honest outcomes: a gate that could not run is logged with the exact
  command and the reason, never silently skipped.
- **No claim in [EVIDENCE-LEDGER.md](../specs/EVIDENCE-LEDGER.md) moves off
  `assumed` under this ADP.** Everything here runs on synthetic fixtures.

## 8. Authorization

```
Authorized:            2026-07-28   by  Repository Owner (via session chat)
Scope granted:         WO-117 – WO-119, WO-118a, WO-121 – WO-124
                       (WO-120 held per §3)
Narrowing / notes:     None. Authorized as drafted; amended same day to add
                       WO-118a — see Amendment 1 at the head of this file.
```

The grant does **not** extend to pushes to the public `origin`, to CI, to
execution against real media, or to amending `SPEC.md` — all of which remain the
stop-and-asks in §3.

## 9. Closeout

ADP-002 closes when WO-117 – WO-119 and WO-121 – WO-123 are merged green on
synthetic fixtures and **WO-124 has reported its numbers**. Closeout deletes the
spike's code, updates `handoff.md`, and writes ADP-003 — whose content depends on
what WO-124 found. If WO-124 shows the Monitor cannot be made good enough to
judge an edit on, **`SPEC.md` §6 and the v3z design change before ADP-003 is
written**, which is the entire reason the spike runs first.
