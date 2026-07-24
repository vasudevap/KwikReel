# Component decomposition — the staged editor as bounded components

**Status:** Draft · **forward-looking design** — owner approval required. Introduces **no accepted decision** and relaxes **no constraint**. Ungraded; introduces no claim into [EVIDENCE-LEDGER.md](EVIDENCE-LEDGER.md).
**Rewritten 2026-07-23** for the pivot to a human-directed, approval-gated editor.
**Governing:** [PROJECT.md](../../PROJECT.md), [ADR-005](../decisions/ADR-005-editor-form-factor.md) (local web app; `project.json` canonical; analysis layer independent of UI and renderer), [ADR-006](../decisions/ADR-006-incremental-staged-build.md) (staged build; per-stage approval; transparency as a standing requirement), [ADR-002](../decisions/ADR-002-privacy-and-data-posture.md), [ADR-003](../decisions/ADR-003-music-and-licensing-posture.md). Build sequencing is authoritative in [ROADMAP.md](../../ROADMAP.md).

## What is real (read this first)

- **No code exists and none is authorized.** This decomposes a *proposed* system; it is buildable only after the owner authorizes an ADP.
- **Every assist is a proposal.** No component may advance a stage. Selection, trim, and speed emit proposals with reasons; the user approves, adjusts, or discards, and that decision is recorded.
- **A component that cannot explain its proposals is not complete** (ADR-006). The `ReasonRecord` is not decoration — it is the contract.

## Organizing principle

Components communicate **only through frozen artifact contracts**, and the same boundaries serve as runtime seams and parallel-build lanes. Deterministic core, bounded probabilistic edges — architectural, not stylistic.

One rule shapes everything below: **machine output and human decision are stored separately and never conflated.** Every field a component proposes carries an `origin` marking it as proposed or user-set. That single discipline is what makes the product transparent, makes overrides durable across save/reload, and makes "were the proposals any good?" measurable at all.

---

## §1 · Contract kernel — freeze first

The only coordination points. Sketches below are **proposed shapes for review**, not authoritative schemas.

**`SourceIndex`** — immutable, read-only facts per source clip.
```jsonc
{
  "source_id": "opaque id",
  "content_hash": "sha256 of bytes — the reproducibility key",
  "path": "read-only path (opened read-only; never written back)",
  "duration_s": 12.4,
  "captured_at": "ISO-8601 with tz offset as recorded",
  "orientation": "portrait|landscape",
  "codec": "hevc|h264|…", "fps": 30,
  "has_gps": true,          // presence flag only; coordinates never leave the data plane
  "readable": true,         // false → reported to the user, never silently dropped
  "proxy_path": "derived; separate output directory"
}
```

**`analysis.json`** — immutable per-clip signals (facts, not decisions).
```jsonc
{
  "source_id": "…",
  "signals": { "blur": 0.12, "exposure": 0.63, "shake": 0.20, "static_score": 0.8,
               "people_count": 2,                // COUNT ONLY — no identity, ever (ADR-002)
               "motion_energy": [ /* per-second */ ],
               "audio_events": { "laughter": 0.8, "cheer": 0.1 },
               "saliency_ref": "map-artifact-id" // reused for 9:16 reframing crop
             },
  "dup_group": "cluster-7",
  "scene_cuts_s": [ 2.1, 7.8 ],
  "run_id": "…"
}
```

**`ReasonRecord`** — the transparency primitive. Every proposing component emits one; **it persists in `project.json`, not just in the UI.**
```jsonc
{
  "code": "BLUR_ABOVE_THRESHOLD",                // machine-readable, stable
  "human_text": "Trimmed the first 2.4 s — too blurry to keep (sharpness 0.12 vs 0.35 floor)",
  "evidence_refs": ["signals.blur"],             // MUST cite what actually drove the proposal
  "score": 0.12,
  "confidence": "high|med|low"
}
```

**`project.json`** — canonical, re-openable state (ADR-005). Replaces the superseded `timeline.json`.
```jsonc
{
  "schema_version": 1, "run_id": "…",
  "target_duration_s": 75,
  "track_ref": "user-supplied rights-cleared local track (ADR-003)",
  "stage_approvals": {                           // nothing advances without these
    "ingest": "2026-07-24T19:02:11Z", "selection": null, "trim": null, "speed": null
  },
  "clips": [
    { "source_id": "…",
      "included": true,
      "order": 1,
      "trim":  { "in_s": 3.0, "out_s": 8.0 },
      "speed": [ { "from_s": 0.0, "to_s": 2.0, "rate": 2.0 } ],  // ramps are core, not advisory
      "deleted": false,                          // recoverable — restore is a stage-6 action
      "origin": { "included": "proposed|user", "order": "proposed|user",
                  "trim": "proposed|user", "speed": "proposed|user" },
      "reasons": [ "ReasonRecord", "…" ]         // why proposed; survives save/reload
    }
  ],
  "rejected": [ { "source_id": "…", "reasons": [ "…" ] } ],   // recoverable, with stated reasons
  "export": { "with_music": true, "without_music": true }
}
```

**`run.json`** — provenance stamp written into every artifact.
```jsonc
{ "run_id":"…", "seeds":{…}, "ffmpeg_version":"…", "model_ids":{…},
  "config":{…}, "input_hashes":[…], "code_rev":"…" }
```

---

## §2 · Component catalog

| # | Component | Kind | Emits → | Milestone |
|---|---|---|---|---|
| 1 | **Ingest & Proxy** — `probe_clip`, `validate_readable`, `make_proxy`, `build_source_index` | Deterministic | `SourceIndex` + proxies | M1 |
| 2 | **Project Store** — `save`, `load`, `migrate_schema`, lossless round-trip | Deterministic | `project.json` | M1 |
| 3 | **Timeline Editor (UI)** *— the product* — sequence view, `set_trim`, `set_speed`, `delete`, `restore`, `reorder`, show rationale | Interactive | user-set fields + `origin` | M2 |
| 4 | **Renderer / Assembler** — `assemble`, `apply_speed_ramps`, `reframe_9x16` (saliency-driven), `loudness_normalize`, `duck_music` | Deterministic, sandboxed | `draft.mp4` | M3 |
| 5 | **Output QA** — `validate_render`: not black/silent/truncated; duration; safe-title margins | Deterministic gate | QAReport | M3 |
| 6 | **Exporter** — 1080×1920 H.264/AAC, **with-music and without-music variants** | Deterministic | final files | M3 |
| 7 | **Per-clip Analysis** — `blur/exposure/shake`, `static_score`, `dup_embedding`, `people_count`, `motion_energy`, `audio_event_salience`, `scene_cuts`, `saliency_map` | Det + on-device models | `analysis.json` | M4 |
| 8 | **Trim Proposer** — `propose_window` from quality/static/duplicate signals | Deterministic | trim proposals + reasons | M4 |
| 9 | **Beat/Section Analyzer** — `detect_beats` (**librosa**), `detect_sections`, `eligible_beat_snapping` | Deterministic | beat-map | M5 |
| 10 | **Speed Proposer** — interest curve from motion/audio/scene → ramps; beat-aligned on opt-in | Deterministic (ML later) | speed proposals + reasons | M5 |
| 11 | **Selection & Order Proposer** — legible heuristic: duration, people **count**, sharpness, motion, event coverage, chronology | Deterministic (ML later) | include/exclude + order + reasons | M6 |
| 12 | **Explanation Composer** — renders `ReasonRecord` into user-facing text, faithfulness-gated to the features that actually drove the proposal | Bounded | UI rationale | M4 → M6 |

**Cross-cutting:** Provenance recorder (`run.json`) · **Approval gatekeeper** (no stage advances without a `stage_approvals` entry) · **Egress guard** (no network from the media path) · Consent & deletion worker (ADR-002) · Golden-set regression harness (fixed inputs → expected `project.json`; drift detection).

### Guardrails bound into components, not left to agent judgment

| Hard constraint | Enforced in |
|---|---|
| No face recognition / person ID | C-7 `people_count` returns a count; no identity API reachable from its file scope |
| Originals read-only; no delete path | C-1 (read-only open) + C-4 (renderer has no source-delete path) |
| Original media never leaves device | Egress guard; media path has no network capability; no CDN/remote fonts in the UI |
| No `madmom` / no distribution-restrictive licence | C-9 uses librosa; dependency-licence check is a build gate |
| No auto-publish | C-4/C-6 have no network; export is a gated human act via C-3 |
| **No assist advances a stage** | Approval gatekeeper: stage N+1 refuses to run without `stage_approvals[N]` |
| **Every proposal explains itself** | No proposing component may emit a field without an accompanying `ReasonRecord`; C-12 faithfulness gate |
| **Overrides are durable** | `origin` is written on every user edit; the Project Store round-trip test is a build gate |
| Recoverable, never destructive | `deleted` is a flag; `rejected[]` retains reasons; restore is always available |

---

## §3 · Data flow

```text
clips + track ─▶[1 Ingest]─▶ SourceIndex + proxies ─▶[2 Project Store]─▶ project.json
                                     │                                        ▲
                                     ▼                                        │
                              [7 Analysis]─▶ analysis.json                    │
                                     │                                        │
        ┌────────────────────────────┼────────────────────────────┐           │
        ▼                            ▼                            ▼           │
 [11 Selection/Order]        [8 Trim Proposer]           [10 Speed Proposer]   │
   proposals+reasons           proposals+reasons          proposals+reasons    │
        └────────────────────────────┴────────────────────────────┘           │
                                     │                                        │
                     ══ APPROVAL GATE — user reviews, overrides, approves ══   │
                                     │  (origin: proposed → user)             │
                                     ▼                                        │
                          [3 Timeline Editor — the product] ───────────────────┘
                                     │  explicit Finalize
                                     ▼
                    [4 Renderer]─▶ draft.mp4 ─▶[5 Output QA]─▶[6 Exporter]
                                                                 └─▶ with-music / without-music
```

## §4 · The keystone is the approval gate, not a scorer

The previous decomposition made a pluggable `Scorer` interface the keystone, so a heuristic and a model ranker could be A/B'd cleanly for the pivotal experiment. That experiment is retired. **The keystone is now the approval gate and the `origin` field.**

Three properties follow:

- **Every assist is independently disposable.** Because proposals only ever write fields the user can override, deleting a proposer degrades the product to manual for that stage and breaks nothing downstream. That is what makes ADR-006's stage-level de-scope actually executable rather than aspirational.
- **Assist quality is measured continuously and for free.** `origin` records whether each final value came from the machine or the human, so "were the proposals kept?" — a `PROJECT.md` success measure — is a query over saved projects, not a study.
- **The manual capability is the baseline.** Built first (M2–M3), it gives each later assist something honest to be judged against.

This is also why proposers are confined to emitting *fields with reasons*, never a finished edit: a component that authored the whole timeline would put unattributable output on the honesty surface and make overrides ambiguous.

## §5 · Build sequencing

Authoritative in [ROADMAP.md](../../ROADMAP.md). Summary: **M1** C-1, C-2 · **M2** C-3 · **M3** C-4, C-5, C-6 *(first shippable — a complete manual editor)* · **M4** C-7, C-8, C-12 · **M5** C-9, C-10 · **M6** C-11.

Assist components (C-8, C-10, C-11) are added on top of working manual capability and may each be dropped without breaking the product.

## §6 · Work Orders

**The existing `docs/work-orders/phase-1-backlog*.md` files are retired** — they decompose the validation apparatus (corpus, scorer A/B, comparison harness, held-out discipline) that ADR-006 withdrew. A fresh Work Order backlog is drawn from this decomposition and the ROADMAP milestones **after** the owner authorizes an ADP.

**This document unlocks nothing.** It is buildable only after that authorization.
