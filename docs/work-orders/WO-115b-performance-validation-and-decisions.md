# WO-115b · Performance validation and the decisions it depends on

**Status:** 📝 **Drafted — 2026-07-25. Not authorized.** Outside the approved M1 backlog and not covered by [ADP-001](../implementation-plans/ADP-001-m1-working-pipe-and-trim.md).
**Governing:** [ES-001](../specs/ES-001-manual-editor-core.md) §4, §9, §10, [ADR-002](../decisions/ADR-002-privacy-and-data-posture.md), [ADR-005](../decisions/ADR-005-editor-form-factor.md), [ADR-006](../decisions/ADR-006-incremental-staged-build.md), [ADR-010](../decisions/ADR-010-proposal-provenance-disposition.md), [ADR-012](../decisions/ADR-012-evidence-checkpoints.md)
**Pairs with:** [WO-115a](WO-115a-ingest-performance.md) — the autonomously completable ingest work.

Everything here needs the owner: a decision, real footage under a recorded consent, or both. **Nothing in this document may be executed on an agent's own judgment.**

---

> **✅ D-1 is fixed — 2026-07-28.** Owner authorized the fix; it landed as **WO-116**.
> `_content_rect` in [`opencv_analysis.py`](../../backend/analysis/opencv_analysis.py)
> crops the letterbox before measuring, derived from the source's rotation-corrected
> aspect ratio rather than detected from pixels — bar detection cannot distinguish a
> black bar from a genuinely dark frame, which is the case the signal exists to catch.
> Two regression tests guard it: measured **0.756 → 0.240** exposure on the landscape
> fixture, against a 0.50 ceiling, and proxy and original now agree within 0.10.
> **D-2 is therefore unblocked** — its equivalence baseline may now be captured.
> **Still open for the owner:** whether the proxy should stop letterboxing altogether
> (see below).

## Finding first: the proxy's letterbox is corrupting the exposure signal

Found while planning the analysis rework. **This is a correctness bug, not a performance item, and it is more important than anything else in either Work Order.**

`make_proxy` letterboxes every source into 540×960 ([`ffmpeg_ingest.py:151`](../../backend/ingest/ffmpeg_ingest.py)):

```
scale=540:960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2,setsar=1
```

A 1920×1080 landscape source scales to 540×304 and is padded to 540×960 — **68% of every frame is black bar.** `OpenCVAnalysis` then reads its video signals from that proxy ([`opencv_analysis.py:47`](../../backend/analysis/opencv_analysis.py)) and computes `exposure` as the fraction of pixels at or below 8 or at or above 247 ([`opencv_analysis.py:99`](../../backend/analysis/opencv_analysis.py)). The bars alone put `exposure` at roughly **0.68** on every second of every landscape clip.

The trim proposer's `exposure_ceiling` is **0.50** ([`trim_proposer.py:35`](../../backend/propose/trim_proposer.py)). So:

- **Every landscape clip fails the keep test on every second, before any real content is considered**, and is reported to the user as `OVEREXPOSED`.
- `blur` is depressed too — Laplacian variance over a frame that is two-thirds flat black — pushing landscape clips under `sharpness_floor` as well.
- Portrait sources scale to exactly 540×960 with no padding and are unaffected. **The bug is landscape-only**, which is why it reads as plausible behaviour rather than an obvious break.

**Why no test catches it.** The unit analysis tests call `probe_clip` and `analyze` without ever building a proxy, so `source.proxy_path` is `None` and analysis reads the *original* — the padded path is never exercised ([`test_analysis.py:33`](../../tests/analysis/test_analysis.py)). The exposure assertion that does exist is on a deliberately black *portrait* clip. The integration test *does* run the real path over a corpus containing a 1920×1080 clip, but §10.4 asserts only that a proposal carries *a* non-empty reason ([`test_full_flow_api.py:64`](../../tests/integration/test_full_flow_api.py)) — never that the reason is *right*. A confidently wrong `OVEREXPOSED` passes every gate in the suite.

**Decision needed.** The fix is straightforward — analyze unpadded content, either by cropping the bars back off before measuring or by deriving signals from the original rather than the proxy. But it **changes trim proposals on landscape footage**, which is product behaviour under ADR-006, so it is yours to call, not an agent's. It also touches ledger claim **C-03** (the trim heuristic is a helpful starting point): that claim has been resting on a proposer that mislabels an entire orientation.

**This should probably be its own Work Order and jump the queue ahead of both 115a and the rest of 115b.** Optimizing a pipeline that computes a wrong number is the wrong order of work.

---

## Owner decisions

### D-1 · The letterbox fix (above)

Fix it, and if so by cropping the proxy's bars before measurement or by analyzing the original. Both are cheap; they differ in what else they change. Blocks D-2.

### D-2 · Analysis in one pass

Extend the proxy ffmpeg invocation to emit, from the same decode, a small analysis mezzanine (128×128 grayscale at 4 fps, matching `AnalysisConfig`) and the 8 kHz mono PCM sidecar, so `OpenCVAnalysis` reads two small local files instead of decoding a full video and separately re-decoding the original's audio. Removes two full passes per clip.

**Sequenced after D-1**, because the mezzanine's framing is exactly what D-1 decides. Building it first would bake the letterbox in.

**Equivalence gate — specified, since an earlier draft left the tolerance undefined and an agent would have had to invent one.** Signals will not be bit-exact: ffmpeg's scaler is not `cv2.resize`, and the scaling order differs. Against a baseline captured *after* D-1 lands, on the WO-115a bench corpus:

| Quantity | Gate |
|---|---|
| `blur`, `exposure`, `shake`, `motion_energy`, `audio_rms` | max absolute per-sample delta **≤ 0.02**; mean absolute delta **≤ 0.005** (signals are normalised 0..1) |
| `scene_cuts_s` | every cut matches one in the other list within **±0.25 s** |
| An unmatched cut | acceptable **only** if that timestamp's `motion_energy` is within **0.02 of `cut_threshold`** — a genuine boundary flip. Any other unmatched cut **fails**. |
| Trim proposals over the corpus | `in_s`/`out_s` within **±0.1 s**; any larger difference must be traceable to a boundary-flip cut, or it **fails** |

`audio_rms` should be effectively unchanged — same 8 kHz mono extraction, just written to a file instead of a pipe. A delta there means something is wrong, not something is tolerable.

### D-3 · Optimistic UI state and the 409

WO-115a debounces mutations, which keeps today's await-then-render flow and removes most round trips. Going further — applying edits to React state immediately and persisting in the background — is faster still but is a **product decision**: it defines what the user sees when a background save fails, and whether their edit visibly reverts.

Coupled to it: rapid successive mutations can raise `ConflictError` → HTTP 409 from the store's optimistic-concurrency check ([`project_store.py:163`](../../backend/store/project_store.py)), which the UI currently surfaces as a raw error. Options, in increasing cost: leave the debounce to close the window; retry once by reloading and reapplying; or full optimistic state with a visible rollback affordance.

### D-4 · A 30 fps cap on proxies

Halves encode work on 60 fps sources. Excluded from WO-115a because it changes what the reviewer sees on high-frame-rate footage, and reviewing is the product. ES-001 §9 fixes geometry and bitrate but is silent on frame rate.

### D-5 · A sampled content hash

Substantially faster than anything in WO-115a Phase 2, but ES-001 §4 specifies "sha256 of bytes". Changing it changes every `source_id`, invalidating saved `project.json` files, proxies, and analysis caches — and M1 has no migrations by design ([`project_store.py:153`](../../backend/store/project_store.py)). Needs an ES-001 amendment **and** a migration answer. Recommend deferring: WO-115a's digest cache removes the repeat cost, which is most of the pain.

---

## The real-footage validation (ADR-012 **CP-3**)

**Gated on a recorded ADR-002 consent.** This is the only work that can move ledger claim **C-05** — "a local web app + local FFmpeg meets the ≤5-min proxy/analysis/render targets on the target Apple Silicon Mac" — off `assumed`.

Run `scripts/bench_ingest.py` (WO-115a Phase 0) over a real ~50-clip day and record, against the ES-001 §9 budgets:

| Budget | Measured | Verdict |
|---|---|---|
| Proxies ≤ ~5 min | | |
| Analysis + trim proposals ≤ ~5 min | | |
| Render ≤ ~5 min | | |
| Timeline scrub responsive on proxies | | |

Then update [`EVIDENCE-LEDGER.md`](../specs/EVIDENCE-LEDGER.md): **C-05** moves to `measured` or `refuted` — and `refuted` is a successful outcome that fires ES-001 §9's revision trigger, not a failure to argue around (ADR-006). This also overlaps the ES-001 §10.1 real-50-clip-day exit gate that WO-114 left owner-gated.

**Nothing recorded by WO-115a can substitute.** Its numbers come from `lavfi testsrc` — clean synthetic patterns with none of the sensor noise that dominates real encode cost, re-encoded by `libx264`/`libx265` rather than an iPhone's hardware encoder. Those runs establish direction and correctness, not magnitude.

---

## Recorded and closed: no database

Examined 2026-07-25 at the owner's question and rejected on the numbers. Recorded here so it is not re-litigated.

Storage today is two file-backed stores — `project.json` per project ([`project_store.py:134`](../../backend/store/project_store.py)) and one JSON file per source for analysis signals ([`analysis_store.py`](../../backend/analysis/analysis_store.py)). For the ES-001 §9 50-clip day that is an estimated 150–250 KB of project state and under ~500 KB of analysis: milliseconds, against a scan measured in minutes and bound by ffmpeg decode/encode over ~20 GB of source footage. **A storage engine cannot move the number ES-001 §9 measures.**

A networked document store (MongoDB and similar) would be slower here, not faster — its advantages are concurrent multi-client access over datasets that exceed memory, and this is one user, one process, sub-megabyte state, where in-process file reads beat IPC and BSON round trips. It would also add a daemon the user must install, against ADR-005's explicit rejection of packaging burden, and a second listening port outside the ADR-011 origin and capability-token guards.

**Where it could change:** SQLite becomes defensible if bounded proposal history (deferred to M2 by ADR-010) or cross-project queries arrive — in-process, single-file, zero-install, local-first preserved. A binary or columnar format for the *analysis* store becomes right if M2/M3 signals move from per-second to per-frame (~900 floats per clip today; ~27,000 then). Either is an ADR question, since ADR-005 and ES-001 §4.1 name `project.json` canonical.

---

## Gates

- **D-1 is resolved and landed before D-2 begins.** The equivalence baseline is captured after the letterbox decision, never before.
- **Every equivalence check in D-2 passes as specified above**, or the phase fails. A waived tolerance is a failed gate.
- **The real-footage run happens only after a recorded ADR-002 consent exists**, and no real footage, thumbnail, or derived artifact is ever committed (ADR-013, WO-113 fixtures guard).
- **C-05 is moved in the ledger** — to `measured` or `refuted` — with the run that moved it cited. A run that could not happen is recorded with its exact command and reason, never silently skipped.
- **Whatever D-3 decides is implemented with a failure path the user can see.** A silent background save failure is worse than the 409.

## Depends

[WO-115a](WO-115a-ingest-performance.md) (for `scripts/bench_ingest.py` and the bench corpus), WO-111 (analysis), WO-112 (proposer), WO-114 (the §10 gates this overlaps).

## Stop-and-ask

Everything in this document is one. Specifically: any real-media run before consent is recorded; any change to ES-001 §4 or §9; any change to `project.json` as canonical state; any commit or push (ADP-001 §3).
