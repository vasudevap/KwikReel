# ES-001 — M1: working pipe + AI trim

**Status:** **Accepted — owner-approved 2026-07-23.** Definition of Ready met; contracts frozen.
**Amendment expected:** per [ADR-008](../decisions/ADR-008-prototype-before-contract-freeze.md), the WO-100 prototype runs before any schema becomes code and produces a list of gaps in §4. Whatever it finds is amended here **before WO-101 starts.** Treat §4 as frozen pending that check.
**Amended 2026-07-24 (pre-ADP course correction):** manual curation added to M1 (ADR-009 → §1, §5.5, §10); proposal `disposition` added (ADR-010 → §4.1, §5.3); local delivery security specified (ADR-011 → §9); prototype thumbnails reconciled with ADR-002 (ADR-013 → WO-100 in the backlog); audio expanded to three modes — `music`/`clip`/`silent`, adding natural clip audio in M1 (§8.1–8.3, §4.1 export, §6, §10–12), per-clip ducking under music still deferred. These are recorded amendments to an Accepted spec (ADR-008), visible in history — not quiet edits.
**Governing:** [PROJECT.md](../../PROJECT.md), [ROADMAP.md](../../ROADMAP.md), [ADR-005](../decisions/ADR-005-editor-form-factor.md) (local web app; `project.json` canonical), [ADR-006](../decisions/ADR-006-incremental-staged-build.md) (approval gate; transparency), [ADR-007](../decisions/ADR-007-build-sequencing.md) (AI trim in M1; pairing rule), [ADR-009](../decisions/ADR-009-manual-curation-in-m1.md) (manual curation in M1), [ADR-010](../decisions/ADR-010-proposal-provenance-disposition.md) (proposal `disposition`), [ADR-011](../decisions/ADR-011-local-delivery-security.md) (local delivery security), [ADR-013](../decisions/ADR-013-prototype-thumbnails-consent.md) (prototype thumbnails), [ADR-002](../decisions/ADR-002-privacy-and-data-posture.md), [ADR-003](../decisions/ADR-003-music-and-licensing-posture.md). Contracts elaborate [COMPONENT-DECOMPOSITION.md](COMPONENT-DECOMPOSITION.md).
**Covers:** ROADMAP milestone **M1** only.
**Authorizes nothing.** Implementation requires an authorized ADP.

## 1 · Scope

Import a folder of clips and a music track, **curate the day by hand** (include/exclude, delete, restore), **have the AI propose a trim for every included clip with a visible reason**, adjust or remove any suggestion, lay the result on a timeline, render, and export in three audio modes (music, natural clip audio, or silent) — with the project saving and reloading losslessly.

| Component | Role |
|---|---|
| C-1 Ingest & Proxy | Probe sources, generate preview proxies |
| C-2 Project Store | `project.json` save/load, lossless round-trip |
| C-7 Per-clip Analysis | Quality signals for trim (§5.1) |
| C-8 Trim Proposer | Proposes in/out per clip, with reasons |
| C-3 Timeline Editor (UI) | Timeline, **manual curation (include/exclude/delete/restore)**, trim controls, proposal review, approval |
| C-4/5/6 Renderer, QA, Exporter | Draft render, QA gate, three audio-mode exports |

### Explicit exclusions

Not built here, even if convenient. Each is a **stop-and-ask**:

- **No selection or ordering *assist*** (M2 proposer). **Manual curation is in M1** (§5.5): the user includes/excludes, deletes, and restores clips by hand; nothing *proposes* inclusion or order. Clip order is the user's, defaulting per §5.4.
- **No speed assist** (M3). Speed is settable manually; nothing proposes it.
- **No people detection of any kind in M1.** Counting arrives with the M2 selection assist; identification never (ADR-002).
- No filters, editorial styles, publishing, cloud anything, telemetry, or packaging.

## 2 · Definition of Ready

Every cross-component interface and schema below is frozen; the technology stack is chosen; the trim proposer's signals, rules, and thresholds are specified; validation gates including the internal checkpoint are stated; exclusions are explicit.

## 3 · Technology

Within ADR-005's envelope (local web app + local FFmpeg backend):

| Layer | Choice | Rationale |
|---|---|---|
| Backend | **Python 3.11+ / FastAPI**, bound to `127.0.0.1` | M1's analysis is OpenCV/numpy work and M3's beats need **librosa** (ADR-003). Python from the start avoids a language boundary later |
| Media | **FFmpeg / FFprobe** subprocesses | ADR-005 |
| Analysis | **OpenCV + numpy** | Blur, exposure, motion, scene cuts, perceptual hashing |
| Frontend | **React + TypeScript (Vite)** | Timeline/scrubbing ecosystem; preview via HTML5 `<video>` on proxies |
| Storage | **`project.json` on disk.** No database | One project open at a time |
| Assets | **All bundled locally** — no CDN, no remote fonts | Build gate (§9) |

## 4 · Frozen schemas

`schema_version: 1` carries fields M1 never writes — `included`/`order` proposals, `speed`, `music.beats_s` — **so M2 and M3 add data without a migration.**

### 4.1 · `project.json`

```jsonc
{
  "schema_version": 1,
  "project_id": "uuid",
  "created_at": "ISO-8601", "updated_at": "ISO-8601",
  "app_version": "0.1.0",

  "media_root": "/absolute/path — opened read-only, never written",
  "target_duration_s": 75,               // M1: displayed reference only (running total vs target); no optimizer

  "music": {
    "track_ref": "/absolute/path to user-supplied local track (ADR-003)",
    "content_hash": "sha256", "duration_s": 191.4,
    "beats_s": [], "sections": []        // M3 — empty in M1
  },

  "sources": [ /* SourceIndex — §4.2 — immutable facts */ ],

  "clips": [
    {
      "source_id": "…",
      "included": true,
      "order": 1,
      "deleted": false,
      "segments": [                       // effective value — what renders
        { "in_s": 3.0, "out_s": 8.0,
          "speed": [ { "from_s": 0.0, "to_s": 2.0, "rate": 1.0 } ] }
      ],
      "audio": { "retain": false, "gain_db": 0.0 },   // always false in v1 (§8.2)

      "origin": {                         // did the effective value come from machine or human?
        "included": "user", "order": "user",
        "segments": "proposed|user", "speed": "user", "audio": "user"
      },

      "proposals": {                      // what the AI last proposed — RETAINED after override
        "segments": { "value": [ /* … */ ], "at": "ISO-8601",
                      "reasons": [ /* ReasonRecord */ ],
                      "disposition": "pending|accepted|adjusted|dismissed" },  // ADR-010: user's terminal action
        "included": null,                 // M2
        "order":    null,                 // M2
        "speed":    null                  // M3
      }
    }
  ],

  "stage_approvals": {
    "ingest":    "2026-07-24T19:02:11Z",
    "trim":      null,                    // LIVE in M1
    "selection": null,                    // M2 — inert
    "speed":     null,                    // M3 — inert
    "finalize":  null
  },

  "export": {
    "audio_modes": ["music", "clip", "silent"],   // modes the user has chosen to export (was with_music/without_music)
    "last_render": { "path": "…", "audio_mode": "music", "rendered_at": "…", "qa": { /* QAReport §8.3 */ } }
  }
}
```

**Why `proposals` exists — and why it is not optional.** `origin` records *whether* a value came from the machine; it does not record *what the machine said.* Without retaining the proposal, an override destroys the only evidence of what was proposed — and "proposals kept versus discarded" is the evidence that fires ADR-006's *assists-earn-their-place* trigger. Keeping `proposals` makes that trigger measurable as a query over saved projects rather than a study.

**Why `disposition`, not just `origin` (ADR-010).** `origin` is binary (`proposed|user`) and distinguishes only two of the five proposal states — it cannot separate a minor accepted adjustment from a total override, nor a dismissal from an adjust-to-full-clip. `disposition` records the user's **terminal action**: `pending` (not yet acted on; promoted to `accepted` when the stage is approved), `accepted`, `adjusted`, or `dismissed`. The assists-earn-their-place metric reads `disposition` at the trim-stage approval snapshot — `accepted` and `adjusted-within-tolerance` count as **kept**, `dismissed` and `adjusted-beyond-tolerance` as **not kept** (tolerance is a config/UI value, not pre-registered). Proposal *history* across re-runs is **bounded and deferred to M2**; M1 keeps only the latest proposal per field plus its `disposition`, so nothing grows without bound inside the gitignored project file.

**Invariants (enforced, not conventional):**
- Every field mutation writes `origin`. A machine write sets `"proposed"`; any user edit sets `"user"`.
- Writing a proposal **never** overwrites a field whose `origin` is `"user"` unless the user explicitly re-runs the assist for that clip.
- `deleted: true` never removes the clip object — deletion is a flag, so restore is exact.
- `order` is dense and unique across non-deleted clips.
- `media_root` and `sources[].path` are opened **read-only**; no code path writes or deletes beneath `media_root`.
- Every proposal carries a `disposition`; a user adjust sets `adjusted`, a remove-suggestion sets `dismissed`, approving the stage over an untouched proposal sets `accepted`, and an explicit re-run resets it to `pending`.

### 4.2 · `SourceIndex` (immutable facts)

```jsonc
{ "source_id": "opaque, stable", "content_hash": "sha256 of bytes",
  "path": "read-only absolute path", "duration_s": 12.4,
  "captured_at": "ISO-8601 with tz offset, or null",
  "orientation": "portrait|landscape", "codec": "hevc|h264|…", "fps": 30,
  "width": 1920, "height": 1080, "has_audio": true,
  "has_gps": true,        // presence flag only; coordinates never enter project.json
  "readable": true,       // false → surfaced to the user, never silently dropped
  "proxy_path": "derived; separate output directory" }
```

### 4.3 · `analysis.json` (facts, not decisions)

Shape frozen; M1 populates only the trim-relevant signals.

```jsonc
{ "source_id": "…",
  "signals": {
    "blur": [ /* per-second sharpness, Laplacian variance */ ],
    "exposure": [ /* per-second clipping score */ ],
    "shake": [ /* per-second frame-to-frame instability */ ],
    "motion_energy": [ /* per-second */ ],
    "audio_rms": [ /* per-second */ ],
    "people_count": null,        // M2 — COUNT ONLY when it arrives; identity never
    "saliency_ref": null         // deferred
  },
  "scene_cuts_s": [ 2.1, 7.8 ],
  "dup_group": "cluster-7",      // perceptual-hash cluster across clips
  "run_id": "…" }
```

### 4.4 · `ReasonRecord` (the transparency primitive)

```jsonc
{ "code": "LEADING_BLUR",                         // machine-readable, stable
  "human_text": "Trimmed the first 2.4 s — too blurry to keep (sharpness 0.12 vs 0.35 floor)",
  "evidence_refs": ["signals.blur[0:2]"],         // MUST cite what actually drove it
  "score": 0.12, "confidence": "high|med|low" }
```

## 5 · The trim assist

### 5.1 · Signals (C-7)
Per-second, from proxies: **sharpness** (Laplacian variance), **exposure** clipping, **shake** (frame-to-frame displacement), **motion energy**, **audio RMS**, plus per-clip **scene cuts** and cross-clip **perceptual-hash duplicate groups**.

### 5.2 · Proposal rules (C-8) — deterministic and legible
1. Score each second against quality floors (sharpness, exposure, shake).
2. Choose the **longest contiguous window** clearing the floors.
3. Trim leading/trailing spans that are blurry, shaky, badly exposed, or **static** (low motion *and* low audio RMS — the dead air at the head and tail of most phone clips).
4. Do not propose a window crossing a scene cut; if a clip contains multiple shots, propose the best single shot.
5. Enforce a **minimum window of 1.0 s**. If nothing clears the floors, **propose the full clip and say so** — never emit an empty or silent result.
6. Emit one `ReasonRecord` per contributing factor, citing the actual signal range.

Thresholds live in config, are surfaced in the UI, and are **not** pre-registered — ADR-006 retired that regime. Tuning them is normal work, not drift.

### 5.3 · Controls (C-3) — the pairing rule, ADR-007
- **Per-clip "AI trim"** button, and a **"Trim all"** bulk action.
- **Adjust** — drag in/out handles; sets `origin.segments = "user"`, `proposals.segments.disposition = "adjusted"`, retains `proposals.segments`.
- **Remove suggestion** — reverts to the full clip; sets `origin.segments = "user"`, `proposals.segments.disposition = "dismissed"`, retains `proposals.segments`.
- **Accept** — approving the trim stage promotes every untouched (`pending`) proposal to `disposition = "accepted"`; `origin.segments` stays `"proposed"`.
- **Re-run** per clip, explicitly, which is the only way a machine write may overwrite a `"user"` value; it writes a fresh proposal with `disposition = "pending"`.
- Every proposal displays its `human_text` inline. **A proposal with no readable reason is a bug, not a cosmetic gap** (ADR-006).

### 5.4 · Default clip order
**Capture time (`captured_at`) ascending; folder order as fallback** where timestamps are missing or identical. Order is always user-editable.

### 5.5 · Manual curation (ADR-009)
The user curates the day by hand in M1 — **no assist proposes inclusion or order.**
- **Include / exclude** — toggles `included`; excluded clips do not render and are not deleted. Sets `origin.included = "user"`.
- **Delete / restore** — `deleted` is a flag; the clip object is retained so restore is exact (§4.1 invariant). In M1, deletion is always a user action (no machine writer).
- **Reorder** — user-set `order`; dense and unique across non-deleted clips.
- The timeline displays the **running total duration against `target_duration_s`** as a reference; there is no optimizer and no enforcement.
- `proposals.included` and `proposals.order` stay `null` in M1; the M2 selection/order assist writes them and is overridden by these same controls — the pairing rule (the controls exist first; the assist proposes into them).

## 6 · HTTP contract

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/project` | Create from `{media_root, track_ref, target_duration_s}` |
| `GET` | `/api/project/{id}` | Load full `project.json` |
| `PUT` | `/api/project/{id}` | Save. Optimistic concurrency on `updated_at`; mismatch → `409` |
| `POST` | `/api/project/{id}/approve/{stage}` | Record a stage approval (§7) |
| `POST` | `/api/import/{id}/scan` | Probe sources + build proxies → async job |
| `POST` | `/api/analyze/{id}` | Compute `analysis.json` → async job |
| `POST` | `/api/propose/trim/{id}` | Body `{source_ids?: []}` — omit for all. Writes `proposals.segments` |
| `GET` | `/api/jobs/{job_id}` | `{state, progress, error}` |
| `GET` | `/api/media/proxy/{source_id}` | Serve proxy (range requests) |
| `POST` | `/api/render/{id}/finalize` | Render draft → async job |
| `GET` | `/api/render/{id}/draft` | Serve draft |
| `POST` | `/api/export/{id}` | `{audio_mode: "music"\|"clip"\|"silent"}` → async job |
| `GET` | `/api/export/{id}/download/{audio_mode}` | Serve final file for that mode |

Errors return `{error_code, human_text, remediation}` — surfaced, never swallowed.

## 7 · Stage approval mechanics (ADR-006)

- A stage may not run until the prior stage has a non-null `stage_approvals` entry.
- **Live in M1:** `ingest`, `trim`, `finalize`. `selection` and `speed` remain `null` and inert. Manual curation (§5.5) is part of user-driven editing and adds **no** gate; the `selection` approval records approval of the *M2 assist*, not of manual curation.
- **Any clip edit invalidates `finalize`** (reset to `null`), forcing re-approval before re-render. Approving a render you then edited is the drift ADR-006 guards against.
- Approvals are timestamps in `project.json`, so they survive reload and are auditable.

## 8 · Render and export

### 8.1 · Pipeline
Per included, non-deleted clip in `order`: trim to `segments[].in_s/out_s` → apply `setpts` per speed range (all `1.0` in M1) → scale/crop to **1080×1920**, centre-crop → concat → mux audio per §8.2. **For `clip` mode**, the concatenated clip audio is muxed (rate-1.0, so no time-stretch), inserting a matched **silent pad for any `has_audio:false` clip** to keep streams aligned, then a single loudness-normalisation pass. **For `music`**, the track is the bed; **for `silent`**, a valid silent AAC track.

### 8.2 · Audio modes (amended 2026-07-24)

M1 exports one of three **global audio modes**, chosen at export. Nothing is muted un-overridably — the user directs the soundtrack.

- **`music`** — the user's supplied track is the bed; clip audio is not mixed in. Loudness normalised to a single target.
- **`clip`** — the reel carries the **natural audio of the clips themselves**, concatenated in order, no music. A single loudness-normalisation pass is applied; per-clip level jumps at cuts are an accepted characteristic of this mode, not a defect. Clips with no audio (`SourceIndex.has_audio == false`) contribute a matched **silent pad** so the concatenation stays in sync.
- **`silent`** — no audio, muxed with a valid **silent AAC track** (for users adding an Instagram song in-app; ADR-003). Some platforms mishandle audio-less uploads.

**Why not "muted by default."** The prior draft muted all clip audio, justified by speed ramping making it unusable — but **M1 has no speed ramps (all segments rate 1.0)**, so that justification does not apply in M1. For family footage the natural sound is often the memory; a tool whose identity is *the user directs* must not make silence an un-overridable editorial claim. The genuinely hard case — natural sound mixed *under* the music with per-clip ducking — is real work and stays deferred (§12); `clip` mode avoids it by using a single audio source.

**Licensing (ADR-003).** `clip` mode plays the user's own recorded audio. Incidental background sound in the originals is the user's own capture and is out of ADR-003's scope, which governs the product *supplying or claiming* licensed music. No ADR-003 change.

**Per-clip audio (`clips[].audio`) stays deferred.** The per-clip `retain` / `gain_db` fields govern the future "music + selectively unducked natural sound" render (ducking) and are **not consulted in M1**; M1 writes `retain: false`. Export is per-mode, not a forced trio.

### 8.3 · Output QA (gate — blocks export)
Not black (sampled-frame luma above floor) · **audio matches the mode's expectation** — `music` must not be silent; `silent` must *be* silent and still carry a valid track (a naive not-silent check would wrongly fail it); `clip` must carry a valid track and is non-silent **unless every included source is audio-less** (`has_audio:false`), in which case a silent `clip` render is correct · duration within **±0.5 s** of the timeline sum · exactly 1080×1920 · H.264/AAC · safe-title margins · frame count non-zero. Any failure blocks export and is surfaced with its reason.

## 9 · Non-functional requirements

| Area | Requirement |
|---|---|
| **Privacy / egress** | Backend binds `127.0.0.1` only. **No outbound network from the media path.** Frontend ships zero remote assets. Enforced by a dependency/asset audit as a build gate. Localhost binding is necessary but **not sufficient** — see Local delivery security. Binding beyond `127.0.0.1` is a stop-and-ask (ADR-005) |
| **Local delivery security (ADR-011)** | Reject cross-origin requests (`Origin`/`Referer` allow-list); validate `Host` against an allow-list (anti DNS-rebinding); **no permissive CORS** (no `*`, no wildcard credentials); a **per-launch capability token** required on state-changing endpoints; **absolute media paths scrubbed** from the error envelope, logs, and any surfaced field. Each protection has a guard test that fails when it is removed (WO-113) |
| **Originals** | Opened read-only. No write, move, or delete path beneath `media_root` — verified by test |
| **Repo hygiene** | `project.json` embeds absolute paths to private media. Already covered by `.gitignore`; **never commit a project file** |
| **Performance (real 50-clip day, Apple Silicon)** | Proxies ≤ ~5 min · analysis + trim proposals ≤ ~5 min · render ≤ ~5 min · timeline scrub responsive on proxies |
| **Proxies** | 540×960 H.264, ~1.5 Mbps, `+faststart`, separate derived directory |
| **Failure honesty** | Unreadable sources are reported with a reason and retained with `readable: false` — never silently dropped |

## 10 · Validation gates

**Internal checkpoint (ADR-007) — not a release.** Import → timeline → render → export must work end to end, proving FFmpeg concat and 9:16 crop, **before** the trim proposer is built. The renderer and the proposer are never debugged simultaneously.

**M1 exit gate:**
1. Import a **real full day (~50 clips)** — not a curated subset — plus a track; every source probed or reported unreadable.
2. `save → reopen → byte-equivalent project.json` (round-trip test is a build gate).
3. No writes beneath `media_root` (test-verified).
4. "Trim all" proposes a window for every clip; **each displays a readable reason**; the fallback rule (§5.2.5) fires visibly on a clip that clears no floor.
5. **Curate:** exclude a clip and restore it (both round-trip; the excluded clip does not render), and delete a clip and restore it (exact restore). Then adjust one trim and remove another: both set `origin = "user"`, set `disposition` to `adjusted` / `dismissed`, **both retain `proposals.segments`**, and both survive reload.
6. Render and export **all three audio modes** (`music`, `clip`, `silent`); each carries a valid track and passes QA; QA catches a deliberately black or truncated render, a silent `music` render, and a non-silent `silent` render; and correctly passes a legitimately-silent `clip` reel of an all-audio-less set.
7. Editing after a finalize approval resets `finalize` to `null`.
8. Owner imports a real day, **manually curates it to a short set**, AI-trims the keepers, exports the reel, and **judges the result against that day's Apple Photos Memory — recording specifically why not if it falls short.** The bar is that M1 is *evaluable against the free alternative and plausibly worth keeping* (ADR-009), **not** proven superior; superiority is the deferred real-user question (ADR-006/007).

## 11 · Decisions

All resolved 2026-07-23:

- `segments[]` per clip; the v1 UI enforces exactly one.
- **Audio has three modes** (`music` / `clip` / `silent`). `silent` (formerly "without music") is for in-app Instagram music; `clip` carries natural sound. Clip audio is never speed-mangled because M1 segments are all rate 1.0.
- **Natural clip audio ships in M1; music-only is not mandatory.** Per-clip ducking *under* music stays deferred (§12).
- AI trim ships in M1 alongside its override controls (ADR-007).
- **Clip order defaults to capture time**, falling back to folder order when timestamps are missing.
- **Mac-only.** Running the editor from a phone browser was considered and deferred (§12). ADR-005 is unchanged, and the backend stays bound to `127.0.0.1`.
- **Manual curation (include/exclude/delete/restore) is in M1**; the selection/order *assist* stays M2 (ADR-009).
- **Every proposal carries a `disposition`**; kept-versus-discarded is read from it, not from binary `origin` (ADR-010).
- **Local delivery is origin-guarded and capability-token protected** (ADR-011); `127.0.0.1` binding is necessary but not sufficient.

## 12 · Deferred

Selection/ordering assist (M2) · speed assist and beat detection (M3) · per-clip audio retention and **ducking under music** (global `clip` mode ships in M1; per-clip mixing under a music bed is the deferred case) · saliency reframing · true speed curves · multi-project management · undo history beyond delete/restore · **bounded proposal history across re-runs (deferred to M2; never an unbounded log — ADR-010)** · packaging and distribution.

**Phone access (deferred).** Serving the editor to a phone browser over Wi-Fi, with clips picked from the Photos album and uploaded to the Mac. Three things must be settled first: whether iOS preserves `captured_at` through a browser upload (it often re-encodes and strips it, which would break capture-time ordering), whether a timeline is workable on a phone screen, and the fact that binding beyond `127.0.0.1` weakens ADR-005's privacy posture. The capture-time question is cheap to test and should be checked before this is revisited.
**TBD:** minimum macOS/Apple Silicon target; FFmpeg distribution (system vs. bundled — a licensing question under ADR-003).
