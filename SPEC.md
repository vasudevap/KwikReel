# SPEC — KwikReel

**Status: ACCEPTED — owner, 2026-07-28. Normative.** The single product and
contract document, outranked only by [CONSTRAINTS.md](docs/CONSTRAINTS.md).
**Acceptance is not authorization to build.** Implementation is gated on an ADP,
and the four things it did not settle at acceptance are listed — **all now
closed** — in [§14](#14--what-this-spec-still-owes).
**Amended 2026-07-30:** DECISIONS §5 adds the narrow server-owned HTTP actions
the frozen frontend needs to operate §4.3, §7 and §8.3; `project.json`, the
design and the guardrails are unchanged.
Written 2026-07-28, forward from `docs/design-claude/mockup-v3z.html` and
[DECISIONS.md](docs/DECISIONS.md).

> **The mockup is not in this repository.** `docs/design-claude/` is gitignored
> by decision — the repo is public and the mockups are the product's look and
> feel. Paths to it resolve on the owner's machine only. This spec is written to
> stand on its own without it.

This is the single product and contract document. Where it disagrees with
anything in `docs/archive/`, this wins and the archived document is not to be
cited. Guardrails are in [CONSTRAINTS.md](docs/CONSTRAINTS.md) and are **not
restated here** — they bind this spec without being repeated in it.

---

## 1 · Scope

A local web app on a Mac that turns a folder of family video into a short
vertical reel. It reads the footage, proposes where to trim and where to speed
up, and the person editing accepts, adjusts or ignores any of it.

**One release.** There is no staged roadmap (DECISIONS A-5c).

**In scope:** import a folder · read each clip · propose trims · propose speed
ramps · manual trim, speed, order, mute and removal · a two-level audio mix over
a user-supplied track · preview · render and export one file.

**Explicitly excluded:** choosing *which* clips belong in the reel (A-5b) ·
approval gates (A-1) · clip rename · multi-folder projects · cutting one clip
into several kept pieces · ducking · beat detection · NLE export · any form of
publishing.

---

## 2 · The product

### 2.1 · The rig

One screen. A Monitor down the left running the full height, and a stack of
units on the right: **Reel · HUD · Transport · Sound · Editor · Clip index ·
Log**. Nothing spans both columns and **no element changes size between states**.

The design is v3z (`docs/design-claude/`, local only), which is locked (A-8). Its
rules — one key size, nothing greys out, state is a lamp and never a repainted
control, every counter the same yellow — are design law, not suggestions, and
`SPEC.md` does not restate them.

### 2.2 · Four controls

**Sources · Trim · Speed · Save.**

- **Sources** picks a folder and creates the project. A second pick replaces the
  root and restarts the reel, behind an explicit confirmation.
- **Trim** and **Speed** are assist toggles. They apply to every clip at once and
  revert when switched off — **except on clips edited by hand, which they never
  touch** (§5.4).
- **Save** renders and exports. There is nothing between it and the file.

### 2.3 · The six states

`empty` · `loaded` · `trim on` · `trim off` · `speed on` · `playing`. These are
states of one view, not screens. `trim off` exists specifically to show that
reverting an assist leaves hand-edited clips alone.

### 2.4 · What each unit owns

| Unit | Owns |
|---|---|
| **Reel** | Sources, Trim, Speed, reel length, the reel name (edited in place), Save |
| **HUD** | `LOCAL` and the nameplate. One row (N-7) |
| **Monitor** | Plays the queue. Shows the playing clip's resolution top-right |
| **Transport** | Play/pause, previous/next clip, frame step, Loop, target length, output resolution, clip-scoped scrub with in/out and current-time readouts |
| **Sound** | Two 0–100 loudness sliders (Music, Clip), the reel timeline, track selection |
| **Editor** | The loaded clip's **time only** — in, out, rate — plus the two proposal keys (reject ✕, re-run ↻) in a housing captioned AI |
| **Clip index** | A four-row window over the clip list. Per row: play-next LED · edit · reorder ▲▼ · mute · **link** · **bin** |
| **Log** | The audit trail (§7) |

**Where a key lives says what it acts on.** Link and bin are row keys because
*is this clip in the reel* and *does it still have a file* are questions asked of
every clip. The Editor keeps only what acts on time.

---

## 3 · The frozen contract

Canonical state is a versioned `project.json` that round-trips losslessly.
Sidecar `analysis.json` per source holds facts, and sidecar `log.json` per
project holds the audit trail (§7.3) — history, deliberately kept out of the
state document. All are local; none is ever committed.

### 3.1 · The central structural rule — effective values are derived

**The assists do not mutate clips. The toggles are a live derivation.**

This is transcribed directly from the v3z generator's own state model and is the
most important structural decision in this document:

```
effective_trim(clip):
    if clip.origin.segments == "user":  return clip.segment      # yours always wins
    if project.trim_assist_on and clip.proposals.segments and
       clip.proposals.segments.disposition != "dismissed":
                                        return the proposal's value
    return whole clip                                            # 0 .. duration_s

effective_speed(clip):
    if clip.origin.speed == "user":     return clip.speed_ranges
    if project.speed_assist_on and clip.proposals.speed:
                                        return the proposal's value
    return []                                                    # 1.0× throughout
```

Three consequences, all of them wanted:

1. **Reverting an assist is free and lossless** — nothing was overwritten, so
   there is nothing to restore. This is why proposals are retained.
2. **Stickiness is structural, not procedural.** A hand edit sets
   `origin.* = "user"`, and from that moment no assist can reach the field. The
   toggle cannot skip a clip incorrectly because it never had the chance to
   touch it.
3. **`clip.segment` and `clip.speed_ranges` hold the *user's* value and are null
   unless `origin` says `"user"`.** They are not "what renders" — what renders is
   derived at render time by the rules above.

### 3.2 · `project.json`

```
Project
  schema_version: 2
  project_id, created_at, updated_at, app_version
  name: str | null                  # display; basename(media_root) when unset
  media_root: str                   # absolute, read-only, one folder per project
  target_duration_s: float          # a reference shown to the user; nothing optimises toward it
  output_resolution: "720p" | "1080p" | "4k"      # 720×1280 · 1080×1920 · 2160×3840, all 9:16
  trim_assist_on: bool = false
  speed_assist_on: bool = false
  audio: AudioMix
  music: Music | null               # a track may be chosen before a project exists
  sources: [SourceIndex]
  clips: [Clip]
  export: Export

AudioMix
  music_level: float                # 0.0–1.0; the UI's 0–100 divided by 100
  clip_level:  float                # lit is derived from > 0. No on/off booleans

Music
  track_ref: str                    # absolute path to a user-supplied local track
  content_hash: str
  duration_s: float
  in_s: float = 0.0                 # where in the track the reel starts

Clip
  source_id: str
  order: int                        # dense, unique
  segment: Segment | null           # the USER's trim; null unless origin.segments == "user"
  speed_ranges: [SpeedRange]        # the USER's ramps; empty unless origin.speed == "user"
  stashed_segment: Segment | null   # what bin/restore returns to (§4.3)
  audio: { retain: bool = true, gain_db: float = 0.0 }
  origin: Origin
  proposals: Proposals

Segment
  in_s: float
  out_s: float                      # out_s <= in_s means "not in the reel" (§3.4)

SpeedRange
  from_s: float                     # SOURCE time, seconds from clip start
  to_s: float
  rate: float                       # > 0. No cap (DECISIONS N-6)

Origin                              # "default" | "proposed" | "user", per field
  order, segments, speed, audio

Proposals                           # retained after override — they make revert possible
  segments: SegmentsProposal | null
  speed:    SpeedProposal | null

SegmentsProposal / SpeedProposal
  value, at, reasons: [ReasonRecord], disposition

ReasonRecord
  code, human_text, evidence_refs: [str], score, confidence

Export
  last_render: RenderRecord | null  # one file, not one per mode
```

**Speed ranges are stored in source time and clipped to the kept region at
render.** A ramp describes a stretch of *content* — the dull bit in the middle —
so moving a trim handle must not slide the ramp off the thing it was computed
for.

**Exactly one segment per clip.** The Editor has one trim bar. Cutting a clip
into several kept pieces is deferred (§12).

### 3.3 · `SourceIndex` and `analysis.json`

Unchanged from what is built: `SourceIndex` carries the immutable facts
(`source_id`, `content_hash`, `path`, `duration_s`, `captured_at`,
`orientation`, `codec`, `fps`, `width`, `height`, `has_audio`, `has_gps`,
`readable`, `proxy_path`) and `Analysis` carries per-second `Signals` — `blur`,
`exposure`, `shake`, `motion_energy`, `audio_rms` — plus `scene_cuts_s`.

`has_gps` is a presence flag; coordinates are never stored. `people_count` stays
declared and unused, and if it ever arrives it is a **count only**.

### 3.4 · Derived state — never stored

| Derived | Rule |
|---|---|
| **In the reel** | A clip is in the reel unless it is *trimmed out* (`out_s <= in_s`), *unlinked* (its file cannot be found) or *damaged* (`readable: false`) |
| **Why it is out** | Those same three, in that precedence. The index shows each in its own colour — amber, yellow, red — because they are fixed three completely different ways |
| **Played duration** | Over the kept region: `Σ (overlap with a ramp) / rate + (kept time under no ramp)` |
| **Reel length** | The sum of played duration over in-reel clips, in `order` |
| **Resume point** | The project reopens as it was. There is no stage and no resume concept |

There is no `included` field, no `deleted` field, and no `stage_approvals`.
**Removal is trimming to nothing**, which is why it needs no state of its own and
why dragging a handle back revives the clip for free.

### 3.5 · The preview queue is not reel membership

The round LED on each row is a **multi-select preview queue** — the lit set, in
order, is what the Monitor plays. It does not affect the reel, the reel length,
or the export, and **it is not persisted**.

> **Recorded as a design risk, not argued away.** One row carries both a lamp
> meaning *preview this* and a bin meaning *remove this from the reel*. Those
> read as neighbours and are not. This is a strong candidate for the correction
> pass A-8 anticipates.

---

## 4 · The assists

Both are deterministic and legible. Neither aims at the target length — the
target is a reference the user reads, not an objective anything optimises toward.

### 4.1 · Trim

Per-second signals are normalised 0..1. A second is **good** when
`blur >= 0.35` **and** `exposure <= 0.50` **and** `shake <= 0.50`. A second is
**static** when `motion_energy <= 0.10` **and** `audio_rms <= 0.10`.

1. Take the **longest contiguous run of good seconds that does not cross a scene
   cut**.
2. Trim static lead-in and static tail from that run. If that would consume it
   entirely, keep the run.
3. If **no** second clears the floors, keep the whole clip and say so
   (`NO_CLEAR_WINDOW`).
4. **There is no minimum window** (A-6). A proposal may be shorter than a second,
   and may be empty — which removes the clip from the reel. Both are warned in
   the Log (§7). Neither is blocked.

Every trimmed span emits one `ReasonRecord` citing the signal range that drove
it: `LEADING_BLUR`, `TRAILING_SHAKE`, `LEADING_STATIC`, `WHOLE_CLIP_GOOD`, and
so on. Thresholds are configuration, not constants.

> **Known naming defect, carried deliberately.** The exposure signal counts *both*
> crushed blacks and blown highlights, but its reason code is `OVEREXPOSED` and
> its wording is "badly exposed" — so a very dark clip is reported as
> overexposed. Correcting it changes user-visible text and is a product decision
> that has not been taken.

### 4.2 · Speed

**Rule: ramp the dull stretches.** A second is **dull** when `motion_energy <=
0.25` **and** `audio_rms <= 0.25` — both already 0..1 normalized, per §4.1's
static-second convention, with dull set above the static band so it doesn't
just re-flag content §4.1 already trims. Dullness score
`d = 1 - max(motion_energy, audio_rms) / 0.25`, clamped to `[0, 1]`.

Contiguous dull seconds form a candidate range. Two candidate ranges separated
by a gap **< 0.5 s** of non-dull seconds merge into one. A merged or single
range becomes a `SpeedRange` only if its duration is **>= 1.5 s** — a shorter
candidate is dropped (no ramp, stays 1.0×). **One clip may carry several
ranges.**

Rate is continuous, not stepped: `rate = 1.5 + 0.5 * d`, using the range's mean
dullness score, giving **1.5×–2.0×**. Everything not in a range stays 1.0×.

The assist never proposes above 2.0×. **Hand-set rates are uncapped** (N-6).

> **SO-1 closed** — owner, 2026-07-28, via ADP-002 Amendment 2. This paragraph
> is the resolution; see [§14](#14--what-this-spec-still-owes).

> **Accepted cost, recorded.** Clip audio is time-stretched with pitch preserved.
> The filter is clean to roughly 2×; beyond that it must be chained and degrades
> audibly. Uncapped manual rates can therefore produce audio the user will not
> like. The Log warns whenever any clip renders at a rate other than 1.0×.

### 4.3 · The controls that act on a proposal

- **Reject (✕)** retains this clip's proposal for the audit trail and writes
  `disposition: "dismissed"`. The derivation skips it, so the clip reverts to
  whole (or to the user's own trim, if there is one).
- **Re-run (↻)** asks for a fresh proposal for this clip alone.
- **Bin** sets the effective trim to zero length, **stashing the previous
  effective value first**. Pressing it again restores the stash. This is the only
  reason `stashed_segment` exists, and it is what makes removal genuinely
  non-destructive.

**Reject and Bin are server-owned actions.** The client does not patch
`disposition`, `stashed_segment`, or a fabricated zero-length user segment
directly. The server applies the transitions above atomically and returns the
saved project. Re-run remains the existing trim-proposal request narrowed to one
`source_id`.

> Both AI keys act on the **trim** proposal only, and nothing on the panel says
> so. A clip carrying an AI trim *and* a hand-set speed reports only the trim in
> its status word. Both are known limits of the locked design, accepted after
> measurement showed splitting the housing would cost the trim bar ~130px of
> drag width.

### 4.4 · Stickiness — a tested requirement

**An assist never changes a field whose `origin` is `"user"`.** Per DECISIONS
§2.2 this is a correctness requirement with its own tests, not a behaviour. With
the approval gates gone it is the entire mechanism by which the person editing
stays in charge.

### 4.5 · Disposition and its three writers

`disposition` is retained (A-3). Its writers:

| Value | Written when |
|---|---|
| `pending` | The proposal is created |
| `adjusted` | The user moves a handle on a clip carrying a proposal |
| `dismissed` | The user presses reject |
| `accepted` | **At export** — every proposal not adjusted or dismissed by then (A-3b) |

Export writes one summary line to the Log: *"Kept 14 of 19 AI trims."* That line
is the instrument for judging whether the assists earn their place, and it is
what puts evidence claim **C-03** back within reach.

> **Amended 2026-07-30 — reject semantics.** A dismissed trim proposal is
> retained, rather than deleted or converted into a user trim, but §3.1 ignores
> it while deriving the played trim. This resolves the former §3.1/§4.3
> contradiction and preserves both reversibility and the C-03 audit denominator;
> see `DECISIONS.md` §4.

---

## 5 · Audio

Two independent levels, `music_level` and `clip_level`, each 0.0–1.0, mixed with
a weighted `amix` into **one exported file**. Both at zero exports silent — and
must still carry a valid AAC track, not an absent one.

- Per-clip mute (the row speaker) is a separate switch from `clip_level`;
  `clip_level` is the mix, mute is per-source.
- The Sound unit's timeline **is** the mix: each trace's brightness is its
  slider's position, so a source at 0 is a ghost on the glass.
- Music starts at `music.in_s`, set by dragging the waveform.
- **When the reel outruns the track, the music stops and the reel plays on with
  clip audio only** (N-4). No loop, no fade. A fade-out is a shelved refinement,
  not an open question.

---

## 6 · Playback and preview

**The Monitor sequences proxies client-side**, seeking each to its in/out, so
edits show instantly. **Save renders the real file** — the thing exported is not
the thing previewed, and the Log says so.

This was the least-specified and highest-risk area of the build, and it is no
longer either. **WO-124 measured it** (2026-07-28); what follows is a record of
results, not a proposal. Numbers, method and limitations:
[WO-124-playback-findings.md](docs/specs/WO-124-playback-findings.md).

The design survived the measurement. **Nothing in v3z changes because of it.**

### 6.1 · The cut — two `<video>` elements, cross-swapped

**The Monitor holds two video elements and swaps between them.** While clip N
plays, clip N+1 is loaded and pre-sought on the idle element; at the cut, the
Monitor swaps.

| Strategy | Cost at the cut |
|---|---|
| **Two elements, cross-swapped** | **0.8 ms** (0.4–1.4) |
| One element, reloaded and re-sought | 36.3 ms (35.0–50.6) |

The difference is structural, not incidental. Starting playback costs 0.1 ms;
the cost is a ~18 ms load and a ~18 ms seek, and the two-element strategy does
not make them faster — **it moves them off the critical path**, paying ~14.7 ms
of preparation while the previous clip is still on screen. At 60 Hz one frame is
16.7 ms, so a 0.8 ms swap lands inside a single frame and a 36.3 ms swap spans
three.

§3.5's preview queue is what makes this possible: the lit set *in order* is
known in advance, so there is always a defined next clip to prepare.

### 6.2 · Seeking is frame-accurate

Across eleven seek targets the displayed frame was the requested frame every
time — **zero frame error**, including a target landing 8.3 s past a keyframe.

**The proxy's keyframe interval is a latency consideration only.** Seek latency
tracks how far past a keyframe the target lands: 9.1 ms just after one, 45.1 ms
at the far end of an 8.3 s GOP, mean 24.6 ms. Clip-scoped scrub and trim-handle
dragging are safe at that cost.

Measured against the old 250-frame GOP; §6.5's recipe now places keyframes about
a second apart, so the figures above are a worst case the product no longer has.

### 6.3 · Speed in preview

**`playbackRate` is exact** — 1.5×, 1.75×, 2.0× and 2.5× all applied with no
clamping and no measurable rate error, including above the assist's 2.0× ceiling
that N-6 permits by hand. `preservesPitch` is supported, so preview matches the
renderer's pitch-preserved `atempo`.

**The renderer is the side that must be made to agree.** `setpts` overshoots a
ramped clip's arithmetic duration by a fixed 1–2 frames, so the renderer clamps
each ramped clip to `kept_duration / rate`. Without that clamp §3.4's played-
duration formula — which is also the reel length the Reel unit displays — is
wrong by ~66 ms per ramped clip, and §9's QA tolerance is breached by a reel
that is otherwise entirely correct.

### 6.4 · The music bed

**A plain `<audio>` element, not WebAudio.** The bed drifts 3.4 ms across a clip
cut and 0.4 ms across a mid-reel seek — both video-side events that never touch
it. WebAudio's complexity buys nothing measurable here.

**Its start must be compensated.** `play()` does not take effect immediately:
the bed lags by ~186 ms, constant and one-time. Set `music.currentTime` to the
reel position *after* `playing` fires rather than assuming the call is
instantaneous, or every reel begins with the music a fifth of a second out.

### 6.5 · Proxies must carry audio

**A proxy carries its source's audio**, encoded as AAC and downmixed to stereo.
A source with no audio of its own gets a proxy with **no audio track** — never a
fabricated silent one, which would be indistinguishable from a clip the user
muted.

This is a requirement, not an implementation note, because three things this
document already promises are unsatisfiable without it:

- **§5's `clip_level` has nothing to act on.** A silent proxy means the mix
  cannot be heard until export, so the user sets a level blind.
- **§5's "the Sound unit's timeline *is* the mix" is false.** The unit draws a
  trace per reel clip at its slider's brightness — describing audio the Monitor
  cannot play.
- **Preview loudness cannot match export loudness** when one of them is silent.

> **Recorded because it was once untrue.** `make_proxy` passed `-an` and every
> proxy shipped silent; WO-124 found it and WO-116a fixed it (2026-07-28). The
> spec *assumed* proxy audio and nothing *required* it, so a future change back
> to `-an` would have contradicted nothing written down. That is what this
> section is for.

Proxy keyframes are placed about a second apart, for the reason in §6.2.

### 6.6 · The reel clock is never an animation frame

**Playback scheduling is driven by media element time, or by `performance.now()`
sampled on media events. Never by `requestAnimationFrame`, `requestVideoFrameCallback`,
`setTimeout` or `setInterval`.**

This is a platform constraint, not a style preference. In a page the browser
considers hidden, animation and video-frame callbacks **do not fire at all**,
and timers are throttled to roughly 1 Hz — while media playback and media events
carry on normally. A Monitor scheduled on `rAF` therefore works perfectly on the
desk and stalls the moment the window is hidden or the user switches tab: a
failure that survives every test and appears only in real use.

> Both traps were hit while measuring. A `setInterval` poll reported every cut
> strategy at ~999 ms — the throttle floor, not a video cost — and a
> `timeupdate` wait reported 297 ms against 266 ms, hiding §6.1's 45× difference
> behind that event's ~250 ms cadence.

### 6.7 · Foreground presentation rerun — measured 2026-07-31

WO-127 reran the retained harness in a visible, focused Chromium page, with
`requestVideoFrameCallback` firing and current audio-bearing proxies. The
presentation-accurate median gap was **25.8 ms** for two elements cross-swapped
(24.4–50.0 ms), versus **58.3 ms** for one element reloaded and re-sought
(57.3–74.9 ms). The same run retained zero frame error across eleven seeks,
exact 1.5×–2.5× playback rates, and music drift within 3.4 ms across a cut.

The foreground result confirms §6.1 rather than contradicting it: the
two-element strategy remains the implementation requirement and the v3z design
does not need to change. The retained harness and its synthetic fixtures were
then deleted as required. Full method and results:
[`WO-124-playback-findings.md` §10](docs/specs/WO-124-playback-findings.md).

---

## 7 · The Log

The Log is **the audit trail** (A-2, A-3). Three lines of glass, newest first,
brightest at the top, two keys down the right edge walking back through the rest.

Each entry is **time · kind · message**, with three kinds:

| Kind | Tag | For |
|---|---|---|
| info | `·` | What happened |
| warn | `WARN` | Something needs attention but nothing failed |
| fault | `FAULT` | Something failed |

### 7.1 · What it must carry

1. **Standing lines** — pinned, always reachable, never aged out: *originals are
   opened read-only and never changed*; *previews are made on this Mac, nothing
   is uploaded and nobody is recognised* (A-7).
2. **Ingest summary** — *"8 files read from Beach Day. 5 in the reel, 3 out."*
3. **Per-clip faults and warnings** — moved sources (`WARN`), undecodable files
   (`FAULT`), and **every clip trimmed to nothing or to under a second**
   (`WARN`, required by A-6).
4. **Proposal reasons** — the `human_text` of each `ReasonRecord`, which is
   already written to be read.
5. **Assist applied and reverted**, with before → after reel length, and which
   clips kept the user's own edit — *"Trim reverted on 4 clips. Kids running in
   kept your own trim."*
6. **Disposition changes**, and the export summary in §4.5.
7. **Save failures** (§8.2). Never silent.
8. **Speed warnings** — clip audio is time-stretched wherever rate ≠ 1.0×.

### 7.2 · Retention, persistence, pinning and precedence

**SO-2 closed — owner, 2026-07-29.** Four answers, all constrained by two things
that were already decided: A-8 locks the Log to **three lines of glass**, so no
answer may add a second surface; and the contract is frozen, so no answer may
change `project.json`.

#### It persists, in a sidecar

**The Log survives closing and reopening a project.** A-3 makes it the audit
trail and *"the way to learn whether the assists are earning their place"*, and
A-3b's export summary is the **only named measure** for evidence claim C-03. A
session-only Log discards that the moment the app closes, which would put C-03
back where `disposition` was retired to rescue it from.

**It lives in a per-project sidecar `log.json`, not in `project.json`.** Two
reasons, and the second is the load-bearing one:

- `project.json` is **state**; the Log is append-only **history**. Growing an
  unbounded array inside the canonical state document confuses the two.
- The contract is **frozen** (§3). A sidecar closes SO-2 **without amending it**,
  and `analysis.json` already establishes the pattern.

#### It holds 500 entries

Evicted oldest-first. A 50-clip reel's full trim and speed run writes on the
order of 110 entries, so 500 holds several such runs plus their export
summaries — deep enough to read back a session's work, small enough that
`log.json` stays a document rather than a database.

#### Pinning is exemption from eviction, not a reserved row

The standing lines of §7.1 are **never evicted**, sit at the foot of the
scrollback, and are **what the three lines show when a project opens**, before
any event has been logged.

> **This is weaker than "always on screen", and deliberately so.** Three lines
> cannot permanently reserve a row for each of two standing lines *and* carry a
> live fault — that would leave one flowing line. A-7's decision was that the
> assurance must not vanish; exemption from eviction plus the opening state
> delivers that. Permanent visibility would need a fourth line, which A-8 does
> not permit.

#### Severity outranks recency in the visible window

Two rules, and together they are what stop a forty-clip reel burying a failure:

1. **A bulk run writes its detail first and its summary last.** A 19-clip trim
   appends the per-clip reason lines, *then* the summary. Newest-first means the
   summary — *"Trim proposed on 19 clips."* — is what you see, and every
   individual reason is one scroll away. **Nothing is withheld**, satisfying A-2;
   nothing floods, because the headline is written last.
2. **An `info` entry never displaces a `WARN` or `FAULT` from the visible
   strip.** The newest warning or fault holds its line until the user scrolls the
   Log or a newer warning or fault takes it. Reason lines are `info`, so a clip
   trimmed to nothing (`WARN`, required by A-6) cannot be pushed off by the
   thirty-nine reasons logged after it.

> **The risk this closes around, not away.** The Log was drawn as three lines for
> occasional warnings and has eight jobs. Reading back a history and catching a
> live failure are different tasks and one strip is still doing both. The rules
> above make that survivable rather than safe, and the Log remains **the most
> likely candidate for the correction pass A-8 anticipates.** If it fails in use,
> it fails here.

### 7.3 · `log.json`

Per project, beside `project.json`, local, never committed.

```
LogEntry
  at: str                     # ISO-8601
  kind: "info" | "warn" | "fault"
  text: str                   # written to be read — a ReasonRecord's human_text
                              # goes here verbatim
  code: str | null            # stable machine code where one exists (LEADING_BLUR)
  source_id: str | null       # the clip it concerns, when it concerns one
  standing: bool = false      # exempt from eviction (§7.2)
```

Entries logged before a project exists — a track chosen first (§8) — are held
for the session and written on the project's first save.

**Write ownership.** The server writes every event it can observe: project
creation and standing lines, ingest results, proposal detail and summaries,
assist transitions, disposition changes, export summaries and job failures.
The optimistic UI writes a failure to its visible strip immediately. If the
failure was first observed by the client, a constrained client-event append
persists that already-visible entry when the server is reachable; absolute paths
are scrubbed before it is accepted. The Log is read independently of
`project.json` through §8's Log route.

---

## 8 · The HTTP contract

Local only, on `127.0.0.1`, with every protection in
[CONSTRAINTS.md](docs/CONSTRAINTS.md) — origin allow-listing, no permissive CORS,
a per-launch capability token on every state-changing route, path scrubbing.
**Every new mutating route needs its own guard test that fails when the guard is
removed.**

> **Amended 2026-07-30 — frontend-operability seam.** A post-authorization
> review found that the original route table could not express §4.3's reject or
> reversible bin transitions, could neither read nor populate §7's persistent
> Log, gave the browser no way to obtain a server-computed music hash and
> duration, and did not expose §8.3's silent link repair. DECISIONS §5 makes
> those server-owned actions and adds only the routes below. `project.json` and
> the design are unchanged.

| Route | Purpose |
|---|---|
| `POST /api/pick-folder` · `POST /api/pick-file` | Native pickers. `pick-file` serves both track selection and relink |
| `POST /api/music/probe` | Probe a selected local track before a project exists; return the server-computed `Music` value (`track_ref`, content hash, duration, default in-point) |
| `POST /api/project` · `GET /api/project/{id}` | Create, read |
| `PATCH /api/project/{id}` | name, target, output resolution, audio mix, assist toggles |
| `PATCH /api/project/{id}/clip/{source_id}` | order, segment, speed ranges, audio, mute |
| `POST /api/project/{id}/clip/{source_id}/bin` | Toggle bin / restore atomically, stashing or restoring the effective trim |
| `POST /api/project/{id}/clip/{source_id}/reject-trim` | Retain and dismiss the trim proposal so its effect is removed |
| `POST /api/project/{id}/relink/{source_id}` | Repoint a clip at a different file |
| `POST /api/project/{id}/repair-links` | Automatically repair dead source paths by content hash beneath `media_root`; preserve edit state and return misses as unlinked |
| `POST /api/import/{id}/scan` · `POST /api/analyze/{id}` | Ingest and analysis jobs |
| `POST /api/propose/trim/{id}` · `POST /api/propose/speed/{id}` | The assists |
| `GET /api/jobs/{job_id}` | Job status |
| `GET /api/project/{id}/log` · `POST /api/project/{id}/log` | Read the retained sidecar; persist a path-scrubbed client-observed failure already shown by the optimistic UI |
| `GET /api/media/proxy/{source_id}` · `thumb` · `peaks` | Preview media, computed on demand and cached |
| `GET /api/music/peaks` | **Keyed by content hash**, because a track may be chosen before a project exists |
| `POST /api/export/{id}` · `GET /api/export/{id}/download` | Render and retrieve. No `audio_mode` anywhere |

**Removed:** `POST /api/project/{id}/approve/{stage}` and every gate read.
`GET /api/export/{id}/download/{audio_mode}` collapses to one file.

### 8.1 · Concurrency

Optimistic, keyed on `updated_at`, `409` on mismatch.

Bin, reject and link repair carry the caller's `updated_at` and return `409` on
a stale project. The Log is a sidecar rather than project state, so appending a
Log entry neither requires nor advances `Project.updated_at`.

### 8.2 · Saves are optimistic with a visible failure path

A control responds the instant it is touched. If the write fails or conflicts,
**the control visibly reverts and the Log says why** (N-9). A silent background
save failure is worse than the 409 and is never acceptable. The client adds the
failure to the visible Log immediately; if the server cannot accept the sidecar
append at that moment, the entry remains in the session buffer and is retried
when communication resumes.

### 8.3 · Linking

The path is the primary link; a dead path is re-found by content hash under
`media_root` and repaired silently where found. A file that cannot be found comes
back **unlinked**, and its row's chain key carries the yellow ring. Link also
repoints a **valid** clip at a different file — trim, order, speed and mute
survive the change of source beneath them.

Repair is a capability-protected `POST`, not a state-changing `GET`. The app
invokes it automatically after opening a project. The server searches only
beneath that project's `media_root`, preserves the existing `source_id` and
every clip edit, and never follows a content match outside the root.

### 8.4 · Corrective action bodies and responses

The corrected seam is deliberately narrow:

```
ProjectActionBody
  updated_at: str

MusicProbeBody
  track_ref: str

ClientLogBody
  kind: "warn" | "fault"       # client-observed failures only
  text: str
  code: str | null
  source_id: str | null
```

- Bin, reject and repair-links accept `ProjectActionBody` and return the saved
  `Project`. The server supplies every state transition; no internal field is
  accepted from the client.
- Music probe accepts `MusicProbeBody` and returns `Music`, with the hash and
  duration computed from the local file. It may populate the session Log buffer
  but does not require a project.
- `GET …/log` returns the retained `[LogEntry]` sidecar in its canonical
  oldest-first order. The frontend reverses that order for §7's newest-first
  glass.
- `POST …/log` accepts `ClientLogBody`, stamps `at`, forces
  `standing: false`, scrubs paths, appends through the 500-entry retention
  rule, and returns the accepted `LogEntry`. It cannot create `info` or standing
  entries; known product events remain server-owned.

---

## 9 · Render, export and QA

Render reads **originals**, never proxies. Per clip: seek to the effective in/out,
apply `setpts` per effective speed range with `atempo` on the audio at matching
rates, scale and centre-crop to the output resolution, concatenate in `order`,
mix audio per §5.

- **Clips not in the reel are skipped** — trimmed out, unlinked or damaged.
- **If every clip is out, the render fails with a stated reason** rather than
  handing ffmpeg an empty concatenation.
- **Upscaling beyond the source is refused or flagged, never silent.** A 4K export
  of 1080p footage is a bigger file and not a better reel.
- GPS and identifying metadata are stripped from the output.

**QA blocks export and states why.** Checks: not black · duration within ±0.5 s of
the computed reel length · **resolution matches the project's setting** (not a
hardcoded 1080×1920) · H.264/AAC · safe margins · frame count · and **audio
matched to the levels** — `music_level > 0` means the output must not be silent;
both at zero means it must be silent *and* still carry a valid AAC track.

---

## 10 · Non-functional

- Ingest, analysis and render on a real day's footage should each complete in a
  timeframe that keeps the whole edit within one sitting. **The existing targets
  are unvalidated** — no run against real footage has ever happened.
- ffmpeg and ffprobe are required and their absence is reported, never silently
  worked around.

### 10.1 · The rack under real data

**SO-4 closed — owner, 2026-07-29.** v3z's stated achievement is that no element
differs in size between any two of the six states. That was drawn against fixed
fake data, and the open question was what real data does to it. The answers below
are **measured against the v3z mockup itself**, not estimated.

**The invariant holds, and is now a recorded number.** The rack is **767 px tall
in all six states**, unchanged at every viewport width from 1024 px to 1440 px.
That is a measurement of the drawing, not a guarantee about the build.

#### Minimum viewport: 960 px wide

The Monitor column is a fixed **465 px**; the side column stops overflowing its
units at about **470 px**; the rack's own padding and border are 20 px.
**465 + 3 + 470 + 20 ≈ 960 px.** Below a ~470 px side column, six of the units
overflow their boxes at once.

**Below the minimum the page scrolls horizontally. It never reflows** — reflow
would change element sizes between viewports, which is the same failure A-8's
invariant exists to prevent, one axis over.

> **The rack has no intrinsic width and must be given one.** Both columns are
> absolutely positioned, so the rack contributes no min-content width: in a
> narrow container it **collapses to its 20 px of chrome** rather than
> overflowing, and a wrapper's `overflow-x: auto` never engages. A `min-width`
> on the rack is what makes the scroll behaviour above actually happen. This is
> a real defect in the mockup's CSS, found by measuring it.

Height is not constrained: 767 px fits inside a 900 px viewport, the shortest
Mac laptop screen in normal use.

#### Long names truncate in the middle, not at the tail

**Clip names are always the file's basename** (§1 — there is no rename), and
camera basenames differ at the **end**: `IMG_20260720_093015_0001.mov` and
`IMG_20260720_093015_0002.mov` share every character but one.

v3z truncates at the tail (`text-overflow: ellipsis` on the index row and the
Monitor overlay), which collapses those two to the **same string** — two
different clips, indistinguishable in the index, on the one surface that
identifies them.

**Every displayed name — clip, track, reel — truncates in the middle, keeping
head and tail.** A fixed character budget per surface, so a long name cannot
change any element's size.

#### The clip index at 200 clips

**Scroll performance is a non-issue, and this was checked rather than assumed.**
The key column is already windowed: **4 rows and 28 buttons in every one of the
six states**, independent of clip count. Only the glass text rows render the
whole list. At 200 clips that is 28 controls and 200 text rows — no
virtualisation needed, and none is specified.

**A position counter is needed and v3z has none.** The Monitor carries a queue
counter (*"3 of 7"*); the index carries nothing, so a four-row window over 200
clips leaves the user with no idea where they are. The Clip index gains a
**window-range counter** — same yellow as every other counter, per §2.1's design
law.

#### The invariant is enforced by testing its causes, not its geometry

Measuring rendered geometry needs a browser-driving dependency, which is outside
WO-117's frozen manifest and a stop-and-ask under ADP-002 §3 — a heavy thing to
add to a project with no CI, to guard a drawing.

**Instead the build tests what makes the geometry stable**, all of which is
unit-testable with no browser:

- the clip index renders **exactly four key rows** at any clip count;
- every displayed name is truncated to its surface's **fixed character budget**;
- counters are **fixed-width**, so a reel going from 9 to 10 clips moves nothing.

**The rendered 767 px stays an aspiration**, verified by eye in the correction
pass A-8 anticipates. Recorded plainly: those three tests make the invariant
*likely*, not *proven*.

---

## 11 · Where this spec departs from v3z

Recorded rather than left to be discovered.

| Departure | Why |
|---|---|
| **Proposal reasons appear in the Log.** v3z states on its own face that no reason appears anywhere and its Log says *"Reasons recorded to project.json; not shown on screen."* | DECISIONS A-2. That Log line is now wrong and the reasons themselves take its place |
| **`disposition` is retained.** v3z drops it | DECISIONS A-3 |
| **The read-only line is pinned**, not merely present at startup | A-7's placement with the mechanism that makes it survive a newest-first three-line window |
| **Trims are stored in seconds; v3z's generator uses fractions** | Fractions are a drawing convenience. Seconds are absolute, survive a re-probe, and render directly |
| **Speed ranges are stored in source time; v3z's generator stores fractions of the kept region** | So a ramp stays on the content it was computed for when a trim handle moves |
| **Names truncate in the middle; v3z truncates at the tail** | Clip names are file basenames and camera basenames differ at the end, so tail truncation renders two different clips as the same string (§10.1) |
| **The Clip index gains a window-range counter; v3z has none** | A four-row window over 200 clips otherwise gives no sense of position. The Monitor already carries a queue counter; the index carries nothing (§10.1) |
| **The rack is given a `min-width`; v3z's has none** | Both its columns are absolutely positioned, so it collapses instead of scrolling in a narrow container. Measured, not theorised (§10.1) |

---

## 12 · Validation gates

The build is done when, on a real day's footage with a recorded consent:

1. A folder imports; unreadable files are reported and never crash the scan.
2. Trim proposes on every clip, and every proposal carries a reason that is
   **right**, not merely present. *(The old gate asserted only that a reason
   existed, which is why a confidently wrong `OVEREXPOSED` passed every check in
   the suite for weeks.)*
3. Turning an assist off restores every clip **except** those edited by hand.
4. A clip trimmed to nothing leaves the reel, says so in the Log, and comes back
   when the handles move.
5. Removal via the bin is exactly reversible.
6. A moved file is relinked; an undecodable one is reported and skipped.
7. The mix exports one file whose audio matches the two levels.
8. QA blocks a bad render and states why.
9. Export writes the kept-count summary to the Log.
10. Save→reopen is byte-equivalent.
11. Every guard in [CONSTRAINTS.md](docs/CONSTRAINTS.md) fails when its
    protection is removed.

**No claim in [EVIDENCE-LEDGER.md](docs/specs/EVIDENCE-LEDGER.md) moves off
`assumed` on synthetic fixtures.** Every gate above needs real footage.

---

## 13 · Deferred, not deleted

Cutting one clip into several kept pieces · a music fade-out · ducking · beat and
section detection · multi-folder projects · saliency reframing (centre-crop is
the fallback and can decapitate people at frame edges) · per-clip audio retention
beyond mute · filters · NLE export · phone access · packaging and distribution ·
the selection assist, which is cancelled rather than deferred (A-5b).

---

## 14 · What this spec still owes

Accepted with four things unsettled. They are recorded here rather than left in
prose so that acceptance does not quietly swallow them. **Each blocks specific
work and nothing else** — the rest of the build is unblocked by this document.

**All four are now closed** — SO-1 and SO-2 by decision, SO-3 and SO-4 by
measurement. The table is kept rather than deleted: what a spec did not know at
acceptance, and how each gap was shut, is part of the record.

| # | Owed | Stated in | Blocks |
|---|---|---|---|
| **SO-1** | ~~The speed assist's parameters~~ — **closed 2026-07-28**, see §4.2 | §4.2 | Closed. WO-120 is unheld as of ADP-002 Amendment 2 |
| **SO-2** | ~~The Log's retention, persistence and pinning~~ — **closed 2026-07-29**, see §7.2 and §7.3 | §7.2 | Closed. The Log unit is unblocked. The *design* risk it carries is not closed — §7.2's last note |
| **SO-3** | ~~The playback engine~~ — **closed 2026-07-29**, measured by WO-124; its foreground presentation rerun closed 2026-07-31 by WO-127, all written into §6.1 – §6.7 | §6 | Closed. The Monitor is unblocked, and the v3z design survived both measurements. |
| **SO-4** | ~~The rack layout invariant under real data~~ — **closed 2026-07-29**, see §10.1 | §10.1 | Closed. The rack design system and the clip index are unblocked |

Nothing here is outstanding. One thing the closures leave open is **not** a spec
gap and is tracked elsewhere: whether one three-line strip can carry the Log's
eight jobs (§7.2), for the correction pass A-8 anticipates.
