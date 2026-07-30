# ADP-002: Contract v2 and Backend Realignment

**Status:** **AUTHORIZED — owner, 2026-07-28, as drafted; amended 2026-07-28 to
add WO-118a, to unhold WO-120, and to add WO-116a; amended 2026-07-29 to make
WO-120 a closeout gate; amended 2026-07-30 to make test ownership executable,
serialize renderer → QA, add held WO-118b, unhold it after the reject decision,
and retain the playback harness through WO-127. **CLOSED 2026-07-30.** Scope:
**WO-116a**, WO-117 – WO-124, plus **WO-118b, all unheld** following the
2026-07-30 reject decision, under the §2 grant (local build to green on
synthetic fixtures).
Pushes, CI and real-media runs stay separately gated in §3.

> **Amendment 1, owner, 2026-07-28 — WO-118a added.** As drafted, this ADP gave
> WO-120 `speed_proposer.py` and left **`trim_proposer.py` owned by nothing**,
> while `SPEC.md` §4.1 changes it substantially: the v2 segment shape, and the
> retirement of the 1.0 s floor (A-6). Found during WO-117, when the v1 test
> `test_respects_the_one_second_floor` turned out to assert behaviour the spec
> now forbids. Left unowned, A-6 would have been a decision that was made and
> never implemented. **WO-118a is unheld** — it depends on nothing SO-1 blocks.

> **Amendment 2, owner, 2026-07-28 — WO-120 unheld.** `SPEC.md` §14 SO-1 is
> closed: the dullness thresholds (`motion_energy <= 0.25` and `audio_rms <=
> 0.25`), the minimum ramp length (1.5 s), the merge rule (gap < 0.5 s), and the
> rate mapping (continuous, `rate = 1.5 + 0.5 * d`) are now fixed in `SPEC.md`
> §4.2. **WO-120 is unheld** and joins WO-118, WO-118a, WO-119, WO-121 – WO-123
> as dependency-ready under the §2 grant. §6's reasoning for why it was held no
> longer applies — the parameters are recorded, not guessed.

> **Amendment 3, owner, 2026-07-28 — WO-116a added.** WO-124 found that
> **`make_proxy` passes `-an`, so every proxy is silent**, and this ADP assigned
> `backend/ingest/` to no Work Order. The plan called ingest "survives", and
> against `SPEC.md` §3 the *contract* does — its **proxy recipe** does not. A
> silent proxy means the Monitor cannot preview clip audio at all, which leaves
> `clip_level` acting on nothing, the Sound unit drawing traces for audio that
> cannot play, and §6's "preview loudness must match export loudness"
> unsatisfiable. **WO-116a is unheld**, owns `backend/ingest/`, and also carries
> the proxy GOP change WO-124 recommended.

> **Amendment 4, owner, 2026-07-29 — WO-120 gates closeout, and the record is
> squared.** §9's closeout condition predated Amendment 2: it still read
> "WO-117 – WO-119 and WO-121 – WO-123", written when WO-120 was held, so the
> ADP could have closed without the speed proposer it had since unheld. **The
> owner's call: it cannot.** §9 now requires every §4 Work Order merged green.
> Squared at the same time: §8's summary block said "amended twice" and omitted
> WO-116a from its scope line; and two 2026-07-29 §4 edits that landed without
> an amendment note are recorded here — WO-118's scope gained the `log.json`
> sidecar when `SPEC.md` §7.3 closed SO-2, and the ramp-overshoot lane
> instruction was added for WO-121/WO-122 after the 2026-07-29 re-measurement.

> **Amendment 5, owner, 2026-07-30 — executable test ownership, renderer → QA
> sequencing, and held WO-118b.** The §4 *Owns* cells were declared to be the
> file-scope lock, but named production paths only while every completion gate
> requires tests. Completed WOs had therefore changed matching `tests/` paths
> outside the literal manifest, and the remaining WO-121 and WO-122 both need
> the mixed legacy file `tests/render/test_render_qa.py`. The manifest now names
> every production and test path explicitly. **WO-121 and WO-122 are one serial
> lane, renderer before QA**; WO-122 owns the retirement/split of that mixed
> legacy file. WO-119, WO-120 and WO-123 remain independent lanes.
>
> The same review found that WO-118 merged with one specified writer withheld:
> reject must write `disposition: "dismissed"` and revert the effective trim,
> while §3.1 still derives from any retained proposal. **WO-118b is added as a
> closeout gate and is held.** This amendment records the corrective scope; it
> does **not** choose among the three product readings in `handoff.md`. A dated
> `DECISIONS.md` entry, any required `SPEC.md` amendment, and a later owner
> amendment unholding WO-118b are still required before its implementation.

> **Amendment 6, owner, 2026-07-30 — reject semantics decided; WO-118b
> unheld.** The owner chose the second reading in `DECISIONS.md` §4: a rejected
> trim remains retained with `disposition: "dismissed"`, but §3.1's derivation
> skips it. `SPEC.md` §3.1 and §4.3 are amended to match. **WO-118b is unheld**
> under the existing local synthetic-fixture grant and remains a closeout gate.

> **Amendment 7, owner, 2026-07-30 — retain the playback harness through
> WO-127.** Closeout originally required deleting all WO-124 spike code, while
> accepted `SPEC.md` §6.7 requires the same harness rerun in a foregrounded
> window before the Monitor ships. Deleting it here would make that required
> check impossible. The owner authorized the narrow resolution: ADP-002 closes
> with `spike/wo-124-playback/` retained; ADP-003 assigns WO-127 its foreground
> rerun and deletion after the result is recorded. No product requirement or
> `SPEC.md` text changes.

**Program ID:** ADP-002
**Type:** Autonomous Delivery Program
**Owner:** Repository Owner
**Created:** 2026-07-28
**Execution Window:** From authorization until §9's closeout condition is met —
every §4 Work Order including WO-118b merged green, WO-124's measurements
reported — or until a stop-and-ask in §3 applies.
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
The *Owns* cell is exhaustive: it includes both production and test paths.
There is no implicit permission to edit a matching test directory.

| WO | Scope | Owns | Completion gate |
|---|---|---|---|
| **WO-116a · Proxy recipe v2** | The proxy must be previewable as `SPEC.md` §5 and §6 assume. **Carry the source's audio** instead of `-an`, and set a keyframe interval of ~1 s instead of x264's 250-frame default | `backend/ingest/`; `tests/ingest/` | A proxy built from a source **with** audio carries a decodable AAC track — *the assertion that did not exist*; a proxy from a silent source still builds and plays; keyframe interval ≤ 1.0 s; the existing invariants hold unchanged (540×960, H.264, nothing written beneath `media_root`) |
| **WO-117 · Contract kernel v2** | `SPEC.md` §3 frozen as code: Pydantic models, regenerated TS types, updated service Protocols, the dependency manifest | `backend/contracts/`; `frontend/src/types/`; `pyproject.toml`; `frontend/package.json`; `tests/contracts/` | Models validate a §3.2 example; save→load byte-equivalent; `origin`/`proposals` retained across a round trip; TS and Pydantic are one source of truth. **Runs alone** |
| **WO-118 · Store v2** | Drop `stage_approvals` and `included`; **retain `disposition`** (A-3) with its three writers; add `stashed_segment`, `AudioMix`, output resolution, the music in-point. The §3.1 derivation — `effective_trim` / `effective_speed` — lives here. **Plus the `log.json` sidecar** (`SPEC.md` §7.3): append, 500-entry eviction oldest-first, standing entries exempt | `backend/store/`; `tests/store/` | An assist never changes a field whose `origin` is `"user"` (§4.4), **with its own tests** — this is a correctness requirement, not a behaviour; toggle off restores exactly, hand-edits untouched; bin→restore exact; `out_s <= in_s` reads as out-of-reel with no `included` field anywhere; **the Log survives close→reopen, evicts at 500, and never evicts a standing entry** |
| **WO-118a · Trim proposer v2** | `SPEC.md` §4.1 as code against the v2 shapes: one `Segment`, not a list. **Remove the 1.0 s floor** (DECISIONS A-6) and emit the sub-second and empty cases the Log has to warn about | `backend/propose/trim_proposer.py`; `tests/propose/test_proposer.py` | Proposals carry a single `Segment`; a clip whose best window is under a second **gets it**, and one where nothing clears the floors gets `NO_CLEAR_WINDOW` on the whole clip; an empty proposal is returned, not raised. The floor test is rewritten to assert A-6's behaviour rather than the rule it retired |
| **WO-118b · Reject semantics correction** | `DECISIONS.md` §4: retain the dismissed trim proposal for audit, but skip it in §3.1 derivation so reject reverts the effective trim without creating a user edit | `backend/store/derive.py`; `backend/store/edits.py`; `backend/store/__init__.py`; `tests/store/test_derive.py`; `tests/store/test_edits.py` | Reject makes the effective trim revert as §4.3 promises; retained proposal data and C-03 counting match the decision; toggle-on, toggle-off, existing user trim and re-run cases have regression tests |
| **WO-119 · Media services** | Thumbnails and peaks on demand + cached; music probe and peaks **keyed by content hash**, working with no project in existence (§8 `GET /api/music/peaks`); `pick-file` via `osascript … choose file`, serving both track selection and relink | `backend/media/` (new); `tests/media/` (new) | Peaks for a track chosen before any project exists; cache hit on second call; picker returns a path or a clean cancel |
| **WO-120 · Speed proposer** | `SPEC.md` §4.2 as code: multiple `SpeedRange`s per clip in **source time**, retained proposals for reversibility | `backend/propose/speed_proposer.py` (new); `backend/propose/__init__.py`; `tests/propose/test_speed_proposer.py` (new) | **Unheld — Amendment 2.** Gate: deterministic on a fixture; ranges survive a trim-handle move (§3.2); the assist never proposes above 2.0× |
| **WO-121 · Renderer v2** | `amix` weighted by the two levels, replacing three non-composable mode branches. `setpts` + chained `atempo` per effective speed range. Skip out-of-reel clips. Resolution from the setting — `TARGET_W`/`TARGET_H` stop being constants. **Clamp every ramped clip to `-t (kept_duration / rate)`** — see below | `backend/render/`; `tests/render/` | Duration ±0.5 s of computed reel length; **a ramped clip's rendered duration matches `SPEC.md` §3.4's arithmetic exactly**, not 1–2 frames over; **upscaling past the source refused or flagged, never silent**; every-clip-out fails with a stated reason, not an empty concat; GPS and identifying metadata stripped |
| **WO-122 · QA v2** | `resolution_ok` against the *setting*, not a hardcoded 1080×1920. `audio_ok` re-derived from the levels. **`duration_ok` keeps §9's ±0.5 s unchanged** — the fix for the ramp overshoot is WO-121's clamp, not a wider tolerance. Runs after WO-121 and splits/retires the mixed v1 renderer/QA test file | `backend/qa/`; `tests/qa/` (new); `tests/render/test_render_qa.py` (retire or reduce to renderer-only) | `music_level > 0` ⇒ output not silent; both at zero ⇒ silent **and** still a valid AAC track; a bad render is blocked **with its reason stated**; **a multi-clip ramped reel lands inside ±0.5 s** — the regression test whose absence let the overshoot through |
| **WO-123 · API v2** | Delete `approve/{stage}` and every gate read. Add the §8 PATCH surface, relink, `download` with no `audio_mode`, thumb/peaks/pick-file. §8.2's optimistic-save failure path | `backend/api/`; `tests/api/`; `tests/guards/test_security.py`; `tests/support.py` | Every §8 route present and no others; **each new mutating route has its own capability-token guard test that fails when the guard is removed**; 409 on `updated_at` mismatch; no path leaks |
| **WO-124 · Playback engine spike** | **Throwaway code, deleted afterwards.** Answers `SPEC.md` §6 / §14 SO-3 with measurements, not opinion | `spike/wo-124-playback/` (deleted at closeout); `docs/specs/WO-124-playback-findings.md` | A written record of: transition gap at a cut, seek error against the proxy's keyframe interval, whether `playbackRate` preview matches rendered `setpts`, how pitch is handled preview-vs-export, and how the music bed holds sync across a transition and a seek. **A number for each, or a stated reason it could not be measured** |

> **The ramp duration overshoot — binding on WO-121 and WO-122.** WO-124
> measured `setpts` + `atempo` overshooting by a **fixed 1–2 frames per ramped
> clip** (+33 ms at 1.5×, +66 ms at 2.0×), *identical at every clip length* — so
> it scales with **clip count, not ramped seconds**, and accumulates linearly:
> six 2.0× clips measured +420 ms against a ±0.5 s gate.
>
> It is a correctness bug before it is a gate problem. `SPEC.md` §3.4's played-
> duration formula also drives **the reel length the user reads** (§2.4), so a
> twenty-ramped-clip reel displays 1:23 and exports 1:24.3.
>
> **`-t (kept_duration / rate)` removes it exactly** — 90 frames instead of 92,
> 3.0000 s instead of 3.0660 s, and the frames dropped are spurious tail frames
> the CFR resampler invented, not content. **No `SPEC.md` change is needed**,
> which is why this is a lane instruction and not the §9 stop-and-ask it was
> first raised as. Full measurements and the rejected alternatives:
> [WO-124-playback-findings.md §3](../specs/WO-124-playback-findings.md).

**Not in this ADP:** WO-125 – WO-132 (frontend, ADP-003) · WO-133 – WO-135
(verification and real footage, ADP-004) · WO-115a/115b (absorbed into WO-135).

## 5. Sequence and gates

```
WO-124 (spike) ──────────────────────────────► [numbers in hand] ──► gates ADP-003
   starts immediately, parallel to everything

WO-117 (alone, contract freeze) ── DONE, merged
   │
   ├── WO-118  store ── DONE ──► WO-118b reject ── DONE
   ├── WO-118a trim proposer ── DONE
   ├── WO-119  media ── DONE
   ├── WO-120  speed proposer ── DONE
   ├── WO-121  renderer ──► WO-122 QA ────────────── lane RQ (serial)
   └── WO-123  API ───────────────────────────────── lane A
                                                    │
                                                    └─► [ADP-002 closes:
                                                         every §4 WO green]
```

### Lane execution plan — Amendment 5

Each launched lane runs in its **own write-isolated worktree**, with one agent
and one active WO branch at a time. The lead/orchestrator owns only barriers,
merge order and stop-and-asks; it does not edit lane-owned paths.

| Lane | Work Orders | Branch order | Merge barrier |
|---|---|---|---|
| **M · media** | WO-119 — done | `wo-119-media` | Merged locally in this Work Order commit |
| **P · speed** | WO-120 — done | `wo-120-speed` | Merged locally at `3d776ba` |
| **RQ · render/QA** | WO-121 → WO-122 | `wo-121-renderer`, then refresh from local `main` and create `wo-122-qa` in the same lane worktree | WO-121 merges first; WO-122 starts from that merge and merges second |
| **A · API** | WO-123 | `wo-123-api` | May merge when WO-123's gate passes |
| **S · reject** | WO-118b — done | `wo-118b-reject` | Merged locally at `d819045` |

M, P, RQ, A and S may execute concurrently. The final convergence barrier is
§9: every lane merged, WO-118b green,
and the closeout records updated together. A merge conflict or need to touch a
path outside a row's *Owns* cell is a stop-and-ask, not permission to widen the
lane.

**One gate interrupted autonomy by design:**

1. **WO-117 runs alone.** Nothing else starts until the contract is merged, for
   the same reason WO-101 did: six lanes editing a schema in parallel is how a
   contract stops being one.

**WO-121 and WO-122 are one lane, in that order.** Their production directories
are disjoint, but the legacy renderer/QA test surface is not, and QA's
multi-clip duration gate consumes the renderer's v2 output. Amendment 5 makes
the real resource dependency explicit instead of pretending the directory
split makes them independent.

WO-120 was held on `SPEC.md` §14 SO-1 until Amendment 2 closed it (2026-07-28,
this session); it is now dependency-ready like the rest of §4's lanes.

**WO-124 depends on nothing in this ADP** and should start on the day it is
signed. It is the highest risk in the plan and the only item whose failure
invalidates work that has not been done yet.

## 6. Why WO-120 was held rather than dropped or guessed

**Historical — resolved by Amendment 2.** Kept for the reasoning; WO-120 is no
longer held.


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
Closed:                2026-07-30
Scope granted:         WO-116a and WO-117 – WO-124, all unheld
                       plus WO-118b, unheld by Amendment 6
Narrowing / notes:     Authorized as drafted; amended seven times —
                       Amendment 1 (2026-07-28) added WO-118a,
                       Amendment 2 (2026-07-28) unheld WO-120,
                       Amendment 3 (2026-07-28) added WO-116a,
                       Amendment 4 (2026-07-29) made WO-120 a closeout gate,
                       Amendment 5 (2026-07-30) made test ownership explicit,
                       serialized WO-121 → WO-122, and added held WO-118b.
                       Amendment 6 (2026-07-30) recorded the reject decision,
                       amended SPEC.md, and unheld WO-118b.
                       Amendment 7 (2026-07-30) retained the WO-124 harness
                       through WO-127, which owns its rerun and deletion.
                       See the head of this file.
```

The grant does **not** extend to pushes to the public `origin`, to CI, to
execution against real media, or to amending `SPEC.md` — all of which remain the
stop-and-asks in §3.

## 9. Closeout

**CLOSED 2026-07-30.** Every §4 Work Order — WO-116a, WO-117, WO-118, WO-118a,
WO-118b, WO-119, WO-120 and WO-121 – WO-123 — is **merged green** on synthetic
fixtures, and **WO-124 has reported its numbers** (done, 2026-07-28). WO-120
gates closeout under Amendment 4; **WO-118b gates closeout under Amendment 5
and is unheld by Amendment 6.** Closeout updates `handoff.md` and writes
ADP-003 — whose content depends on what WO-124 found. Amendment 7 supersedes
the deletion-at-closeout instruction: the spike survives only through WO-127,
which reruns it foregrounded and deletes it after recording the result.
If WO-124 shows the Monitor cannot be made good enough to judge an edit on,
**`SPEC.md` §6 and the v3z design change before ADP-003 is written**, which is
the entire reason the spike runs first.
