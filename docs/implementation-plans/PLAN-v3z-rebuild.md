# Plan — building KwikReel on the v3z frontend

**Status: LARGELY DISCHARGED. Still not an authorization.**
Drafted 2026-07-28. It names the decisions, specs, ADPs and Work Orders required
to take the product from what exists today to what
`docs/design-claude/mockup-v3z.html` draws. (That folder is gitignored and local
only — the mockups are not in the public repo.)

**Progress, 2026-07-29.** All of §5's serial steps are done — the **clean cut**,
the **decision session** ([`DECISIONS.md`](../DECISIONS.md)), **`SPEC.md`
accepted** (discharging S-1 and — within it — S-4, S-5, S-6, S-9 and S-10),
**ADP-002 signed**, and **WO-117 merged**. WO-116 and WO-124 both landed; the
backend lanes are fanning out under ADP-002.

**What this plan still holds that `SPEC.md` does not:** the ADP-003/ADP-004
sequencing in §3 – §5. The four spec gaps it once held open — S-2 (SO-3), S-3
(SO-1), S-7's open half (SO-2) and S-8 (SO-4) — all closed by 2026-07-29. Where
this plan and `SPEC.md` disagree, **`SPEC.md` wins** — it is normative and this
is a plan. §1's ADR framing is superseded by `DECISIONS.md`, which recorded the
same eight departures in one session and **reversed A-3**: `disposition` is
kept, not retired.

**The live authorization is [ADP-002](ADP-002-contract-v2-and-backend.md)** —
authorized 2026-07-28, amended through 2026-07-30. Amendment 5 makes test
ownership explicit, serializes renderer → QA, and adds held WO-118b for the
unresolved reject semantics.

**One naming note that matters:** the new normative document is **`SPEC.md`**,
written *forward from v3z*. It is not an amendment to the archived ES-001, and
must not be produced by editing it — amending inherits the ghosts the clean cut
just removed. Section references to ES-001 below are there to say what the new
document must *cover*, not what it should be derived from.

---

## 0 · What this plan is reconciling

Two things are true at once and they do not agree.

**What exists (2026-07-24):** M1 is functionally complete on synthetic fixtures.
Backend lanes WO-102–106, 111, 112 and frontend WO-107–110 all pass; 67 tests
green. That product has **five approval gates**, a **nine-stage pipeline**, a
`disposition` on every proposal, three mutually-exclusive **audio modes**, and
**no speed**.

**What v3z draws (2026-07-28):** four controls (Sources · Trim · Speed · Save),
**one view in six states**, **no gates at all**, **speed in M1**, audio as **two
level sliders**, no `disposition`, no rename, no displayed reasons, and a **Log**
unit as the only warning surface.

v3z is not a reskin of the built product. It is a different product with a large
shared backend. The plan below is sized accordingly: roughly the same magnitude
as the original M1, with most of the *backend* surviving under amendment and the
*frontend* being a rewrite.

### What survives, what changes, what goes

| Area | Verdict |
|---|---|
| `backend/ingest/`, `backend/analysis/` | **Survives.** One correctness fix (letterbox, below) and the WO-115a performance work |
| `backend/propose/trim_proposer.py` | **Survives**, minus the 1.0 s floor (D-11); gains a sibling speed proposer |
| `backend/store/`, `backend/contracts/` | **Amended heavily** — schema v2 |
| `backend/render/`, `backend/qa/` | **Amended heavily** — mix levels, speed, configurable resolution |
| `backend/api/` | **Amended heavily** — gates removed, PATCH surface added |
| `frontend/src/**` (~1,000 LOC) | **Rewritten.** `contracts.ts` regenerates; `liveClient.ts` is a starting point. `App.tsx`, `Curation.tsx`, `Timeline.tsx`, `TrimReview.tsx`, `ui.tsx` are superseded by the rack |
| Approval gates, `stage_approvals`, `disposition`, `included`, `AudioMode`, clip rename | **Deleted from the product** |

**The mockup contains no behaviour.** v3z is script-free — six independently
baked static renders. There is no interaction logic to port. Every behaviour in
the plan below is built from zero against a design that has only ever been
looked at, never operated.

---

## 1 · Decisions that must land first (ADR work)

Three of these are **stop-and-ask** items under `CLAUDE.md`: v3z violates hard
constraints that are locked by accepted ADRs and may not be relaxed by an
agent's judgment. Nothing downstream is legitimate until they are decided by the
owner.

| # | ADR action | What it decides | Why it blocks |
|---|---|---|---|
| **A-1** | **New ADR-014 · Retiring the approval gates** (supersedes ADR-006 in part) | v3t/v3z remove all five gates and the nine-stage progression. `stage_approvals`, G-6, G-8 and OPEN-01 all become moot | `CLAUDE.md`: *"No assist may act without user approval… nothing advances a stage without the user's explicit approval."* This is the single largest departure in the whole plan. It also **closes OPEN-01 by deletion** — the item currently recorded as blocking implementation |
| **A-2** | **Amend ADR-006 · reasons recorded, not displayed** (D-01) | `ReasonRecord` keeps being produced and stored; nothing renders it | `CLAUDE.md`: *"A stage that cannot explain its proposals is not complete."* Also settles **N-9** — confirm that a record produced, stored and read by nothing is still worth producing |
| **A-3** | **Retire ADR-010 · `disposition`** (O-19) | `origin` alone records whose a value is; kept-vs-discarded is no longer a stored field | `CLAUDE.md` names `disposition` as a hard constraint. Retiring it thins the "assists earn their place" evidence to a countable-but-weaker form |
| **A-4** | **New ADR-015 · The audio model** (D-02) | Two 0–100 % levels replace `music`/`clip`/`silent` modes; one export file; per-clip mute retained; ducking still out | Retires G-5 and `Export.audio_modes`; changes the renderer and QA |
| **A-5** | **New ADR-016 · Speed in M1** (amends ADR-007, restructures ROADMAP) | Speed ramping moves from M3 into M1; M2's selection/order assist is **cancelled** (O-12) | ROADMAP's three milestones no longer describe the product. Milestone restructure is an owner call |
| **A-6** | **New ADR-017 · Retiring the 1.0 s floor** (D-11) | No minimum window for user or machine; sub-second and empty results are **warned, never blocked** | With A-2, this permits a clip to vanish from the reel with no on-screen explanation. The Log unit is the mitigation and is therefore load-bearing, not decorative |
| **A-7** | **Amend ADR-002 · the read-only affordance** (N-8) | v3t removed `[ORIGINALS] READ ONLY` from the HUD. Nothing on screen now says originals are never modified | The privacy posture is unchanged in code; the *user-visible assurance* was deleted. Decide whether that is acceptable or whether the Log/footer carries it |
| **A-8** | **New ADR-018 · Locking the v3z baseline** (or an ADR-008 amendment) | Declares v3z the frozen design, ends the mockup series, and states that contract v2 is cut from it | ADR-008's rule is prototype-before-contract-freeze. v3a→v3z *is* that prototype. This is the moment it closes |

**Owner questions to close alongside the ADRs** (from `v3t-brief.md` §4, none
decided):

- **N-4** — reel longer than the music track: loop, or run silent past its end?
- **N-6** — `atempo` is clean roughly 0.5×–2×. Does the speed assist clamp there?
- **N-7** — the HUD is down to two items. Keep the row, or move them onto the rack?
- **N-10** — speed's reversibility needs the same retained-proposal machinery as
  trim, which makes `SpeedProposal` **live in M1**.

---

## 2 · Engineering specs to iron out before work starts

This is the section that decides whether the build goes smoothly or churns.
Items **S-1**, **S-2** and **S-5** are the ones where the existing documents
have nothing to say at all.

### S-1 · `SPEC.md` — the product and the frozen contract v2

**Everything else codes against this. It lands alone and first.**

A **new document**, not a fifth amendment to ES-001: the removals (gates,
disposition, included, audio modes, rename) are large enough that an amended
ES-001 would be more strikethrough than text.

Transcribe the contract from **v3z's own generator**, which already carries a
working state model — `trimOf()` is the toggle-stickiness rule, `played()` is the
speed duration math, `ml`/`cl` are the two mix levels. That collapses most of
S-3 and all of S-6 into transcription rather than derivation.

| Change | Driver |
|---|---|
| `stage_approvals` removed from `Project` | A-1 |
| `disposition` removed from every proposal | A-3 |
| `Clip.included` removed — no writer exists once M2 selection is cancelled | O-12/O-18 |
| `Clip.name` **not** added — D-07 reversed, clips are always their file's base name | O-26 |
| `Clip` gains a **stashed segment list** so Remove is genuinely reversible | N-11 |
| `AudioMix` on `Project`: `music_level`, `clip_level` (0.0–1.0). Lit is derived from `> 0`, no booleans | D-02 |
| `Clip.audio.retain` becomes live, **default `True`** | D-02 |
| `AudioMode`, `Export.audio_modes` retired; `Export.last_render` collapses to one `RenderRecord` | D-02 |
| `Project.music` becomes optional (track can be chosen before a project exists) | D-05 |
| `Music` gains an **in-point** | O-22/O-23 |
| `Project` gains **output resolution**: 720×1280 / 1080×1920 / 2160×3840, all 9:16 | O-29/N-2 |
| `SpeedProposal` becomes live; **multiple `SpeedRange`s inside one clip** | O-5/N-10 |
| `IncludedProposal`, `OrderProposal` dropped | O-12 |
| G-5 and G-9 retired | D-02, D-11 |
| No peaks field on `Music` — computed on demand | D-06 |

### S-2 · The playback engine spec — **the highest-risk item in the plan**

D-14 says the Monitor sequences **proxies client-side**, seeking each to its
in/out. v3z adds speed on top, and the Sound unit adds a **music bed mixed
against per-clip audio at two independent levels, on the reel's own time base,
with a cursor tracking the Monitor**. No existing document specifies any of it.

Must resolve, before any Monitor code:

- Clip-to-clip transition: one `<video>` with reload-and-seek, or two elements
  cross-swapped? What gap is acceptable at a cut, and is it measured?
- Seek accuracy against proxy keyframe interval — a 1.5 Mbps 540×960 H.264 proxy
  built with default GOP may not seek to an arbitrary in-point cleanly.
- Speed preview: `HTMLMediaElement.playbackRate` vs. the rendered `setpts`
  result. Rate is capped and pitch-shifts audio unless
  `preservesPitch` is set — the preview and the export must not disagree about
  what the user is approving.
- Music sync: WebAudio for the bed, or a second `<audio>` element? How does the
  bed stay aligned across a clip transition and a seek?
- The two level sliders drive both **the mix** and **the trace brightness** — so
  the display *is* the mix, and preview loudness must match export loudness.

**Recommendation: prove this with a throwaway spike before authorizing the
frontend ADP** (WO-124 below). It is the one thing that could invalidate the
v3z design after eight Work Orders have been built against it — exactly the
failure ADR-008 exists to prevent.

### S-3 · The speed assist spec *(a `SPEC.md` section)*

O-5 gives the rule in one line — *ramp low `motion_energy` + low `audio_rms`
stretches to 1.5–2×* — which is not enough to implement deterministically.
Needs: thresholds and how they are derived, minimum ramp length, how adjacent
ranges merge, whether rate is continuous or stepped, the **N-6 clamp**,
interaction with the trim range, and how "explainable" is satisfied when nothing
is displayed (A-2).

### S-4 · The audio spec

Levels → `amix` weights. `atempo` chained per speed range with pitch preserved
(O-6) — **this reopens ES-001 §8.2**, which kept natural audio specifically on
the argument that M1 had no speed ramps. Plus per-clip mute, the both-at-zero
case (output must be silent **and** still carry a valid AAC track), and **N-4**.

### S-5 · Persistence and concurrency — **new, and now load-bearing**

With the gates gone there is no explicit "approve" moment, so **every
interaction is a live mutation**. This was previously carried by a gate; now it
is carried by nothing.

Needs: the PATCH surface (D-08), when writes fire, debounce policy, optimistic
UI and what the user sees on a **409** (WO-115b's **D-3**, still undecided),
what undo means with no gate to fall back to, and the failure path — *a silent
background save failure is worse than the 409*.

### S-6 · Toggle stickiness and reversibility

The Trim and Speed toggles apply to **every clip at once** and revert when
switched off, but **skip any clip the user edited** (O-7). Specify: how "the
user edited this clip" is determined (recommend deriving from `origin: "user"`
rather than adding a flag), what *off* reverts to in each of the four
combinations, the **N-11 stash** semantics for Remove, and **N-10** speed
reversibility.

### S-7 · The Log spec — the only warning surface

A-2 removes displayed reasons and A-6 lets the proposer return an empty segment.
Together they permit **a clip to disappear from the reel with no explanation
anywhere on screen**. The Log is the mitigation. Specify: the event vocabulary,
severity, ordering, retention (three visible lines — how deep does it scroll?),
whether it persists into `project.json` or is session-only, and — specifically —
the D-11 warnings for sub-second and empty results.

### S-8 · The rack layout invariant

v3z's stated achievement is that **no element differs in size between any two of
the six states**, at a fixed 767px. That was measured against six hand-built
states with fixed fake data. Real data breaks it. Specify: minimum viewport and
what happens below it, behaviour for long clip names and long track names
(truncate where?), the Clip index at 200 clips (4-row window + scroll keys is
already the answer — confirm scroll performance and whether a position indicator
is needed), and whether the invariant is **enforced by a test** or is a design
aspiration.

### S-9 · Link / relink

v3z puts **link on every row**, not just damaged ones — repointing a *valid*
clip at a different file is new behaviour. Specify what survives the repoint
(trim, order, speed, mute do; what about the stash?), the content-hash repair
path (D-09), and the three out-of-reel row states — **trimmed out · unlinked ·
damaged** — which are fixed in three completely different ways.

### S-10 · Validation gates v2 *(replaces ES-001 §10)*

The current acceptance test exercises delete/restore and the approval gates,
neither of which exists any more. Rewrite the exit gates for the new product,
including speed, the mix, and the Log warnings.

### Also to amend

`ROADMAP.md` (milestone restructure — A-5) · `PROJECT.md` · `handoff.md` ·
`CLAUDE.md`'s hard-constraints list (gates, disposition, reason display) ·
`docs/specs/EVIDENCE-LEDGER.md` — **claim C-03 ("the trim heuristic is a helpful
starting point") is currently resting on a proposer that mislabels an entire
orientation**, per the letterbox finding below.

---

## 3 · ADPs to create

| ADP | Grants | Gated on | State |
|---|---|---|---|
| **[ADP-002](ADP-002-contract-v2-and-backend.md) · Contract v2 and backend realignment** | WO-116a, WO-117 – WO-124, all unheld; WO-118b held. Local build only; pushes, CI and real-media runs stay separately gated, as ADP-001 §3 | `DECISIONS.md` and `SPEC.md`, both landed. WO-118b remains held on the reject-semantics decision; no other WO waits on it | **Authorized 2026-07-28, amended ×5** |
| **ADP-003 · The v3z rack frontend** | WO-125 – WO-132 | **WO-124's spike passing**, plus SO-2 and SO-4 | Not written — its content depends on WO-124's numbers |
| **ADP-004 · Verification and real-footage validation** | WO-133 – WO-135, and WO-115a/115b | ADP-002 + ADP-003 complete; **a recorded ADR-002 consent** for anything touching real footage | Not written |

WO-124 (the spike) sits between ADP-002 and ADP-003 and should be authorized
**inside ADP-002** as its last item, so its result is in hand before the frontend
ADP is written.

---

## 4 · Work Orders to create

Numbering continues from the drafted WO-115a/115b. The directory-ownership
discipline from `m1-backlog.md` is what makes the lanes safe. Amendment 5 makes
that discipline executable: each Work Order owns named production **and test**
paths, and any shared resource makes the WOs one serial lane. Dependency
manifests remain owned by the contract WO alone.

### Runs first, alone — and jumps the queue

| WO | Scope | Notes |
|---|---|---|
| **WO-116 · Letterbox / exposure correctness fix** | Analysis reads the *padded* proxy, so **every landscape clip fails the keep test on every second** and is reported `OVEREXPOSED`. Analyze unpadded content | This is WO-115b's **D-1**, and it should precede everything. Optimizing or rebuilding on top of a proposer that computes a wrong number is the wrong order of work. It changes trim proposals on landscape footage, so it is an **owner decision**, not an agent's. It also moves ledger claim **C-03** |
| **WO-117 · Contract kernel v2** | ES-002 §4 frozen as code: Pydantic models + regenerated TS types + updated service Protocols. Owns `backend/contracts/`, `frontend/src/types/`, `pyproject.toml`, `package.json` | Runs **alone**. Everything else codes against it, exactly as WO-101 did |

### Backend lanes — parallel after WO-117

| WO | Scope | Owns |
|---|---|---|
| **WO-118 · Store v2** | Remove `stage_approvals`, `disposition`, `included`. Add the segment stash, the audio mix, the resolution setting, the music in-point. Origin-based "user edited this" derivation (S-6). Invariants retested | `backend/store/` |
| **WO-118b · Reject semantics correction — held** | Implement the owner-selected resolution of the §3.1/§4.3 contradiction and the missing `dismissed` writer. Gates ADP-002 closeout; no other WO waits on it | Named store implementation and test files in ADP-002 §4 |
| **WO-119 · Media services** | Thumbnails and peaks on demand + cached (D-06); music probe and peaks keyed by **content hash** so they work with no project in existence (D-05); `POST /api/pick-file` via `osascript … choose file`, serving both track selection and relink | `backend/media/`; `tests/media/` |
| **WO-120 · Speed proposer** | S-3's rules as code. Multiple `SpeedRange`s per clip, the N-6 clamp, retained proposals for reversibility (N-10) | Named proposer implementation/export files; `tests/propose/test_speed_proposer.py` |
| **WO-121 · Renderer v2** | `amix` weighted by the two levels, replacing the three non-composable mode branches. `setpts` + chained `atempo` per speed range. Skip `out_s <= in_s` (D-12). Configurable resolution — `TARGET_W`/`TARGET_H` stop being constants. **Upscaling past the source is refused or flagged, never silent.** Fail with a stated reason when every clip is zero-length rather than handing ffmpeg an empty concat | `backend/render/`; `tests/render/` |
| **WO-122 · QA v2** | `resolution_ok` checks against the *setting*, not a hardcoded 1080×1920. `audio_ok` re-derived from the levels: `music_level > 0` means not silent; both at 0 means silent **and** still a valid AAC track. **Runs after WO-121 in the same lane** | `backend/qa/`; `tests/qa/`; retirement/split of the mixed legacy renderer/QA test file |
| **WO-123 · API v2** | Delete `approve/{stage}` and every gate read. Add the narrow PATCH routes (D-08), relink, download without `audio_mode`, thumb/peaks/pick-file. **Each new mutating route needs its own ADR-011 capability-token guard test — that is the real cost of D-08 over a client write queue** | `backend/api/`; named API/security tests and `tests/support.py` |

### The spike — gates ADP-003

| WO | Scope |
|---|---|
| **WO-124 · Playback engine spike** | **Throwaway code, deleted afterwards.** Answers S-2 with a measurement, not an opinion: can a browser sequence proxies through in/out points, apply variable rate, and hold a music bed in sync, smoothly enough that the Monitor is the thing the user judges the edit on? Records the transition gap, the seek error, and whether preview loudness matches export. **If it fails, the design changes before eight frontend Work Orders are built on it** |

### Frontend lanes — parallel after WO-125

| WO | Scope | Owns |
|---|---|---|
| **WO-125 · Rack design system** | Extract v3z's CSS into a real stylesheet and component primitives — module/ears/screws, keys, LEDs, seven-segment, VFD and LCD glass, labelled housings, the CSS-drawn glyph set, the embedded fonts. Encodes S-8's invariants. **Runs first in this group; every other frontend WO consumes it** | `frontend/src/rack/` |
| **WO-126 · App shell, state model, client v2** | The six states as **one live view**. PATCH mutation queue, optimistic UI, the 409 path (S-5). Mock and live clients | `frontend/src/app/` |
| **WO-127 · Monitor and Transport** | Queue playback from the spike's proven approach; clip-scoped scrub; target length; the three-way resolution selector; Loop; the resolution box top-right | `frontend/src/monitor/` |
| **WO-128 · Sound** | The reel timeline — music in green above the centre line, every reel clip's audio in orange below, on the reel's own axis, windowed to the stretch that plays. Two vertical 0–100 % sliders driving both mix and brightness. Cursor, playing-clip wash, drag-to-set music in-point, track picker on the glass | `frontend/src/sound/` |
| **WO-129 · Clip index** | Four-row window, scroll keys that move *which four clips the keys address*. Seven keys per row: play-next LED · edit · reorder ▲▼ · speaker · **link** · **bin**. The three out-of-reel states rendered as v3z specifies — bin lit green when trimmed out, chain ringed yellow when unlinked, neither when damaged. **Nothing greys out and nothing disappears** | `frontend/src/index/` |
| **WO-130 · Editor** | In, out and rate — everything that acts on *time*. Trim bar with crossable handles; the speed lane in a **fixed-width well** whose light changes, not its size; the AI housing (✕ reject, ↻ re-run) acting on the **trim proposal only** (a known limit, N-12); the dark empty state | `frontend/src/editor/` |
| **WO-131 · Log** | S-7 as code. Three lines of glass, scroll keys pinned to its ends. Carries the D-11 warnings, which is the whole reason it exists | `frontend/src/log/` |
| **WO-132 · Reel row and HUD** | Sources · Trim · Speed … Length · reel name · Save. In-place rename on the glass. Sources re-pick confirmation (D-10) — **the first modal pattern in the rig**. LOCAL + nameplate, per N-7 | `frontend/src/reel/` |

### Verification

| WO | Scope |
|---|---|
| **WO-133 · Guards and build gates v2** | ADR-011 token guards on every new mutating route, each proven to fail when violated. Origin guard, path scrubbing, the fixtures guard. **Plus `SPEC.md` §10.1's three cause-tests** — four key rows at any clip count, names within their character budget, fixed-width counters. **The browser-driving stop-and-ask is withdrawn:** SO-4 closed by testing the invariant's causes rather than its rendered geometry, so no new dependency is needed |
| **WO-134 · Integration verification v2** | S-10's rewritten exit gates, end to end through the API on synthetic fixtures |
| **WO-135 · Real-footage validation** | **Owner-gated on a recorded ADR-002 consent.** The real ~50-clip-day run, the Apple Photos Memory comparison, and WO-115b's **CP-3** perf spike — the only work that can move ledger claim **C-05** off `assumed`. Absorbs **WO-115a** (ingest performance) and the rest of **WO-115b** |

**Total: 21 Work Orders**, of which 8 are frontend. That is roughly the size of
the original M1 backlog, which is the honest reading of what "build it as v3z
draws it" costs.

---

## 5 · Sequence

Only four steps are serial before the work fans out.

0. ~~**The clean cut.**~~ **Done 2026-07-28.**
1. ~~**One decision session.**~~ **Done 2026-07-28** —
   [`DECISIONS.md`](../DECISIONS.md), signed once.
2. ~~**`SPEC.md`**, per S-1.~~ **Accepted 2026-07-28**, with four items owed
   (§14). The only document that gates code.
3. ~~**Sign [ADP-002](ADP-002-contract-v2-and-backend.md).**~~ **Done
   2026-07-28.** *(Added: the plan originally ran straight from the spec to the
   contract kernel, which skipped the authorization. Nothing may be built
   without it.)*
4. ~~**WO-117 contract kernel, alone.**~~ **Done 2026-07-28.** Everything is
   fanning out — this is where the build is now.

**Two things run in parallel with all of the above**, because neither depends on
any v3z decision:

- ~~**WO-116, the letterbox fix.**~~ **Done** — `3d0d0d6`, two regression tests.
- ~~**WO-124, the playback-engine spike.**~~ **Done 2026-07-28** — findings in
  [`WO-124-playback-findings.md`](../specs/WO-124-playback-findings.md). SO-3
  closed, the v3z design survived its own measurement, and the one defect it
  surfaced (silent proxies) was fixed the same day as WO-116a.

Then: **ADP-002** (independent media, speed and API lanes; serial renderer → QA
lane; held WO-118b before closeout) → read the spike's numbers → **ADP-003**
(WO-125 alone, then seven frontend lanes in parallel) → **ADP-004** (guards,
integration, and — behind a consent record — real footage).

---

## 6 · Risks recorded honestly, not argued around

- **The design has never been operated.** v3z is six static renders. Everything
  that feels right in a screenshot — the four-row window at 200 clips, scroll
  keys instead of a scrollbar, seven 26px keys on every row, no greying and no
  disappearing — is untested as *interaction*. Some of it will not survive
  contact and the plan should expect a v4 pass after WO-126 makes it live.
- **A clip can vanish silently.** A-2 takes reasons off the screen, A-6 lets the
  proposer return nothing. The Log (S-7, WO-131) is the *only* thing standing
  between that combination and a silent surprise. Treat it as a correctness
  requirement, not a nicety.
- **Removing the gates removes the review moment.** ADR-006's staged approval was
  also the product's answer to *"the AI proposes, the human decides."* With the
  gates gone, that promise now rests entirely on the toggles being reversible and
  on user edits being sticky (S-6). If stickiness is buggy, the machine silently
  overwrites human work — the exact failure the gates were built to prevent.
- **Speed in M1 reopens settled ground.** `atempo` contradicts ES-001 §8.2's
  reasoning, which assumed no ramps. Chained `atempo` beyond ~2× audibly
  degrades; N-6 is not a detail.
- **C-03 is currently unsupported.** The letterbox bug means the trim proposer
  mislabels every landscape clip, and no test catches it because the assertion
  only checks that *a* reason exists, never that it is *right*. **A confidently
  wrong `OVEREXPOSED` passes every gate in the suite today.** WO-116 first.
- **Every claim in the evidence ledger is still `assumed`.** No experiment has
  run. Owner approval of the v3z design is a build gate, not evidence the
  product is good.
