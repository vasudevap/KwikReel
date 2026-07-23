# Component decomposition — the overarching agent as bounded sub-agents

**Status:** Draft · **forward-looking design** — owner approval required. Introduces **no accepted decision** and relaxes **no constraint**. Ungraded; introduces no claim into [EVIDENCE-LEDGER.md](EVIDENCE-LEDGER.md).
**Governing:** subordinate to [PROJECT.md](../../PROJECT.md), [ADR-001](../decisions/ADR-001-prototype-shape.md) (local CLI, planner independent of renderer), [ADR-004](../decisions/ADR-004-validation-first-sequencing.md) (validation-first; apparatus-not-product), and [prototype-definition.md](prototype-definition.md) (component boundaries, technology assessment). Build sequencing is authoritative in [phase-1-backlog.md](../work-orders/phase-1-backlog.md).

## What is real (read this first)

- **No code exists and none is authorized.** This document decomposes a *proposed* pipeline; it is buildable only after the ADRs are accepted, `VALIDATION-PLAN.md` is approved, and the owner authorizes an ADP.
- **Only Phase-1 apparatus nodes build first**, and the pivotal experiment (EXP-003) gates everything below it. Components tagged Phase 2+ are decomposed here as *design*, not licensed to build.
- **"Agent" means a governed pipeline that proposes** ([PROJECT.md](../../PROJECT.md)). The probabilistic model lives at the **edges** as a bounded scorer; it never plans, never touches pixels, never bypasses the deterministic timeline constraints.

## Organizing principle

Components communicate **only through frozen artifact contracts**. One consequence does the heavy lifting: the same boundaries serve as *runtime* seams and as *parallel-build* lanes. Freeze the contracts (§1) and the rest fans out into disjoint Work Orders (§6). Deterministic core, probabilistic edges — the split is architectural, not stylistic.

---

## §1 · Contract kernel — freeze first (WO-001)

The only coordination points. Nothing parallelizes until these are frozen. Sketches below are **proposed shapes for review**, not authoritative schemas.

**`SourceIndex`** — immutable, read-only facts per source clip.
```jsonc
{
  "source_id": "opaque id, scoped to a synthetic contributor ID",
  "content_hash": "sha256 of bytes — the reproducibility key",
  "path": "read-only path (opened read-only; never written back)",
  "duration_s": 12.4,
  "captured_at": "ISO-8601 with tz offset as recorded",
  "orientation": "portrait|landscape",
  "codec": "hevc|h264|…", "fps": 30,
  "has_gps": true,          // presence flag only; coordinates never leave the data plane
  "readable": true,         // false → CorruptReport{reason}
  "proxy_path": "derived; separate output directory"
}
```

**`analysis.json`** — immutable per-clip signals + candidacy (one row per source).
```jsonc
{
  "source_id": "…",
  "signals": { "blur": 0.12, "exposure": 0.63, "shake": 0.20,
               "faces_count": 2,                 // COUNT ONLY — no identity, ever (ADR-002)
               "saliency_ref": "map-artifact-id",// reused for 9:16 reframing crop
               "audio_events": { "laughter": 0.8, "cheer": 0.1 } },
  "dup_group": "cluster-7",
  "candidacy": "usable|rejected",                // rejected is recoverable, never deleted
  "must_include": false,                         // user-declared; if true never rejected, declared-not-inferred
  "candidate_windows": [ { "in_s": 3.0, "out_s": 8.0, "local_quality": 0.7 } ],
  "reasons": [ "ReasonRecord", "…" ],
  "run_id": "…"                                  // tool/model versions live in run.json
}
```

**`ReasonRecord`** — the explainability primitive; every deciding component emits one.
```jsonc
{
  "code": "BLUR_ABOVE_THRESHOLD",                // machine-readable, stable
  "human_text": "Too blurry to keep — sharpness 0.12 vs 0.35 floor",
  "evidence_refs": ["signals.blur"],             // MUST cite what actually drove the decision
  "score": 0.12,
  "confidence": "high|med|low"                   // model-sourced reasons carry uncertainty
}
```

**`timeline.json` (the EDL)** — the contract between planning and rendering: inspectable, editable, replayable.
```jsonc
{
  "run_id": "…", "target_duration_s": 75,
  "track_ref": "rights-cleared local track (ADR-003)",
  "segments": [
    { "source_id": "…", "in_s": 3.0, "out_s": 8.0, "order": 1, "event": "cluster-2",
      "crop": "saliency-driven 9:16",            // not blind center-crop
      "speed": 1.0,                              // advisory flags only; never auto-ramped
      "beat_refs": [12, 16], "transition": "cut",
      "reasons": [ "ReasonRecord", "…" ] }       // selects / rejects / timing rationale
  ],
  "rejected": [ { "source_id": "…", "reasons": [ "…" ] } ],  // recoverable
  "clean_export": true                           // no-music variant offered (ADR-003)
}
```

**`Scorer` interface** — the pluggable seam that makes the pivotal A/B clean.
```
Scorer.score(candidate, context) -> ScoredCandidate{ score, features, reasons:[ReasonRecord] }
  HeuristicScorer (WO-007): pure function of analysis.json signals — the baseline
  ModelScorer     (WO-008): temp-0, rank-normalized; returns STRUCTURED features, not a free EDL
  Identical I/O → downstream unchanged → clean A/B. Neither may write the comparison harness.
```

**`run.json`** — provenance stamp written into every artifact (reproducibility).
```jsonc
{ "run_id":"…", "seeds":{…}, "ffmpeg_version":"…", "model_ids":{…},
  "prompt_hash":"…", "config":{…}, "input_hashes":[…], "code_rev":"…" }
```

---

## §2 · Component catalog

| # | Component (runtime sub-agent) | Kind | Emits → | Phase / WO |
|---|---|---|---|---|
| 1 | **Ingest & Proxy** — `probe_clip`, `validate_readable`, `make_proxy`, `build_source_index` | Deterministic | `SourceIndex` + proxies | 1 / WO-005 |
| 2 | **Per-clip Analysis** — `blur/exposure/shake`, `dup_embedding`, `detect_faces_count`, `saliency_map`, `audio_event_salience` | Det + on-device models | `analysis.json` signals | 1 / WO-006, 010 |
| 3 | **Dedup & Junk Filter** — `cluster_duplicates`, `flag_unusable`, `apply_must_include` | Deterministic | annotates `analysis.json` | 1 / WO-006 |
| 4 | **Event Clustering** — `cluster_by_time_gap`, `cluster_by_gps`, `refine_by_visual_sim`, `resolve_chronology` | Deterministic | events + order | 2 / EXP-005 |
| 5 | **Candidate Builder** — `propose_windows` (motion+audio+saliency), `score_window_quality` | Deterministic | candidate windows | 1 / WO-010 |
| 6a | **HeuristicScorer** — duration+faces+sharpness+motion+audio+coverage+must-include. Built deliberately well | Deterministic | `ScoredCandidate[]` | 1 / WO-007 |
| 6b | **ModelScorer** — rubric, temp-0, pairwise on borderline; local default, cloud-keyframe = separate opt-in, non-gating | **Model, bounded** | `ScoredCandidate[]` | 1 / WO-008 |
| 7 | **Timeline Solver** *(the planner — NOT the LLM)* — `select_under_budget`, `enforce_must_include`, `order_chronological`, `emit_timeline` | Deterministic | `timeline.json` | 2 / EXP-006 *(thin slice → Phase 1)* |
| 8 | **Beat/Section Analyzer** — `detect_beats` (**librosa**), `detect_sections`, `eligible_beat_snapping` (subset) | Deterministic | beat-map | 2 / EXP-006 |
| 9 | **Renderer/Assembler** *(the hands)* — `assemble`, `reframe_9x16` (saliency-driven), `loudness_normalize`, `duck_music` | Deterministic, sandboxed | `draft.mp4` | 2 |
| 10 | **Output QA** — `validate_render` (not black/silent/truncated; duration; safe-title margins) | Deterministic gate | QAReport | 2 |
| 11 | **Explanation Composer** — `render_reason` from the features that drove the score (faithfulness-gated) | Bounded | report / manifest text | 1 (manifest) → 3 (UI) |
| 12 | **Review/Correction UI** *(the product)* — `lock/remove/restore/regenerate/adjust_window/show_provenance` | Interactive | corrected `timeline.json` + corrections count | 3 / EXP-008 |

**Cross-cutting governed components:** Provenance recorder (`run.json`) · **Golden-set / EDL-regression harness** (fixed inputs → expected EDLs; drift detection; powers the every-phase-close floor re-run) · Consent & deletion worker (ADR-002, WO-002) · Held-out guard · Egress guard · Competitive-floor harness (WO-004).

### Guardrails bound into components (not left to agent judgment)

| Hard constraint | Enforced in |
|---|---|
| No face recognition / person ID | C-2 `detect_faces_count` returns a count; no identity API is reachable from its file scope |
| Originals read-only; no delete path | C-1 (read-only open) + C-9 (renderer has no source-delete path) |
| Original media never leaves device | Egress guard (cross-cutting) + C-6b cloud arm = opt-in keyframes only, non-default, non-gating |
| No `madmom` / no distribution-restrictive licence | C-8 uses librosa; dependency-licence check is a WO gate |
| Held-out day untouched | Held-out guard; the day is excluded from every component's allowed file scope |
| No auto-publish | C-9 has no network; export is a gated human act via C-12 |
| Pre-registered thresholds not relaxed | thresholds are config consumed by C-3/C-6/C-7; changing one is stop-and-ask |
| Explainable throughout | every deciding component emits a `ReasonRecord`; C-11 faithfulness gate |

---

## §3 · Data flow (artifacts are the seams)

```text
folder ─▶[1 Ingest]─▶ SourceIndex+proxies ─▶[2 Analysis]─▶ analysis.json ─┬─▶[3 Filter]─┐
                                                                          ├─▶[4 Events]─┤
                                                                          └─▶[5 Windows]┘
                                                                                        │
                                    ┌──────────── same Scorer interface ────────┐   ScoredCandidate[]
                                    │  [6a HeuristicScorer]   [6b ModelScorer]   │      │
                                    └────────────────┬───────────────┬──────────┘      ▼
                Phase-1 gate ◀── [WO-009 comparison harness: Spearman + margin, EXP-003] ┘
                                                     │
                        ═══════ EXP-003 must pass to unlock everything below ═══════
                                                     ▼
        [8 Beat] ─▶ [7 Solver] ─▶ timeline.json(EDL) ─▶ [9 Renderer] ─▶ draft.mp4 ─▶ [10 QA]
                                        │                                                 │
                                        └──────────▶ [11 Explanation] ─▶ manifest ◀───────┘
                                                             │
                                                     [12 Review UI] ─▶ corrected EDL + corrections (EXP-008)
```

## §4 · The scorer seam is the keystone

Because 6a and 6b implement one `Scorer` interface, everything downstream is byte-identical regardless of which is active. Two properties fall out:

- **The pivotal experiment is a clean A/B by construction** — swap the scorer, hold all else fixed, compare rankings (EXP-003).
- **The baseline and model rankers are the natural parallel-build pair** — disjoint file scopes, neither writes the comparison harness ([phase-1-backlog.md](../work-orders/phase-1-backlog.md)). The interface is the coordination contract; the implementations never see each other.

This is also why the model is confined to a *scorer*, not promoted to an *EDL author*: an LLM emitting the whole timeline would make the A/B unclean and put confabulated free-text on the honesty surface. The deterministic solver plans; the model only supplies scores it must justify against real features.

## §5 · Phase gating

- **Buildable in Phase 1 (apparatus):** Contract kernel, C-1, C-2, C-3, C-5, C-6a, C-6b, the WO-009 comparison harness, C-11 in *manifest* mode, and the cross-cutting guards/harnesses.
- **Thin vertical slice pulled into Phase 1:** `emit_timeline` in **rank → manifest** mode (no render) + `render_reason`, so an annotator can count *edits-to-acceptance on the manifest* — an early, directional read on the north star without the Phase-2 generator or the Phase-3 UI. Detailed as a proposed delta in [phase-1-backlog-deltas.md](../work-orders/phase-1-backlog-deltas.md).
- **Decomposed but deferred (Phase 2+):** C-4, full C-7, C-8, C-9, C-10, C-12. Authorized only if EXP-003 passes, via the Phase-2 Engineering Specification — never by inertia.

## §6 · Mapping to the existing Work Orders

| Component(s) | Work Order |
|---|---|
| Contract kernel + guards | WO-001 (extend to freeze §1 contracts) |
| Consent & deletion; corpus; held-out seal | WO-002, WO-003 |
| Competitive-floor harness | WO-004 |
| C-1 Ingest | WO-005 |
| C-2 Analysis + C-3 Filter | WO-006 |
| C-6a HeuristicScorer | WO-007 |
| C-6b ModelScorer | WO-008 |
| WO-009 comparison harness (+ thin manifest slice, proposed) | WO-009 |
| C-5 Candidate Builder | WO-010 |
| Throughput | WO-011 |
| Integration verification (+ golden-set harness, proposed) | WO-012 |

The overlay is near-exact with the accepted backlog — the reassuring sign the decomposition is right. What this document *adds*: the contract kernel as a first-class freeze step, saliency reuse for reframing, an Output-QA component, a faithfulness-gated Explanation Composer, the golden-set regression harness, and the thin rank→manifest slice. Those additions are carried as proposed deltas, not applied here.

**This document unlocks nothing.** It is buildable only after the ADR → validation-plan → ADP gates, and below EXP-003 only after that experiment reports.
