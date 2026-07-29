# WO-115a · Ingest performance — autonomously completable

> **⚠️ STALE — drafted against the pre-v3z product (2026-07-25), kept as raw
> material.** Its governing documents (ES-001, the ADRs) were archived in the
> 2026-07-28 clean cut and are no longer citable; several links below point at
> their pre-archive locations and no longer resolve; some cited code paths were
> deleted with the old frontend. **Absorbed into WO-135** — ADP-004's
> real-footage lane, not yet drafted or authorized (ADP-002 §4, *Not in this
> ADP*). Read it as input to WO-135; take no requirement from it.

**Status:** 📝 **Drafted — 2026-07-25. Not authorized.** Outside the approved M1 backlog (WO-100–114) and not covered by [ADP-001](../implementation-plans/ADP-001-m1-working-pipe-and-trim.md). Needs owner authorization before any code.
**Governing:** [ES-001](../specs/ES-001-manual-editor-core.md) §4 (SourceIndex), §9 (non-functional requirements), [ADR-005](../decisions/ADR-005-editor-form-factor.md), [ADR-006](../decisions/ADR-006-incremental-staged-build.md), [ADR-011](../decisions/ADR-011-local-delivery-security.md), [ADR-012](../decisions/ADR-012-evidence-checkpoints.md)
**Pairs with:** [WO-115b](WO-115b-performance-validation-and-decisions.md) — everything in this area that needs the owner.
**Origin:** the "noted during the real-footage review, not yet actioned" item in [handoff.md](../../handoff.md).

## What this Work Order can and cannot claim

**It can claim:** each change works, is guarded, and moves the measured number in the right direction on a synthetic corpus.

**It cannot claim** that ES-001 §9's budgets are met. Those budgets are defined on *a real 50-clip day*, which is gated on an ADR-002 consent record. Ledger claim **C-05** ("a local web app + local FFmpeg meets the ≤5-min proxy/analysis/render targets") stays graded **`assumed`** at the end of this WO. Moving it is [WO-115b](WO-115b-performance-validation-and-decisions.md)'s job, via the ADR-012 **CP-3** perf spike.

**The synthetic corpus is not a proxy for real footage.** `tests/synthetic.py` generates clips from ffmpeg's `lavfi testsrc` — a clean, deterministic pattern with none of the sensor noise or grain that dominates real camera encode cost, re-encoded here by `libx264`/`libx265` rather than an iPhone's hardware encoder. **Speedup ratios measured on it bound nothing about real footage.** They establish direction and correctness, not magnitude. Every number this WO writes to the ledger must carry that caveat in its Notes column.

## Why

A scan makes three separate full passes over every original, all serial:

| Cost | Where | Why it is slow |
|---|---|---|
| Full-file SHA-256 | [`ffmpeg_ingest.py:110`](../../backend/ingest/ffmpeg_ingest.py) | Reads every byte of every clip; re-run on every scan, never cached. `_unreadable` hashes a second time. |
| Proxy transcode | [`ffmpeg_ingest.py:155`](../../backend/ingest/ffmpeg_ingest.py) | `libx264` at its default `medium` preset, software decode, **no cache check** — an existing valid proxy is rebuilt from scratch. |
| Scan loop | [`app.py:206`](../../backend/api/app.py) | `for i, s in enumerate(sources)` — one clip at a time, one core. |
| Timeline mutation | [`App.tsx:59`](../../frontend/src/app/App.tsx) → [`project_store.py:162`](../../backend/store/project_store.py) | Every UI edit PUTs the whole project; `save()` then re-reads the prior file, validates, deep-copies and re-serializes it. |

`h264_videotoolbox` and `hevc_videotoolbox` are present on the development Mac (`ffmpeg -encoders`, 2026-07-25).

## Phase 0 · Baseline — runs first, alone

`scripts/bench_ingest.py`: times probe / hash / proxy / analysis per clip over a media directory, plus a whole-scan total, and emits a JSON record so runs are comparable.

**Bench corpus — specified, because the existing one is far too small to measure with.** `tests/synthetic.py::make_corpus` produces three clips of 2–3 s; that exercises the gates, not the clock. Phase 0 adds `make_bench_corpus(root, scale)` built from the same `make_clip` primitive:

| Group | Count | Size | Codec | fps | Duration | Audio |
|---|---|---|---|---|---|---|
| portrait HD | 20 | 1080×1920 | h264 | 30 | 20 s | yes |
| portrait 4K | 15 | 2160×3840 | hevc | 30 | 20 s | yes |
| landscape 4K | 10 | 3840×2160 | hevc | 60 | 15 s | yes |
| portrait HD, silent | 4 | 1080×1920 | h264 | 30 | 20 s | no |
| unreadable | 1 | — | — | — | — | — |

50 files, ~17 minutes of footage — the shape of the ES-001 §9 day, at synthetic fidelity. Generation is itself slow (libx265 at 4K), so it is built once into a **gitignored** directory and reused; `--rebuild` forces regeneration. It is never committed — ADR-013 and the WO-113 fixtures guard both apply, and nothing here contains a person.

Phase 0 also records the **project-save round trip**: time a `PUT /api/project/{id}` for a 50-clip project, p50 and p95. Phase 5's debounce interval is derived from this measurement, not asserted.

**Nothing else starts until Phase 0 has produced a baseline record.**

## Phase 1 · Proxy build

Four independently landable, independently revertable changes to `FFmpegIngest.make_proxy` and the `scan` job:

1. **Cache.** Return early if `<proxy_root>/<source_id>.mp4` exists. `source_id` derives from the content hash, so an existing proxy is provably the proxy for those bytes. Re-scan drops to near zero.
2. **Hardware encode.** `h264_videotoolbox` at `-b:v 1.5M`, selected by a one-time cached capability probe, falling back to `libx264 -preset veryfast` where VideoToolbox is absent. ES-001 §9 fixes the proxy *output* — 540×960 H.264, ~1.5 Mbps, `+faststart` — not the encoder, so this is within spec.
3. **Hardware decode.** `-hwaccel videotoolbox` ahead of `-i`.
4. **Parallel scan.** A bounded `ThreadPoolExecutor` in the `scan` job with a lock-guarded completion counter driving `progress()`. Subprocess work releases the GIL, so threads are correct.

**The worker count is measured, not asserted.** Sweep 1 / 2 / 4 / 8 / `os.cpu_count()` over the bench corpus, record every result, and take the knee. If the sweep is inconclusive, default to `min(4, max(2, (os.cpu_count() or 4) // 2))` and say so. *(An earlier draft asserted a VideoToolbox concurrent-encode-session limit as the reason for the cap. That was never verified and is withdrawn — the sweep is the arbiter.)*

## Phase 2 · Hashing — mechanical items only

ES-001 §4 pins `content_hash` to "sha256 of bytes". **The algorithm does not change here.** What does:

- Hash each file exactly once per scan (remove the second hash in `_unreadable`).
- Hash in parallel with the proxy pool — this is I/O-bound.
- Raise `_CHUNK` from 1 MiB to 8 MiB.
- Cache the digest in the derived directory, keyed on `(path, size, mtime, inode)`.

## Phase 3 · Browser load

- `Cache-Control: public, max-age=31536000, immutable` on `/api/media/proxy/{source_id}` in `_serve` ([`app.py:153`](../../backend/api/app.py)) — safe because the id is content-addressed. Draft and export responses stay `no-cache`; they change under a stable URL.
- `preload="metadata"` on the always-mounted `<video>` in [`Timeline.tsx:42`](../../frontend/src/timeline/Timeline.tsx). `TrimReview` already mounts its preview lazily behind `previewing` and needs no change.

## Phase 4 · Store and save-path

1. **In-memory prior-`Project` cache** in `FileProjectStore`, keyed on `updated_at`, removing one full disk read + parse + validate per save ([`project_store.py:162`](../../backend/store/project_store.py)). A cache miss falls back to disk; concurrency semantics must be provably identical, which the existing store tests already assert.
2. **`fsync` before `os.replace`** in `_atomic_write`. A durability gap rather than a speed one, but it lives in the same function.
3. **Debounce and coalesce mutations** in `App.tsx`'s `mutate` — trailing-edge, so the last value in a burst wins. The trim `in`/`out` number inputs ([`TrimReview.tsx:100`](../../frontend/src/trim/TrimReview.tsx)) currently fire one full round trip per keystroke. **Interval = the p95 save round trip measured in Phase 0, clamped to [100 ms, 400 ms]**, recorded with the measurement that produced it.

Debouncing alone keeps the existing await-then-render flow — the UI still shows server-confirmed state. Optimistic local rendering, and the 409 that rapid mutation can raise, are **WO-115b**: both change what the user sees when a save fails, which is a product decision.

## File scope

`scripts/`, `tests/synthetic.py` (additive: `make_bench_corpus`), `backend/ingest/`, `backend/api/app.py` (scan loop + `_serve` headers only), `backend/store/project_store.py`, `frontend/src/app/App.tsx`, `frontend/src/timeline/Timeline.tsx`, `tests/ingest/`, `tests/store/`, `docs/specs/EVIDENCE-LEDGER.md`, `.gitignore`

## Excludes

- Any change to the ES-001 §4 schemas, the HTTP contract, or `content_hash`'s algorithm.
- Any change to proxy geometry, bitrate, or frame rate (ES-001 §9).
- `backend/analysis/` — the single-pass rework is WO-115b Phase 1.
- Optimistic UI state and 409 handling — WO-115b.
- Real-frame thumbnails or posters (an ADR-013 decision, not a performance item).
- Render and export performance — a separate ES-001 §9 budget.
- Adding a database. Examined and rejected on the numbers; the reasoning is recorded in WO-115b.
- New dependencies. Manifests are WO-101's alone.

## Gates

- **A Phase 0 baseline record exists before any optimization lands**, and a before/after record for each phase is written to [`EVIDENCE-LEDGER.md`](../specs/EVIDENCE-LEDGER.md) **carrying the synthetic-corpus caveat**.
- **The encoder fallback is proven**, not assumed: a test forces the no-VideoToolbox path and the proxy still builds to the ES-001 §9 output spec. This must not silently become macOS-only.
- **The proxy cache is proven correct**: changing a source's bytes changes its `source_id` and therefore produces a new proxy; an unchanged source reuses one. A stale-proxy failure mode is the one way this phase can be quietly wrong.
- **The WO-113 read-only guard still passes**: nothing is created, modified, moved, or deleted beneath `media_root`. Hash caches and derived artifacts write only to derived roots.
- **The bench corpus is untracked** — the WO-113 fixtures guard must still pass.
- **The full existing suite stays green** (67 passed / 1 owner-gated skip at drafting) and the frontend typechecks and builds clean.
- **The worker count and the debounce interval are each traceable to a recorded measurement**, not to a number in this document.
- Every check that could not run is recorded with its exact command and the reason.

## Depends

WO-102 (ingest), WO-103 (store), WO-106 (API), WO-107/108/110 (frontend) — all complete.

## Stop-and-ask

- **A sampled (head/tail) content hash** — faster than anything in Phase 2, but ES-001 §4 says "sha256 of bytes" and changing it invalidates every saved `source_id`, proxy, and analysis cache. Deferred to WO-115b as a spec question.
- **Any new runtime dependency.** Manifests are WO-101's alone.
- **Benchmarking against real footage** before an ADR-002 consent record exists. Phase 0 runs on synthetic only.
- **Committing or pushing.** ADP-001 §3 keeps each push a separate owner decision.
- If the Phase 0 baseline shows the *synthetic* scan is already far inside budget in a way that makes the whole exercise moot, **stop and report** rather than optimizing to no purpose (ADR-006). Note this is weak evidence either way — see the caveat at the top.
