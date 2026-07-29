# WO-124 · Playback engine — findings

**Status: MEASURED, 2026-07-28.** Closes `SPEC.md` §14 **SO-3**, subject to the
one limitation in §7. Run under [ADP-002](../implementation-plans/ADP-002-contract-v2-and-backend.md) §4.

Raw numbers: `spike/wo-124-playback/results.json`. The code that produced them is
throwaway and is deleted at ADP-002 closeout; **this document is what survives.**

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
the arithmetic duration, and the overshoot grows with rate:

| Rate | Expected | Rendered | Error |
|---|---|---|---|
| 1.5× | 8.000 s | 8.033 s | +0.42 % |
| 1.75× | 6.857 s | 6.900 s | +0.63 % |
| 2.0× | 6.000 s | 6.067 s | +1.11 % |
| 2.5× | 4.800 s | 4.867 s | +1.39 % *(chained `atempo`)* |

**This matters to a gate that already exists.** `SPEC.md` §9 requires QA to
check "duration within ±0.5 s of the computed reel length." At +1.11 %, a reel
with 45 s of 2.0× content overshoots by ~0.5 s **from this effect alone** — and
that is before any per-clip rounding. A speed-heavy reel can fail QA while
being, in every sense the user cares about, correct.

**Consequence for the build.** Two things, both cheap, and they belong to
different lanes:

- **WO-121** should compute expected duration from what ffmpeg will actually
  produce, not from `duration / rate`, or the renderer and the gate will
  disagree by construction.
- **WO-122** should either widen the tolerance for ramped reels or derive it
  from the ramp content. **This is a `SPEC.md` §9 question, so it is a
  stop-and-ask, not a lane decision** — the ±0.5 s is written down.

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

## 6 · Two things this spike found that nobody owns

Both remedies are in **`backend/ingest/`**, which ADP-002 §4 assigns to no Work
Order — the plan called ingest "survives", and against `SPEC.md` §3 the
*contract* does survive. Its **proxy recipe** does not.

| Finding | Remedy | Severity |
|---|---|---|
| Proxies are silent (`-an`) | Encode an AAC track | **Blocks §5 and §6 as written.** The Sound unit cannot do its job |
| 8.333 s keyframe interval | `-g 30` | Optimisation. Seeking is already correct; this only reduces a 45 ms worst case |

**Raised as a stop-and-ask, not absorbed.** The first is not optional if the
Sound unit is to be built as specified.

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

**ADP-003 is unblocked on this axis.** It still waits on SO-2 (the Log) and SO-4
(the rack invariant), which this spike says nothing about.

**Four amendments `SPEC.md` §6 now warrants** — proposed here, an owner's to
accept:

1. Record the two-element cross-swap as the specified mechanism, with the 0.8 ms
   and 36.3 ms figures and the reason.
2. Record that seeking is frame-accurate and that the GOP is a latency
   consideration only.
3. Add the renderer-vs-QA duration conflict from §3 to §9, which currently
   states a ±0.5 s tolerance that ramped reels can breach legitimately.
4. State that proxies **must** carry audio, which §5 and §6 assume and the
   current ingest contradicts.
