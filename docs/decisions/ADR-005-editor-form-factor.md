# ADR-005 — Local web application as the editor form factor

**Status:** Accepted — owner-approved 2026-07-23
**Supersedes:** ADR-001 — Start with a local command-line editorial pipeline
**Relates to:** ADR-002 (privacy and data posture) — unchanged and still governing

Acceptance is scoped to this decision only. It fixes the form factor and the canonical state artifact (`project.json`). It does **not** authorize implementation — Work Orders additionally require an authorized ADP — and it does **not** authorize media collection, which remains gated by ADR-002.

## Context

ADR-001 chose a local CLI pipeline on an explicit premise: *"The uncertainty is editorial quality, not interface polish."* It deferred any review application until editorial quality was proven, and made the manifest and report the review surface.

The 2026-07-23 pivot invalidates that premise. The product is now a nine-stage, transparent, approval-gated editor in which the user reviews machine proposals — selection, ordering, trim, speed — overrides any of them, and approves each stage before the next runs, then finishes the edit on a timeline. **Review-and-approve at every proposing stage cannot be delivered through a JSON manifest and a printed report.** The interaction surface is the primary deliverable, not a deferred nicety.

ADR-001 anticipated this path — it kept planner interfaces renderer-independent so "a desktop review application… can be added after results justify them." The pivot brings that addition forward and makes it central.

Constraints that persist unchanged: local-first, originals never leave the device (ADR-002), Apple Silicon Mac as the target, FFmpeg for decode and render.

## Options considered

1. **Local web application (recommended):** browser UI served by a local backend bound to localhost; FFmpeg and the analysis/proposal layer run in that backend. Fastest iteration on a timeline surface, mature ecosystem for timeline/scrubbing components, no packaging burden during the build, and local-first by construction.
2. **Cross-platform desktop (Tauri or Electron):** single installable artifact, native file dialogs, better filesystem integration. Tauri is light, Electron heavy. Adds packaging and signing work before the interaction itself is proven.
3. **Native macOS (SwiftUI + AVFoundation):** best preview/scrub performance and OS integration on Apple Silicon. Highest build cost for a timeline editor, Mac-only, slowest iteration on UI questions that are still open.
4. **Retain CLI + manifest (ADR-001 status quo):** cheapest, but structurally cannot deliver a review-and-approve product. Rejected by the pivot.
5. **Hosted web application:** rejected outright — uploading private family footage violates ADR-002.

## Proposed decision

Adopt option 1. Build the editor as a **local web application**: a browser UI served by a local backend on localhost, with FFmpeg-based ingest, analysis, and render running in that backend process. Original media is read in place, never modified, and never leaves the device.

**Canonical state is a versioned `project.json`** holding clip references, selection and order, per-clip trim in/out, speed ramps, deletions and restores, the music reference, and **the rationale attached to every machine proposal.** It is the stage-9 save/load artifact and must round-trip losslessly.

Keep the analysis/proposal layer independent of both the UI and the renderer, so a Tauri or native shell, or an NLE export adapter, can be added later without rewriting the assists.

## Consequences

- Fast iteration on the timeline, which is the actual product surface.
- Local-first is preserved by construction: bound to localhost, no media egress. This must be explicit and verified — no telemetry, no remote asset or font fetches, no CDN dependencies.
- **Rationale is persisted state, not a transient UI string.** The audit trail survives save, reload, and re-edit; a reopened project still explains itself.
- Browser preview of long or large clips requires proxies, so **proxy generation becomes a stage-1 requirement** rather than a later optimization.
- No installable artifact during the build phase. Distribution and packaging are a separate, later decision, and a new ADR if they change the form factor.
- A browser UI will not match native scrub performance. Accepted: the bottleneck for this product is review and approval ergonomics, not frame-accurate professional scrubbing.
