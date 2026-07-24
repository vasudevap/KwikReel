# WO-100 → WO-101 · ES-001 schema gaps found by the prototype

**Status:** Proposed findings — for owner/spec-owner decision before WO-101 freezes contracts
**Source:** The WO-100 clickable prototype (`frontend/`), built against [ES-001 §4](ES-001-manual-editor-core.md) on fake data
**Governing:** [ADR-008](../decisions/ADR-008-prototype-before-contract-freeze.md) (prototype before contract freeze). Per the M1 backlog, *every gap here is amended into ES-001 first; WO-101 does not start until ES-001 reflects what the screen actually needs.*

These are the places where building the actual screens revealed something ES-001 §4 does not yet express. Each is a **proposal to resolve**, not a decision — changing a screen takes minutes; changing a schema after eight Work Orders build on it is a migration.

---

## Load-bearing (a screen already depends on the answer)

### G-1 · `origin.segments` has no value for the untouched default clip
ES-001 §4.1 allows `origin.segments ∈ {proposed, user}`. But **before any proposal is run or any edit is made**, the effective segment is the whole clip — set by neither the machine nor the human. The prototype defaults it to `"user"`, which misrepresents "system default, untouched."
**Proposed:** add a third origin value (`"default"` / `"initial"`), or state the rule "full clip until first proposal, origin omitted/`default`." Touches the §4.1 invariant "every mutation writes origin."

### G-2 · No project display name
§4.1 `project.json` has no human name/title. Every screen header wants one ("Import review — *Beach Day*"). The prototype carries a name in memory and drops it (nothing persists).
**Proposed:** add `project.json.name: string` (display-only), or make the rule explicit that `media_root` basename is the display name.

### G-3 · No source display label
§4.2 `SourceIndex` has `path` but no label. The prototype derives a label from the path basename for every clip card. Works, but it's an undocumented UI dependency on `path` shape.
**Proposed:** document "basename(path) is the display label," or add `SourceIndex.label`.

### G-4 · Default `included` / `origin.included` for an unreadable source
For `readable:false`, what are `included` and `origin.included`? An unreadable clip cannot render, so the prototype forces `included:false` — but marks `origin.included:"user"` though the user didn't choose it (same root cause as G-1: no system origin).
**Proposed:** rule — unreadable ⇒ `included:false`, `origin.included:"default"` (pending G-1); the UI blocks including it.

### G-5 · Multi-mode export vs single `last_render`
§4.1 `export.last_render` is a single object, but `export.audio_modes` is a list and the flow renders one file per chosen mode (prototype produced `…-music.mp4` **and** `…-clip.mp4`). One `last_render` can't describe two outputs.
**Proposed:** make `last_render` a map/array keyed by `audio_mode` (one QA + path per mode).

## Flow / gate shape

### G-6 · Manual curation has no approval gate slot
§7 `stage_approvals` = `{ingest, trim, selection(M2), speed(M3), finalize}`. In M1 `selection` is inert, so manual curation (ADR-009) has **no gate of its own** — the prototype folds it into the ingest→trim transition with no recorded "curation approved" timestamp.
**Proposed:** decide explicitly — either (a) curation is free-form editing with no gate (document it), or (b) add a `curate` approval timestamp. Affects the "five gates across nine stages" framing.

### G-7 · The "nine-stage pipeline" is not enumerated in ES-001
CLAUDE.md and the framing reference a "nine-stage pipeline"; ES-001 names the **five gates** but does not list the nine stages. The prototype's stepper had to invent an ordering (Create · Sources · Import · AI-select · Curate · AI-trim · Speed · Finalize · Export).
**Proposed:** enumerate the canonical nine stages in ES-001 so the UI and the gate set agree by reference, not by invention.

### G-8 · No persisted "current stage" for resume
`project.json` records approval *timestamps* but no pointer to where the user is in the flow. Reopening a saved project can't return them to the stage they left (the prototype keeps stage in memory only).
**Proposed:** either derive the resume point from `stage_approvals` (define the rule) or add a `ui_state.current_stage` (explicitly non-authoritative, excluded from the round-trip invariant).

## Minor / confirm-only

### G-9 · Is the 1.0 s minimum window a proposer rule or a hard timeline rule?
§5.2 rule 5 sets a 1.0 s minimum for *proposals*. The prototype also enforces it on **user adjust**. Confirm whether a human may trim below 1.0 s or the floor is universal.

### G-10 · Stage navigation should reset scroll / show stage entry cleanly
Not a schema gap — a UX note surfaced while walking it: moving between stages keeps the prior scroll position. WO-107/108 should reset scroll on stage change. Recorded here so it isn't lost.

---

## What the prototype confirmed works as specified (no change needed)
- The `disposition` model (ADR-010): `pending → accepted` on stage approval; `adjusted` on drag; `dismissed` on remove; retained `proposals.segments` throughout. The finalize "kept 8 / dismissed 1" snapshot reads straight from `disposition`.
- `origin` flips to `user` on every human edit; re-run is the only overwrite path.
- `deleted` as a flag with exact restore; `order` dense/unique after reorder.
- Unreadable sources surfaced, never dropped.
- Three audio modes incl. the clip-mode silent-pad note when a silent source is present (§8.2).
- Faked ~5-minute analysis and render waits with the real figure always shown (ADR-008 rule 1).
- Deliberately-bad proposals (`KEPT_SHARPEST` cutting the good middle; `NO_CLEAR_WINDOW` full-clip fallback) are reviewable and fixable (ADR-008 rule 2).
