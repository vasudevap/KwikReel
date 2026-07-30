# WO-124 · Playback engine — findings

**Status: MEASURED, 2026-07-28.** Closes `SPEC.md` §14 **SO-3**, subject to the
one limitation in §7. Run under [ADP-002](../implementation-plans/ADP-002-contract-v2-and-backend.md) §4.

Raw numbers: `spike/wo-124-playback/results.json`. The code that produced them
is throwaway. ADP-002 Amendment 7 retains it only through WO-127, which reruns
the harness foregrounded as `SPEC.md` §6.7 requires, appends that result here,
then deletes the spike directory; **this document is what survives.**

**The verdict: the Monitor is buildable as `SPEC.md` §6 describes it, and the
v3z design does not have to change.** Four of the five questions came back
comfortably. The fifth found a real defect — in the *ingest* code, not the
design.

---

## 0 · How to read these numbers

Measured on **Chromium 148 (Electron 42)**, 11 cores, on the owner's Mac,
against proxies built by the **real `FFmpegIngest.make_proxy`** — not a
hand-rolled ffmpeg line, because the proxy's own keyframe interval is exactly
what half of §6 asks about.

Frame identity is not inferred. Each fixture frame carries a **9-bit index in
nine large black/white blocks**, so "which frame is on screen" is a threshold on
nine pixels rather than a guess. Large flat blocks are the one thing H.264
preserves faithfully; a timecode overlay would have needed OCR and a colour
gradient would not have survived yuv420p.

> **Two measurement traps were hit and fixed before these numbers were taken,
> and both would have produced confident nonsense.** A `setInterval` poll
> reported *every* strategy at ~999 ms — that is Chromium throttling background
> timers to 1 Hz, not a video cost. Waiting on `timeupdate` reported the two cut
> strategies at 297 ms and 266 ms — that is `timeupdate`'s ~250 ms cadence, and
> it hid a **45×** difference between them. Everything below is timed on
> discrete media events (`seeked`, `playing`) or `performance.now()`, never on a
> timer or an animation frame.

---

## 1 · Seeking is frame-accurate. The long GOP costs latency, not accuracy

**The proxy's keyframe interval is 8.333 s** — x264's default 250-frame GOP at
30 fps, because `make_proxy` passes no `-g`. §6 asked whether a proxy built that
way "may not seek to an arbitrary in-point cleanly."

It does. **Across 11 seek targets the displayed frame was the requested frame
every time — maximum error 0 frames.**

| Seek target | s past keyframe | Frame error | Latency |
|---|---|---|---|
| 0.5 s | 0.5 | 0 | 9.1 ms |
| 4.0 s | 4.0 | 0 | 39.4 ms |
| 8.3 s | 8.3 *(worst case — just before the next keyframe)* | 0 | **45.1 ms** |
| 8.4 s | 0.067 *(just after it)* | 0 | 11.9 ms |
| 11.9 s | 3.567 | 0 | 27.8 ms |

The pattern is clean and it is the expected one: **latency tracks how far past a
keyframe you land**, because the decoder walks forward from that keyframe. Worst
observed 45.1 ms, mean 24.6 ms.

**Consequence for the build.** Trim-handle dragging and clip-scoped scrub are
safe: a scrub that re-seeks on every pointer move has a ~25 ms floor per seek,
which is fine for a 60 Hz drag. Nothing in the Editor or Transport needs to be
redesigned around seek accuracy.

**Recommended, not required:** adding `-g 30` to `make_proxy` would cap the walk
at one second and roughly quarter the worst case. It costs bitrate and it is an
`backend/ingest/` change, which **no ADP-002 Work Order owns** (see §6).

---

## 2 · The cut: two elements, decisively — 0.8 ms against 36.3 ms

§6 asked: "one element reloaded and sought, or two cross-swapped?"

| Strategy | Cost at the cut (median) | Range |
|---|---|---|
| **Two `<video>` elements, cross-swapped** | **0.8 ms** | 0.4 – 1.4 ms |
| One `<video>`, reloaded and re-sought | 36.3 ms | 35.0 – 50.6 ms |

**A 45× difference, and it is structural rather than incidental.** The
single-element breakdown says why:

| Component | Median |
|---|---|
| `load()` → `loadeddata` on the new source | 18.3 ms |
| `seek` to the in-point | 18.3 ms |
| `play()` → `playing` | **0.1 ms** |

Starting playback is free. **Loading and seeking are the entire cost, and the
two-element strategy does not make them faster — it moves them off the critical
path**, paying them while the previous clip is still on screen. Measured
preparation cost: 14.7 ms, incurred early where nobody sees it.

**Consequence for the build.** WO-127 builds the Monitor on **two `<video>`
elements, with clip N+1 loaded and pre-sought while clip N plays.** At a 60 Hz
refresh one frame is 16.7 ms, so a 0.8 ms swap lands inside a single frame while
a 36.3 ms swap spans two to three. That is the difference between a cut and a
visible stutter.

The preview queue in `SPEC.md` §3.5 makes this straightforward: the lit set *in
order* is known ahead of time, so there is always a well-defined "next clip" to
prepare.

---

## 3 · `playbackRate` is exact. The renderer is the one that drifts

§6 asked whether `playbackRate` preview matches the rendered `setpts` result.

**The preview is exact at every rate the product can produce**, including above
the assist's 2.0× ceiling, which N-6 permits by hand:

| Rate | Applied | Clamped? | Measured effective | Error |
|---|---|---|---|---|
| 1.5× | 1.5 | no | 1.500 | 0 % |
| 1.75× | 1.75 | no | 1.750 | 0 % |
| 2.0× | 2.0 | no | 2.000 | 0 % |
| 2.5× | 2.5 | no | 2.500 | 0 % |

**The disagreement is on the renderer's side.** `setpts` + `atempo` overshoots
the arithmetic duration.

> **Corrected 2026-07-29.** This section first reported the overshoot as a
> **percentage** — +0.42 % to +1.39 % — measured at a single clip length. That
> framing was wrong and it pointed at the wrong remedy. A follow-up measurement
> across four clip lengths shows the overshoot is **not proportional to anything
> about the clip.** The original percentages are arithmetically correct and
> causally misleading; what follows replaces them.

### 3.1 · It is a fixed 1–2 frames per ramped clip

The same overshoot, in milliseconds, at every source duration tested:

| Rate | 2 s source | 6 s | 12 s | 30 s | Spread |
|---|---|---|---|---|---|
| 1.0× *(control)* | +20 ms | +14 ms | +4 ms | 0 ms | — |
| 1.5× | +33 ms | +33 ms | +33 ms | +33 ms | **0 ms** |
| 2.0× | +66 ms | +66 ms | +66 ms | +66 ms | **0 ms** |
| 2.5× | +66 ms | +66 ms | +66 ms | +66 ms | **0 ms** |

`+33 ms` is exactly one frame at 30 fps; `+66 ms` is two. The mechanism is
**resampling the compressed timeline back to CFR**: ffmpeg lands 1–2 frames over
and the container duration is `nb_frames / fps` exactly. At 2.0× a 12 s clip
wants 180 frames and gets 182.

**So ramped *seconds* are irrelevant. Ramped *clip count* is the only variable.**
A 30 s clip and a 2 s clip cost the same 66 ms.

### 3.2 · It accumulates, and the budget is about seven clips

Measured on a concatenation of six 2.0× clips: **+420 ms.** Linear.

Against `SPEC.md` §9's ±0.5 s that is a budget of roughly **7 ramped clips at
2.0×**, or ~15 at 1.5×. §10 scopes the product at **50+ clips**, and §4.2's rule
is "ramp the dull stretches" — on a family day that is plausibly most of them.
This is a normal reel, not an edge case.

### 3.3 · It is a correctness bug, not a gate-tuning question

The QA gate is the second victim, not the first. §3.4 defines *Played duration*
as `Σ (overlap with a ramp) / rate + (kept time under no ramp)`, and **that same
arithmetic is what the Reel unit displays as reel length** (§2.4).

So a reel with twenty ramped clips does not merely fail a check — **it tells the
user 1:23 and hands them a file of 1:24.3.** Any remedy that only adjusts the
gate leaves the displayed length wrong.

### 3.4 · The remedy: clamp each ramped clip to its arithmetic duration

Pass `-t (kept_duration / rate)` per clip. Measured:

| Strategy | Frames | Duration | Overshoot |
|---|---|---|---|
| default | 92 | 3.0660 s | +66.0 ms |
| **`-t` exact** | **90** | **3.0000 s** | **+0.0 ms** |
| `-fps_mode passthrough` | 180 | 3.0333 s | +33.3 ms |
| `-fps_mode passthrough` + `-t` | 179 | 3.0000 s | +0.0 ms |

Six clamped clips concatenated: **18.023 s against a wanted 18.000** — the
residual 23 ms is container overhead and does **not** accumulate per clip.

**The clamp costs nothing editorially.** A 6 s source at 30 fps is 180 frames;
at 2.0× the content is 90 frames, and clamping yields exactly 90. The frames it
removes are **spurious tail frames the resampler invented**, not content.

**No `SPEC.md` change is required, and that is the argument for this remedy over
the alternatives.** Clamping makes §3.4's formula *true*, so §9's ±0.5 s keeps
meaning what it says and still catches the truncated-render and black-output
faults it exists for.

Rejected, with reasons:

| Alternative | Why not |
|---|---|
| **Widen §9's tolerance** | A tolerance that scales with clip count stops catching a genuine one-second truncation on a 50-clip reel. It trades a working gate for a bug |
| **Let QA model the quantisation** | Spreads renderer internals into the spec's user-facing maths, and leaves the displayed reel length wrong regardless |
| **`-fps_mode passthrough` alone** | Halves the error rather than removing it, and produces VFR output |

**Consequence for the build.**

- **WO-121** clamps every ramped clip with `-t (kept_duration / rate)`.
- **WO-122** keeps §9's ±0.5 s unchanged, and gains a regression test that a
  multi-clip ramped reel lands inside it — the check that would have caught this.

> **This was originally raised as a `SPEC.md` §9 stop-and-ask. It is not one.**
> With the mechanism measured it is a renderer defect with a clean fix, and §9
> stands exactly as written.

---

## 4 · The proxies have no audio at all — the one real defect

This is the finding that matters most, and it is not in the design.

**`make_proxy` passes `-an`. Every proxy is silent.** Confirmed both ways:
`ffprobe` reports no audio stream, and the browser's
`webkitAudioDecodedByteCount` is `0` after load.

`SPEC.md` §6 asks "how pitch is handled in preview versus export." **As built
the question is moot, because there is no preview audio to have a pitch.** And
that unravels three things the spec asks for:

- **§5 — `clip_level` has nothing to act on in preview.** The Monitor cannot
  play clip audio at any level, so the user sets a mix they cannot hear until
  they export.
- **§5 — "the display *is* the mix"** fails on its own terms. The Sound unit
  draws every reel clip's audio trace at its slider's brightness, describing
  audio the preview cannot play.
- **§6 — "preview loudness must match export loudness"** cannot be satisfied.
  One of them is silent.

**The browser side is ready.** `preservesPitch` is supported and settable, so a
proxy carrying audio would preview at the renderer's pitch-preserved `atempo`
behaviour without further work.

**Consequence for the build.** `make_proxy` must stop passing `-an` and encode
an AAC track. It is a small change — and again `backend/ingest/` is **owned by
no ADP-002 Work Order** (§6).

> **Why no test caught this.** For the same reason the letterbox fault survived
> to WO-116: the proxy path is barely exercised. Analysis tests call
> `probe_clip`, which leaves `proxy_path` unset, so the proxies the app actually
> plays are built and inspected almost nowhere.

---

## 5 · The music bed holds sync. An `<audio>` element is enough

§6 asked how the bed stays aligned across a transition and a seek.

| | Offset from wall clock |
|---|---|
| After start | −186.2 ms |
| After a clip cut | −189.6 ms |
| After a mid-reel seek | −189.2 ms |

**Drift across a cut: −3.4 ms. Drift across a seek: +0.4 ms.** The bed does not
care about either — both are video-side events and it is never touched.

The −186 ms is **startup offset, not drift**: the gap between calling `play()`
and the element actually starting. It is constant, and reporting it as drift
would have condemned a bed that is in fact keeping near-perfect time.

**Consequence for the build.** WO-128 uses a plain `<audio>` element. **WebAudio
is not required**, and the complexity it would add is not justified by anything
measured here. But the startup offset must be **compensated, not ignored**: set
`music.currentTime` to the correct reel position *after* `playing` fires, rather
than assuming `play()` takes effect immediately. Left uncompensated, every reel
starts with the music ~0.19 s out.

---

## 6 · Two things this spike found that nobody owned — **now fixed**

Both remedies were in **`backend/ingest/`**, which ADP-002 §4 assigned to no
Work Order — the plan called ingest "survives", and against `SPEC.md` §3 the
*contract* does survive. Its **proxy recipe** did not.

| Finding | Remedy | Severity |
|---|---|---|
| Proxies are silent (`-an`) | Encode an AAC track, downmixed to stereo | **Blocked §5 and §6 as written.** The Sound unit could not do its job |
| 8.333 s keyframe interval | `-g` at one keyframe per second | Optimisation. Seeking was already correct; this only reduces a 45 ms worst case |

> **Resolved 2026-07-28 by ADP-002 Amendment 3 · WO-116a**, which gives
> `backend/ingest/` an owner and lands both. A proxy of a source with audio now
> carries a decodable AAC track; a silent source still gets **no** track, rather
> than a fabricated one that would be indistinguishable from a muted clip.
>
> **The missing test is the real fix.** The suite's one proxy assertion used
> `landscape_silent` — a source with no audio — so an audio check would have
> found nothing missing and passed. Three tests now cover it, and both new
> assertions were confirmed to **fail against the old recipe** before being
> accepted; a test written against a bug it cannot detect is what produced this
> finding in the first place.

---

## 7 · What this spike did not measure, and why

**The visible black-frame duration at a cut.** The numbers in §2 are
time-to-`playing`, which is what the two strategies differ by; they are not the
duration of any gap a viewer would perceive.

Presentation-accurate timing needs `requestVideoFrameCallback`, and **rVFC does
not fire in a page the browser considers hidden.** Neither the Browser pane nor
a background Chrome tab is ever visible in that sense; a foregrounded window on
the owner's own display is required. A real Chrome tab was tried and would not
even load the media (`readyState 0` indefinitely) while backgrounded.

**This does not weaken §2's conclusion.** Both strategies were measured
identically, the 45× gap is far outside any plausible measurement error, and the
component breakdown explains the mechanism rather than just reporting a total.
What is missing is the absolute number — "the cut takes N ms of black" — not the
choice between the two approaches.

**To close it:** re-run `spike/wo-124-playback/harness.html` in a foregrounded
browser window before WO-127 ships; the harness already detects rVFC and records
presentation gaps automatically when it fires.

---

## 8 · A platform constraint the Monitor must be built around

Discovered while fixing the measurement traps, and it outlives the spike:

- **`requestAnimationFrame` and `requestVideoFrameCallback` do not fire at all
  in a hidden page.**
- **`setInterval` / `setTimeout` are throttled to ~1 Hz** in the same state.
- **Media playback and media events keep running normally.**

**Consequence for the build.** The reel clock must be driven by media element
time, or by `performance.now()` sampled *on media events* — **never by an
animation frame or an interval.** A Monitor scheduler built on `rAF` works
perfectly on the desk and stalls the moment the user switches tab or hides the
window, which is exactly the kind of failure that survives every test and
appears only in real use.

---

## 9 · What this means for `SPEC.md` and ADP-003

**SO-3 is answered and the design survives.** §6's four questions have numbers:
two elements cross-swapped (§2), frame-accurate seeking at ~25 ms (§1),
`playbackRate` exact with the renderer at fault (§3), and a plain `<audio>` bed
that holds sync (§5).

**ADP-003 is unblocked on this axis.** SO-2 (the Log) and SO-4 (the rack
invariant) are also closed; ADP-003 is now drafted but not authorized.

**Three amendments `SPEC.md` §6 now warrants** — proposed here, an owner's to
accept. Each records something measured; none decides anything:

1. Record the **two-element cross-swap** as the specified mechanism, with the
   0.8 ms and 36.3 ms figures and the reason.
2. Record that **seeking is frame-accurate** and that the GOP is a latency
   consideration only.
3. State that **proxies must carry audio**, which §5 and §6 assume — landed in
   ingest by WO-116a, but not yet written into the spec that requires it.

> **A fourth was proposed here and is withdrawn.** It asked to amend §9's ±0.5 s
> QA tolerance, on the strength of the percentage this document first reported
> in §3. Re-measured 2026-07-29 across four clip lengths, the overshoot is a
> fixed 1–2 frames per ramped clip and `-t` removes it exactly. **§9 stands as
> written**, and the remedy is an ADP-002 §4 lane instruction for WO-121 and
> WO-122 rather than a spec change. Withdrawing it is the finding, not an
> oversight — see §3.4.
