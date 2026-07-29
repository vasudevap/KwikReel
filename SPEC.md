# SPEC — KwikReel

**Status: DRAFT for owner review. Normative once accepted. Nothing here is
authorized to be built.**
Written 2026-07-28, forward from [mockup-v3z](docs/design-claude/mockup-v3z.html)
and [DECISIONS.md](docs/DECISIONS.md).

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

The design is [v3z](docs/design-claude/README.md), which is locked (A-8). Its
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
Sidecar `analysis.json` per source holds facts. Both are local; neither is ever
committed.

### 3.1 · The central structural rule — effective values are derived

**The assists do not mutate clips. The toggles are a live derivation.**

This is transcribed directly from the v3z generator's own state model and is the
most important structural decision in this document:

```
effective_trim(clip):
    if clip.origin.segments == "user":  return clip.segment      # yours always wins
    if project.trim_assist_on and clip.proposals.segments:
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

**Rule: ramp the dull stretches.** A second is **dull** when `motion_energy` and
`audio_rms` are both low. Contiguous dull stretches become `SpeedRange`s at
**1.5×–2.0×**, scaled within that band by how dull they are. Everything else
stays 1.0×.

The spec must fix, before implementation: the dullness thresholds, the minimum
ramp length (a half-second ramp is a glitch, not an effect), and how adjacent
ranges merge. **One clip may carry several ranges.**

The assist never proposes above 2.0×. **Hand-set rates are uncapped** (N-6).

> **Accepted cost, recorded.** Clip audio is time-stretched with pitch preserved.
> The filter is clean to roughly 2×; beyond that it must be chained and degrades
> audibly. Uncapped manual rates can therefore produce audio the user will not
> like. The Log warns whenever any clip renders at a rate other than 1.0×.

### 4.3 · The controls that act on a proposal

- **Reject (✕)** discards this clip's proposal — `disposition: "dismissed"`. The
  clip reverts to whole (or to the user's own trim, if there is one).
- **Re-run (↻)** asks for a fresh proposal for this clip alone.
- **Bin** sets the effective trim to zero length, **stashing the previous
  effective value first**. Pressing it again restores the stash. This is the only
  reason `stashed_segment` exists, and it is what makes removal genuinely
  non-destructive.

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

**This is the least-specified and highest-risk area of the build.** Before any
Monitor code, a spike must answer, with measurements rather than opinion:

- clip-to-clip transition: one element reloaded and sought, or two cross-swapped?
  What gap at a cut is acceptable, and what is achieved?
- seek accuracy against the proxy's keyframe interval;
- whether `playbackRate` preview matches the rendered `setpts` result, and how
  pitch is handled in preview versus export;
- how the music bed stays aligned across a transition and a seek.

If the spike cannot deliver a Monitor good enough to judge an edit on, **the
design changes before the frontend is built**, not after.

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

### 7.2 · What the spec still owes

Retention depth · whether the Log persists across reopening a project · how
pinning composes with a newest-first list · and whether a forty-clip reel's forty
reason lines belong in the same window as a live fault.

> **Flagged as the most likely correction.** The Log was drawn as three lines for
> occasional warnings and now has eight jobs. Reading back a history and catching
> a live failure are different tasks, and one strip is doing both.

---

## 8 · The HTTP contract

Local only, on `127.0.0.1`, with every protection in
[CONSTRAINTS.md](docs/CONSTRAINTS.md) — origin allow-listing, no permissive CORS,
a per-launch capability token on every state-changing route, path scrubbing.
**Every new mutating route needs its own guard test that fails when the guard is
removed.**

| Route | Purpose |
|---|---|
| `POST /api/pick-folder` · `POST /api/pick-file` | Native pickers. `pick-file` serves both track selection and relink |
| `POST /api/project` · `GET /api/project/{id}` | Create, read |
| `PATCH /api/project/{id}` | name, target, output resolution, audio mix, assist toggles |
| `PATCH /api/project/{id}/clip/{source_id}` | order, segment, speed ranges, audio, mute |
| `POST /api/project/{id}/relink/{source_id}` | Repoint a clip at a different file |
| `POST /api/import/{id}/scan` · `POST /api/analyze/{id}` | Ingest and analysis jobs |
| `POST /api/propose/trim/{id}` · `POST /api/propose/speed/{id}` | The assists |
| `GET /api/jobs/{job_id}` | Job status |
| `GET /api/media/proxy/{source_id}` · `thumb` · `peaks` | Preview media, computed on demand and cached |
| `GET /api/music/peaks` | **Keyed by content hash**, because a track may be chosen before a project exists |
| `POST /api/export/{id}` · `GET /api/export/{id}/download` | Render and retrieve. No `audio_mode` anywhere |

**Removed:** `POST /api/project/{id}/approve/{stage}` and every gate read.
`GET /api/export/{id}/download/{audio_mode}` collapses to one file.

### 8.1 · Concurrency

Optimistic, keyed on `updated_at`, `409` on mismatch.

### 8.2 · Saves are optimistic with a visible failure path

A control responds the instant it is touched. If the write fails or conflicts,
**the control visibly reverts and the Log says why** (N-9). A silent background
save failure is worse than the 409 and is never acceptable.

### 8.3 · Linking

The path is the primary link; a dead path is re-found by content hash under
`media_root` and repaired silently where found. A file that cannot be found comes
back **unlinked**, and its row's chain key carries the yellow ring. Link also
repoints a **valid** clip at a different file — trim, order, speed and mute
survive the change of source beneath them.

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
- The timeline stays responsive at 50+ clips. The four-row window and its scroll
  keys are the mechanism; that they are sufficient is untested.
- ffmpeg and ffprobe are required and their absence is reported, never silently
  worked around.

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
