# ADR-001 — Start with a local command-line editorial pipeline

**Status:** Accepted — owner-approved 2026-07-22

Acceptance is scoped to this decision only. It fixes the prototype shape (local CLI, `timeline.json` canonical output, planner interfaces kept renderer-independent). It does **not** authorize implementation — Phase 1 Work Orders additionally require ADR-004 accepted and an authorized ADP — and it does **not** authorize media collection, which is gated separately by ADR-002.

## Context

The uncertainty is editorial quality, not interface polish. The prototype must prove that a batch can be ranked, ordered, timed, and rendered safely from private footage on an Apple Silicon Mac.

## Options considered

1. **Local CLI pipeline (recommended):** FFmpeg-based ingestion/rendering plus local analysis and JSON manifests.
2. Desktop application: better review ergonomics, but adds packaging/UI work before editorial quality is proven.
3. Web application: convenient sharing, but uploads/retention and video processing cost create privacy and operational distractions.
4. Final Cut/Premiere workflow: valuable later as an interchange/export adapter, but depends on an editor and does not validate autonomous assembly.
5. Atlas-managed workflow: apt for governed long-running jobs later; premature before a standalone editorial pipeline exists.

## Proposed decision

Build a local, deterministic CLI proof of concept first. Its canonical output is a versioned `timeline.json` plus an FFmpeg-rendered Reel. Keep planner interfaces independent of the renderer so a desktop review application, NLE interchange adapter, or Atlas orchestration can be added after results justify them.

## Consequences

- Strong privacy baseline and fast iteration using a local test corpus.
- No polished review UI in the POC; report/manifest are the review surface.
- A cloud or hybrid multimodal scorer remains an experiment behind explicit opt-in and redaction/retention controls.
