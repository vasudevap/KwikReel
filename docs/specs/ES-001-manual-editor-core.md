# ES-001 — Manual editor core (M1–M3)

**Status:** Draft — owner approval required
**Governing:** [PROJECT.md](../../PROJECT.md) (Accepted), [ROADMAP.md](../../ROADMAP.md) (Accepted), [ADR-005](../decisions/ADR-005-editor-form-factor.md) (local web app; `project.json` canonical), [ADR-006](../decisions/ADR-006-incremental-staged-build.md) (staged build; approval gate; transparency), [ADR-002](../decisions/ADR-002-privacy-and-data-posture.md), [ADR-003](../decisions/ADR-003-music-and-licensing-posture.md). Component contracts elaborate [COMPONENT-DECOMPOSITION.md](COMPONENT-DECOMPOSITION.md).
**Covers:** ROADMAP milestones **M1, M2, M3** — the complete manual editor.
**Authorizes nothing.** Implementation requires an authorized ADP.

## 1 · Scope

Deliver a working, human-driven reel editor with **no AI assists**: import clips and a track, lay them on a timeline, hand-edit trim/speed/order, delete and restore, finalize a render cut to the music, and export with and without music — with the project saving and reloading losslessly.

| Milestone | Delivers | Components (per decomposition) |
|---|---|---|
| **M1** | Import & project spine | C-1 Ingest & Proxy, C-2 Project Store |
| **M2** | Timeline & manual edit | C-3 Timeline Editor (UI) |
| **M3** | Finalize & export | C-4 Renderer, C-5 Output QA, C-6 Exporter |

### Explicit exclusions

Not built here, even if convenient. Each is a **stop-and-ask**, not a judgment call:

- **No assists of any kind** — no trim proposer, speed proposer, or selection/ordering proposer (M4–M6).
- **No analysis** — no blur/exposure/shake/motion/scene-cut/duplicate detection, no beat detection, no saliency. `analysis.json` is not produced.
- **No people detection of any kind** in M1–M3. (Counting arrives with M4 analysis; identification never — ADR-002.)
- No filters, no multiple editorial styles, no publishing, no packaging/distribution, no cloud anything, no telemetry.

## 2 · Definition of Ready (met by this document)

Every cross-component interface and schema below is frozen; the technology stack is chosen; per-milestone validation gates are stated; exclusions are explicit; the two decisions requiring the owner are isolated in §10.

## 3 · Technology decisions

Within ADR-005's envelope (local web app + local FFmpeg backend). Proposed here for approval:

| Layer | Choice | Rationale |
|---|---|---|
| Backend | **Python 3.11+ / FastAPI**, bound to `127.0.0.1` | The M4–M6 assists are Python-native: **librosa** for beats is mandated by ADR-003, and blur/motion/scene analysis is OpenCV/numpy work. Choosing Python now avoids a language boundary later |
| Media | **FFmpeg / FFprobe** as subprocesses | ADR-005; no Python media bindings needed |
| Frontend | **React + TypeScript (Vite)** | Mature timeline/scrubbing ecosystem; preview via HTML5 `<video>` against proxies |
| Storage | **`project.json` on disk.** No database | v1 has one project open at a time; SQLite is deferred until it's justified |
| Assets | **All bundled locally** — no CDN, no remote fonts | Enforced as a build gate (§8) |

## 4 · Frozen schemas

**The schema freeze is the point of this ES.** `schema_version: 1` includes fields M1–M3 never populates — `origin`, `reasons`, `music.beats_s`, the assist entries in `stage_approvals` — **so that M4–M6 add data without a migration.** Populate progressively; do not extend.

### 4.1 · `project.json` (canonical state — ADR-005)

```jsonc
{
  "schema_version": 1,
  "project_id": "uuid",
  "created_at": "ISO-8601", "updated_at": "ISO-8601",
  "app_version": "0.1.0",

  "media_root": "/absolute/path — opened read-only, never written",
  "target_duration_s": 75,

  "music": {
    "track_ref": "/absolute/path to user-supplied local track (ADR-003)",
    "content_hash": "sha256",
    "duration_s": 191.4,
    "beats_s":  [],      // M5 — empty through M3
    "sections": []       // M5 — empty through M3
  },

  "sources": [ /* SourceIndex — see §4.2 — immutable facts */ ],

  "clips": [
    {
      "source_id": "…",
      "included": true,
      "order": 1,
      "deleted": false,              // recoverable; restore is always available
      "segments": [
        { "in_s": 3.0, "out_s": 8.0,
          "speed": [ { "from_s": 0.0, "to_s": 2.0, "rate": 2.0 } ] }
      ],
      "audio": { "retain": false, "gain_db": 0.0 },   // per-clip; always false in v1 (§7.2)
      "origin": {                    // provenance per field — "proposed" | "user"
        "included": "user", "order": "user",
        "segments": "user", "speed": "user", "audio": "user"
      },
      "reasons": []                  // ReasonRecord[] — empty through M3
    }
  ],

  "stage_approvals": {               // no stage advances without its entry
    "ingest":    "2026-07-24T19:02:11Z",
    "selection": null,               // M6
    "trim":      null,               // M4
    "speed":     null,               // M5
    "finalize":  null
  },

  "export": {
    "with_music": true, "without_music": true,
    "last_render": { "path": "…", "rendered_at": "…", "qa": { /* QAReport §7.3 */ } }
  }
}
```

**Invariants (enforced, not conventional):**
- `origin` is written on **every** field mutation. Through M3 every value is `"user"`.
- `deleted: true` never removes the clip object. Deletion is a flag; `segments` and `origin` survive so restore is exact.
- `order` is dense and unique across non-deleted clips.
- `media_root` and `sources[].path` are opened **read-only**; no code path writes or deletes under `media_root`.

### 4.2 · `SourceIndex` (immutable per-clip facts)

```jsonc
{
  "source_id": "opaque, stable",
  "content_hash": "sha256 of bytes — the reproducibility key",
  "path": "read-only absolute path",
  "duration_s": 12.4,
  "captured_at": "ISO-8601 with tz offset as recorded, or null",
  "orientation": "portrait|landscape",
  "codec": "hevc|h264|…", "fps": 30,
  "width": 1920, "height": 1080,
  "has_audio": true,
  "has_gps": true,          // presence flag only; coordinates never enter project.json
  "readable": true,         // false → surfaced to the user, never silently dropped
  "proxy_path": "derived; separate output directory"
}
```

### 4.3 · `ReasonRecord` (frozen now, first emitted at M4)

```jsonc
{ "code": "STABLE_MACHINE_CODE", "human_text": "plain-language explanation",
  "evidence_refs": ["signals.blur"], "score": 0.12, "confidence": "high|med|low" }
```

## 5 · HTTP contract

All endpoints local-only. JSON unless noted.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/project` | Create from `{media_root, track_ref, target_duration_s}` |
| `GET` | `/api/project/{id}` | Load full `project.json` |
| `PUT` | `/api/project/{id}` | Save. Optimistic concurrency on `updated_at`; mismatch → `409` |
| `POST` | `/api/project/{id}/approve/{stage}` | Record a stage approval (§6) |
| `POST` | `/api/import/{id}/scan` | Probe sources + generate proxies → async job |
| `GET` | `/api/jobs/{job_id}` | `{state, progress, error}` for scan/render/export |
| `GET` | `/api/media/proxy/{source_id}` | Serve proxy for preview (range requests) |
| `POST` | `/api/render/{id}/finalize` | Render the draft → async job |
| `GET` | `/api/render/{id}/draft` | Serve rendered draft |
| `POST` | `/api/export/{id}` | `{with_music: bool}` → async job |
| `GET` | `/api/export/{id}/download/{variant}` | Serve final file |

Errors: `{error_code, human_text, remediation}` — surfaced to the user, never swallowed.

## 6 · Stage approval mechanics (ADR-006)

The approval gatekeeper is a real component, not a UI convention.

- A stage's work may not run until the **prior** stage has a non-null `stage_approvals` timestamp.
- Through M1–M3 the live gates are **`ingest`** and **`finalize`**; `selection`/`trim`/`speed` stay `null` and are inert.
- **Any user edit to a clip invalidates `finalize`** (reset to `null`), forcing a re-approval before re-render. Approving a render you then edited is exactly the drift ADR-006 guards against.
- Approvals are timestamps in `project.json`, so they survive save/reload and are auditable.

## 7 · Render and export

### 7.1 · Pipeline
Build an FFmpeg `filter_complex` per included, non-deleted clip in `order`:
1. Trim to `segments[].in_s/out_s`.
2. Apply speed: `setpts` per speed range. **Clip audio is dropped at this stage in v1** (§7.2), so no `atempo` chain is required. Constant-rate segments are the v1 norm; ramps are piecewise-constant sub-ranges, not interpolated curves.
3. Scale/crop to **1080×1920**, centre-crop in v1 (saliency-driven reframing is deferred to the assist milestones).
4. Concat, then mux audio per §7.2.

### 7.2 · Audio variants

**Clip audio is not carried in v1.** Speed ramping makes it unusable: at 4× speech is unintelligible and ambience becomes a chirp; at 0.5× everything drones. `atempo` preserves pitch but still yields artefact rather than sound. Concatenating audio across clips recorded in different places compounds this with an abrupt ambience jump at every cut.

- **`with_music`** — the user's track is the bed; clip audio muted.
- **`without_music`** — **silent.** Video only, muxed with a **silent AAC track** rather than no audio stream at all, since some platforms mishandle audio-less uploads.
- Music loudness normalised to a single target.

Retaining audio on a *specific* clip is a real editorial choice — a kid's first words, someone singing — and it only makes sense on an unspeeded (rate 1.0) segment. That is a **per-clip user decision, not an export-time guess.** `clips[].audio` is frozen into schema v1 now and exposed in a later milestone with its own UI and ducking; v1 always writes `retain: false`.

### 7.3 · Output QA (gate, blocks export)
`QAReport` must pass: not black (sampled-frame luma above floor) · **audio matches the variant's expectation** — `with_music` must not be silent, while `without_music` must *be* silent and still carry a valid silent track (a naive not-silent check would wrongly fail it) · duration within **±0.5 s** of the timeline sum · resolution exactly 1080×1920 · H.264/AAC · safe-title margins respected · frame count non-zero. Any failure blocks export and is surfaced with its reason.

## 8 · Non-functional requirements

| Area | Requirement |
|---|---|
| **Privacy / egress** | Backend binds `127.0.0.1` only. **No outbound network from the media path.** Frontend ships zero remote assets. Enforced by a dependency/asset audit as a build gate |
| **Originals** | Opened read-only. No write, move, or delete path exists under `media_root` — verified by test |
| **Repo hygiene** | `project.json` embeds absolute paths to private media: **add `*.project.json`, proxy and render output dirs to `.gitignore`.** Never commit a project file |
| **Performance (50-clip day, Apple Silicon)** | Proxy generation ≤ ~5 min · timeline scrub responsive against proxies · final render ≤ ~5 min |
| **Proxies** | 540×960 H.264, ~1.5 Mbps, `+faststart`, in a separate derived directory |
| **Failure honesty** | Unreadable/corrupt sources are reported with a reason and retained in `sources` with `readable: false` — never silently dropped |

## 9 · Validation gates

| Milestone | Must pass |
|---|---|
| **M1** | Import a real folder + track; every source probed or reported unreadable; proxies play; **save → reopen → byte-equivalent `project.json`** (round-trip test is a build gate); no writes under `media_root` |
| **M2** | Set trim in/out; set speed; reorder; delete; **restore a deleted clip to its exact prior state**; all mutations write `origin`; reload preserves every edit |
| **M3** | Finalize renders a playable draft cut to the track; QA gate catches a deliberately black/silent/truncated render; both export variants produced; duration within ±0.5 s; editing after approval resets `finalize` to `null` |

Owner approval on **real footage** is the acceptance gate for each (ADR-006). Owner approval is a build gate, **not** evidence of product quality — that requires M3.5's real users.

## 10 · Decisions (resolved 2026-07-23)

**A. Segment model — `segments[]` adopted.** The schema permits multiple segments per clip; the **v1 UI enforces exactly one**. This future-proofs the single change that would otherwise break the frozen schema — wanting two moments out of one clip — and avoids a migration across every saved project.

**B. "Without music" exports silent — clip audio stripped.** Owner-directed, overriding the original recommendation to retain it. Carrying original audio through a speed-ramped, multi-clip concatenation produces artefact rather than sound (§7.2), so it is dropped rather than mangled. Per-clip audio retention survives as a deliberate later feature, with `clips[].audio` frozen into schema v1 now so adding it needs no migration.

## 11 · Open / deferred

- **Per-clip audio retention and ducking** (`clips[].audio`, §7.2) — a later milestone with its own UI, only meaningful on rate-1.0 segments.
- Multi-project management, undo-history beyond delete/restore, saliency reframing, true speed *curves* (v1 is piecewise-constant), packaging and distribution.
- **TBD:** minimum supported macOS/Apple Silicon target; FFmpeg distribution (system vs. bundled — a licensing question under ADR-003).
