# M1 Work Order backlog — working pipe + AI trim

**Status:** Draft — owner approval required
**Governing:** [ES-001](../specs/ES-001-manual-editor-core.md) (Accepted), [ROADMAP.md](../../ROADMAP.md), [ADR-005](../decisions/ADR-005-editor-form-factor.md), [ADR-006](../decisions/ADR-006-incremental-staged-build.md), [ADR-007](../decisions/ADR-007-build-sequencing.md), [ADR-008](../decisions/ADR-008-prototype-before-contract-freeze.md)
**Authorizes nothing.** No Work Order may start until the owner authorizes an ADP.

## Directory layout (this is what makes the lanes safe)

```
backend/contracts/   WO-101      frontend/src/types/     WO-101
backend/ingest/      WO-102      frontend/src/app/       WO-107
backend/store/       WO-103      frontend/src/timeline/  WO-108
backend/render/      WO-104      frontend/src/edit/      WO-109
backend/qa/          WO-105      frontend/src/trim/      WO-110
backend/api/         WO-106
backend/analysis/    WO-111      fixtures/               WO-100
backend/propose/     WO-112      tests/guards/           WO-113
                                 tests/integration/      WO-114
```

**Dependency manifests (`pyproject.toml`, `package.json`) are owned by WO-101 alone.** WO-101 pre-declares the whole M1 set: fastapi, uvicorn, pydantic, opencv-python, numpy, pytest · react, typescript, vite. **Any WO needing something outside that set is a stop-and-ask** — two agents editing a manifest at once is the classic way parallel work corrupts itself.

WO-100 creates the frontend directories; later frontend WOs fill in their own. WO-100 also creates `fixtures/synthetic/` (committed, synthetic/rights-cleared only) and `fixtures/local/` (gitignored, owner-only real thumbnails) per ADR-013.

---

### WO-100 · Clickable prototype — runs first, alone
- **Scope:** React prototype of the entire M1 flow with fake data: create project → pick folder and track → clips on a timeline → **manually curate (include/exclude, delete, restore, reorder)** → AI trim (per clip and *Trim all*) → read the reasons → adjust or remove a suggestion → **approve (proposals get a `disposition`)** → finalize → export the three audio modes (music/clip/silent). Per [ADR-008](../decisions/ADR-008-prototype-before-contract-freeze.md) it must **fake the real waiting times** (~5 min analysis, ~5 min render) and **seed deliberately bad AI proposals** (a trim cutting the good part; a clip where the proposer gives up). **Thumbnails follow [ADR-013](../decisions/ADR-013-prototype-thumbnails-consent.md):** committed fixtures are **synthetic / rights-cleared only** (`fixtures/synthetic/`, no real people); real-footage thumbnails are the owner's own, generated locally into `fixtures/local/` (gitignored, never committed) behind a self-consent + lifecycle note recorded before extraction.
- **File scope:** `frontend/`, `fixtures/synthetic/` (committed), `fixtures/local/` (untracked)
- **Excludes:** Any backend. Any real processing. **Any committed real footage or real-footage thumbnail.** **Visual polish — colour, spacing, typography.**
- **Gates:** The full flow (incl. manual curation) is clickable end to end · the owner walks it and agrees it is the right flow · **a written list of ES-001 schema gaps is produced** · **no real footage or thumbnail is committed** (only `fixtures/synthetic/`)
- **Depends:** none
- **Stop-and-ask:** a gap requiring a change to an accepted ADR · effort drifting into visual design · **any need to commit real footage or a real-footage thumbnail**

> **Between WO-100 and WO-101:** any gap the prototype finds is amended into ES-001 first. WO-101 does not start until ES-001 reflects what the screen actually needs.

### WO-101 · Contract kernel and scaffold — runs second, alone
- **Scope:** Backend skeleton; dependency manifests. Freeze **as code** the ES-001 §4 schemas (`project.json`, `SourceIndex`, `analysis.json`, `ReasonRecord`) — **including the proposal `disposition` field (ADR-010)** — as Pydantic models with matching TypeScript types, **plus the service interfaces** every other WO codes against (Python Protocols for ingest, store, render, qa, analysis, propose). Schema round-trip test harness.
- **File scope:** `backend/contracts/`, `frontend/src/types/`, `tests/contracts/`, `pyproject.toml`, `package.json`
- **Excludes:** Any behaviour. Interfaces and types only.
- **Gates:** Schemas validate the ES-001 §4.1 example · round-trip is byte-equivalent · TS types and Pydantic models share one source of truth
- **Depends:** WO-100
- **Stop-and-ask:** any deviation from ES-001 as amended

### WO-102 · Ingest and proxies
- **Scope:** `probe_clip` via ffprobe, `validate_readable`, `make_proxy` (540×960 H.264 ~1.5 Mbps `+faststart`), `build_source_index`. Unreadable sources retained with `readable: false` and a reason.
- **File scope:** `backend/ingest/` · **Excludes:** any write beneath `media_root`; any analysis
- **Gates:** Real 50-clip day probes cleanly · a corrupt file is reported, not crashed on · proxies play · read-only enforcement test passes
- **Depends:** WO-101

### WO-103 · Project store
- **Scope:** `save`, `load`, schema-version handling, optimistic concurrency on `updated_at` (`409` on mismatch). Enforces the ES-001 §4.1 invariants: `origin` written on every mutation, `proposals` retained on override, **`disposition` set on every proposal (`pending`/`accepted`/`adjusted`/`dismissed`)**, `deleted` never removes a clip, `order` dense and unique.
- **File scope:** `backend/store/` · **Excludes:** HTTP concerns
- **Gates:** save → load → byte-equivalent · a machine write refuses to overwrite an `origin: "user"` field · delete then restore returns the exact prior state
- **Depends:** WO-101

### WO-104 · Renderer and exporter
- **Scope:** FFmpeg `filter_complex` per ES-001 §8.1 — trim, `setpts`, scale/crop to 1080×1920 centre-crop, concat. **Audio per §8.2 — three modes:** `music` uses the track and does not mix clip audio; `clip` muxes the concatenated **natural clip audio** with a **silent pad for any `has_audio:false` clip**; `silent` carries a valid silent AAC track. Single loudness-normalisation pass per mode.
- **File scope:** `backend/render/` · **Excludes:** speed ramps beyond rate 1.0 (M3); saliency reframing; **per-clip ducking under music (M2+)**; any network
- **Gates:** Duration within ±0.5 s of the timeline sum · exactly 1080×1920 H.264/AAC · all three audio modes produced on request · the `silent` mode carries a valid audio track · a `clip` render of an all-audio-less set is correctly silent with a valid track
- **Depends:** WO-101 · **Stop-and-ask:** if centre-crop proves unacceptable on real footage

### WO-105 · Output QA
- **Scope:** `validate_render` per ES-001 §8.3 — not black; **audio matched to the mode's expectation** (`music` not silent; `silent` silent + valid track; `clip` valid track, non-silent unless every source is audio-less); duration; resolution; codec; safe-title margins; non-zero frame count. Emits `QAReport`; failure blocks export with a stated reason.
- **File scope:** `backend/qa/` · **Excludes:** rendering; works against fixtures
- **Gates:** Catches a deliberately black render, a truncated render, and a silent `music` render · **does not** fail a correct `silent` render for being silent · **does not** fail a correct `clip` render of an all-audio-less set for being silent
- **Depends:** WO-101

### WO-106 · HTTP API and job runner
- **Scope:** FastAPI routes per ES-001 §6, bound to `127.0.0.1`. **Local delivery security per ES-001 §9 / [ADR-011](../decisions/ADR-011-local-delivery-security.md): Origin/Host allow-listing, no permissive CORS, a per-launch capability token on state-changing routes, and a path-scrubbed error envelope.** Async job runner reporting `{state, progress, error}`. Error envelope `{error_code, human_text, remediation}`. Proxy serving with range requests. Codes against WO-101 interfaces, not implementations.
- **File scope:** `backend/api/` · **Excludes:** business logic — it lives in the service WOs
- **Gates:** Every ES-001 §6 endpoint present · binds localhost only · **a cross-origin POST is rejected · a request with a missing/invalid capability token is rejected · no wildcard CORS · error responses carry no absolute media paths** · a failing job surfaces its error rather than hanging
- **Depends:** WO-101

### WO-107 · Frontend — app shell and API client
- **Scope:** Promote the prototype shell to real: routing, project create/open, job progress handling, and an **API client with a mock mode**. Runs on the prototype's fake data until WO-106 merges, then switches to the real API.
- **File scope:** `frontend/src/app/` · **Excludes:** timeline, edit controls, proposals. **No remote assets of any kind**
- **Gates:** Runs fully in mock mode · switching to the real client changes no component code
- **Depends:** WO-101 *(not WO-106 — this is what keeps the frontend off the critical path)*

### WO-108 · Frontend — timeline and preview
- **Scope:** Timeline sequence view showing clips, trims, and the music track. Proxy preview player with scrubbing.
- **File scope:** `frontend/src/timeline/` · **Excludes:** editing controls
- **Gates:** 50 clips render without stalling · scrubbing is responsive on proxies
- **Depends:** WO-107

### WO-109 · Frontend — manual curation, edit controls, and approval
- **Scope:** **Manual curation — include/exclude, delete, restore ([ADR-009](../decisions/ADR-009-manual-curation-in-m1.md) §5.5)** — plus trim handles, reorder, and the stage-approval UI. Excluded clips do not render; deleted clips are flag-retained for exact restore. The timeline shows running total vs `target_duration_s` (reference only). Every edit sets `origin: "user"`.
- **File scope:** `frontend/src/edit/` · **Excludes:** AI proposals; any *proposer* for inclusion/order (M2)
- **Gates:** Every edit survives reload · exclude→restore and delete→restore round-trip exactly · excluded clips are absent from the render · editing after a finalize approval visibly resets that approval
- **Depends:** WO-108

### WO-110 · Frontend — trim proposal UI
- **Scope:** Per-clip *AI trim* button and *Trim all* bulk action. Each proposal's `human_text` displayed inline. Adjust a proposal (→ `disposition: "adjusted"`); remove a proposal (→ `"dismissed"`); accept untouched proposals on stage approval (→ `"accepted"`); explicitly re-run one clip (→ fresh `"pending"`). All retain `proposals.segments`.
- **File scope:** `frontend/src/trim/` · **Excludes:** proposal logic — that is WO-112
- **Gates:** A proposal with no readable reason fails the build · adjust and remove both set `origin: "user"`, set `disposition` accordingly, and retain the proposal · re-run is the only path that overwrites a user value
- **Depends:** WO-109, WO-112, **and the checkpoint**

### WO-111 · Per-clip analysis
- **Scope:** Per-second sharpness (Laplacian variance), exposure clipping, shake, motion energy, audio RMS. Per-clip scene cuts. Cross-clip perceptual-hash duplicate groups. Emits `analysis.json`.
- **File scope:** `backend/analysis/` · **Excludes:** **any person detection or counting** — `people_count` stays `null` until M2; any proposal logic
- **Gates:** A real 50-clip day analyses in ≤ ~5 min on Apple Silicon · signals are per-second arrays matching clip duration
- **Depends:** WO-101, WO-102 · **Stop-and-ask:** any library offering face or person identification

### WO-112 · Trim proposer and explanations
- **Scope:** ES-001 §5.2 rules — longest contiguous window clearing the quality floors; trim blurry, shaky, badly-exposed, and static head and tail; never cross a scene cut; minimum 1.0 s window; **propose the full clip and say so when nothing clears the floors**. One `ReasonRecord` per contributing factor, citing the actual signal range. Thresholds in config.
- **File scope:** `backend/propose/` · **Excludes:** selection, ordering, speed; writing over any `origin: "user"` field
- **Gates:** Every clip receives a proposal · every proposal carries a `ReasonRecord` whose `evidence_refs` point at signals that genuinely drove it · the fallback rule fires visibly on a clip clearing no floor
- **Depends:** WO-101, WO-111, **and the checkpoint**

### WO-113 · Guards and build gates
- **Scope:** Automated checks — no outbound network from the media path; no CDN, remote fonts, or remote assets in the frontend bundle; dependency-licence check (no `madmom`, nothing distribution-restrictive); read-only enforcement beneath `media_root`; `project.json` gitignored. **Local delivery security guards (ADR-011): a cross-origin POST is rejected; a missing/invalid capability token is rejected; a wildcard-CORS config fails the build; an error response carrying an absolute media path fails.** **Fixtures guard (ADR-013): only `fixtures/synthetic/` is tracked — a committed real-footage file or thumbnail fails.**
- **File scope:** `tests/guards/`, `scripts/` · **Excludes:** feature work
- **Gates:** Each guard **fails** when deliberately violated — a guard that cannot fail is not a guard
- **Depends:** WO-101

### WO-114 · Integration verification
- **Scope:** The full ES-001 §10 M1 exit gate on **a real ~50-clip day, not a curated subset** — including the manual-curation round-trips (§10.5) and the **judge-against-Apple-Memory** comparison (§10.8).
- **File scope:** `tests/integration/` · **Excludes:** fixing what it finds — failures become new Work Orders
- **Gates:** All eight ES-001 §10 checks pass
- **Depends:** every WO above

## The checkpoint (ADR-007)

**The media pipeline must work end to end before WO-110 and WO-112 may merge** — WO-102, 103, 104, 105, 106, 107, 108, 109 merged and green, proving import → timeline → render → export.

Not a release. It exists so the renderer and the trim proposer are never being debugged at the same time.

## Lanes

Two WOs may run concurrently only if no dependency path connects them **and** their file scopes are disjoint. Both hold below.

| Lane | Sequence |
|---|---|
| **—** | **WO-100 alone.** Prototype, then amend ES-001 |
| **—** | **WO-101 alone.** The contract freeze everything waits on |
| A | WO-102 → WO-111 → WO-112 |
| B | WO-103 |
| C | WO-104 → WO-105 |
| D | WO-106 |
| E | WO-107 → WO-108 → WO-109 → WO-110 |
| F | WO-113 |
| **—** | **WO-114 alone**, after all lanes merge |

```
   WO-100 prototype ──► amend ES-001 ──► WO-101 freeze
                                              │
        ┌──────────┬──────────┬───────────────┼──────────┐
      WO-102     WO-103     WO-104          WO-106     WO-107     WO-113
        │                     │                          │
      WO-111                WO-105                     WO-108
        │                                                │
        │                                              WO-109
        │                                                │
        └────── checkpoint: pipeline green ──────────────┤
                          │                              │
                       WO-112 ─────────────────────────► WO-110
                          │                              │
                          └────────── WO-114 ────────────┘
```

## Stop-and-ask triggers (all Work Orders)

None of these is a judgment call.

1. Changing a frozen schema or service interface from WO-101.
2. Adding a dependency outside WO-101's declared set.
3. Any need to write, move, or delete beneath `media_root`.
4. Any outbound network call from the media path.
5. Any face recognition or person identification capability, at any phase.
6. Relaxing a validation gate to make it pass.
7. Anything needing a new ADR, ES, or Work Order.
8. Interface work beyond the WO's stated scope, including visual polish during WO-100.
9. Committing any real footage or real-footage thumbnail (only `fixtures/synthetic/` is tracked — ADR-002/013).
10. Relaxing any local delivery security control from ES-001 §9 / ADR-011.
