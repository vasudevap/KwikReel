# Project — AI Vacation Reel Agent

**Status:** **Accepted — owner-approved 2026-07-23; amended 2026-07-24 (pre-ADP course correction — ADR-009/010/011/012/013).** Supersedes the prior ranking-centric draft (pivot 2026-07-23).
**Governing methodology:** `_oversight/DELIVERY-PLAYBOOK.md`, normal flow (Direction → Specification → incremental staged build). Validation-first sequencing and the PROP-01 pilot are **retired** for this project by ADR-006 (Accepted 2026-07-23); ADR-001's CLI-first prototype shape is superseded by ADR-005 (Accepted 2026-07-23). ADR-002 (privacy) and ADR-003 (music/licensing) stand. This project is at **Stage A — Direction (re-opened by the pivot)**. No implementation, media collection, or remote repository is authorized.

## Framing

Build an **explainable, local-first, human-directed first-draft reel editor for private family footage.** The system proposes a transparent first pass at the whole edit — **which clips, in what order, where to trim, where to change speed** — and the human reviews every proposal, overrides anything, and **approves each machine-proposing stage before the next runs — five approval gates (ingest, selection, trim, speed, finalize) across the nine-stage pipeline.** The AI proposes; the human decides.

Three words are load-bearing. *Human-directed* — the user makes every editorial decision, by approving or overriding. *Assisted* — the heavy first pass is done for them, as a starting point. *Transparent* — every pick, rejection, trim, and speed change carries a plain-language reason and is auditable. The **staged, confirmation-gated pipeline and the timeline where the user finishes the edit are the product;** the automated assists are what make that finishing fast.

> **Naming note.** The repository is `ai-vacation-reel-agent` and predates this framing. The name is retained to avoid breaking paths; wherever the product is described, the framing above governs. "Agent" here means a governed pipeline that *proposes at each stage and waits for approval*, not an autonomous editor that decides.

## What changed in this pivot (and why)

The previous draft bet the project on one hard capability used *autonomously*: that model-assisted cross-clip ranking could out-select a human well enough to be the product's entire reason to exist. That framing justified validation-first sequencing, a pivotal experiment, an annotated ranking corpus, and a locked kill criterion.

**The autonomy is gone — not the ranking.** Ranking and selection stay, but **demoted to a transparent proposal the user reviews and approves,** sitting under the same per-stage gate as every other assist. Consequences:

- **Scope shifts.** Speed ramping moves from out-of-scope to a **core stage**; an interactive timeline UI moves from deferred to **central**; ranking/selection is **re-cast as a reviewable, approval-gated assist** rather than an autonomous engine; a full **audit trail** becomes first-class.
- **The product stops depending on the AI being *right*.** Every proposal is overridable; a weak assist is a worse *starting point*, not a broken product.
- **Validation-first can retire.** With an approval gate on every assist, there is no single pivotal capability to pre-validate — assists are proven per-stage as they are built.
- **Governance gets stronger, not weaker.** "Human-approved at consequential points" is now literally *every stage*.

## Architectural thesis

Strong AI products are **governed systems**: deterministic where possible, probabilistic where useful, measurable throughout, privacy-aware by default, reversible in their actions, and human-approved at consequential points. The six principles are defined in the playbook's *Governed-systems design principles* and cited by ADR rather than restated. After the pivot the human is present at every gate, and every machine proposal is explained — the thesis in its strongest form.

## Problem

Turning a day's vacation clips into a reel you're proud to post still costs a tedious evening in CapCut or iMovie. The **mechanical grind** is what the memory-keeper resents: scrubbing each clip for the usable few seconds, deciding which moments make the cut and in what order, timing speed changes so the boring parts fly by and the good moments land, nudging cuts to the music, and redoing it all when one change throws off the rest.

**What is already served, and must not be claimed as a gap.** Fully automated assembly-to-music is commodity: Apple Photos Memory Movies, Google Photos Highlight Videos, CapCut AutoCut, GoPro Quik. They are free, fast, pre-installed — and they take control *away* and explain nothing. You get a montage, not a say and not a reason.

**The candidate gap:** a tool that does the heavy first pass *and shows its work*, while keeping the human in control and able to approve or overturn every decision — assisted selection, ordering, trim, and speed, each with a visible rationale, on a convenient timeline, every decision reversible, the whole project saved and re-editable. The differentiator is **transparent, approvable assistance — not autonomous judgment, and not a black box.** This is a hypothesis until real users confirm they value it over one-tap automation.

This reframing also lowers platform-absorption risk: incumbents are racing toward *more* automation and *less* visibility — the opposite direction from this product.

## Primary user

The **memory-keeper parent**: 30–50, shoots on iPhone, captures 20–100 clips per vacation day, owns an Apple Silicon Mac, wants to share a reel with family and friends. Currently either never edits, or burns 2–4 evening hours in CapCut/iMovie once per trip.

**Job:** "Turn today's footage into a shareable 60–90 second reel in one sitting — with the app doing the grunt work and showing me why, but every call still mine to approve or change."

**Quality bar:** proud to post. Better than an Apple Memory *because I directed it and can see how it was built*.

Deliberately not targeted: professional creators (have NLEs and standards this won't meet); users who genuinely want one-tap automation (well served by Apple/Google/CapCut); action-camera users (Quik).

## Product promise

Propose and explain at every stage; never advance a stage without approval; never publish automatically; never destructively modify or discard originals. Every selection, rejection, trim, and speed change carries a plain-language reason and is reversible, and the entire project is save-able and re-editable later.

## Scope — the nine-stage pipeline

| # | Stage | System role | Gate |
|---|---|---|---|
| 1 | **Ingest** | User selects candidate clips + one music track. System inventories duration, timestamp, orientation, codec and builds preview proxies without touching originals; unsupported/corrupt items are reported. | → confirm |
| 2 | **Assisted selection & ordering** | System proposes which clips to include and their sequence (chronology-aware), each pick and each rejection carrying a plain-language reason. User reviews with full transparency, adds/removes/reorders, and **approves**. | → approve |
| 3 | **Trim assist** | System proposes in/out points keeping the usable part of each selected clip (trimming blur, shake, dead air, junk), each with a reason. | → confirm |
| 4 | **Speed assist** | System proposes speed ramps — faster through low-interest spans, slower on high-interest moments — aligned to the track's beats/sections where the user opts in. | → confirm |
| 5 | **Timeline** | Clips laid out in sequence with their trims, speeds, and the music track visible, alongside the rationale for each. | (presentation) |
| 6 | **Manual edit** | User selects any clip and changes trim in/out, changes speed, deletes it, or **restores a previously deleted clip**. Immediate and reversible. This is the product. | user drives |
| 7 | **Finalize** | An explicit "Finalize" action renders a draft reel cut to the music for review. Nothing renders without it. | → approve |
| 8 | **Export** | On approval, export 1080×1920 H.264/AAC in a **user-selectable audio mode — music, natural clip audio, or silent** (ES-001 §8.2). | |
| 9 | **Save / Load** | Project (clip order, selection, trims, speeds, deletions, music reference, rationale) saves to a re-openable file and reloads faithfully for later editing. | |

**Five approval gates, not nine.** The nine stages are the pipeline; the gates that hold the next stage are the five machine-proposing/consequential ones — **ingest, selection, trim, speed, finalize** (the `stage_approvals` keys in ES-001). Stages 5/6/9 (timeline, manual edit, save) are presentation or user-driven and gate nothing. **Manual curation (include/exclude/delete/restore) is available from M1** (ADR-009); the selection/order *assist* is M2.

**In scope:** AI-assisted **selection, ordering, trim, and speed-ramping**, each presented as a transparent, overridable proposal that requires user approval to proceed; an interactive **local web-app timeline editor**; music beat/section alignment for speed and cuts; a per-decision **audit trail**; lossless project save/reload; export in three audio modes (music, natural clip audio, or silent).

**Baseline for the assists:** deterministic and transparent first — for selection, a legible heuristic (duration, people **count** without identity, sharpness, motion energy, event coverage, chronology); for trim, quality/duplicate/static detection; for speed, motion energy, audio events, scene changes, and beat markers. ML-based "interestingness" is a **later enhancement**, not v1. Because the user selects freely at any time, the selection assist can start simple and improve after the mechanically simpler stages are working.

**Out of scope:** any selection, ordering, or publishing that proceeds **without user review and approval**; face recognition or person **identification** of any kind (assists may detect and count people, never identify them); cloud processing of originals; commercial Instagram music (ADR-003); **filters (a named future enhancement)**; multiple editorial styles; opaque preference learning.

## Success measures

Primary bar, per the pivot: **control + a good starting point.** Success is not minimizing the user's edits — editing is the point — it is that the assists give a good-enough, *explained* start that a proud reel is finished **in one sitting, in the user's control**, without dropping back to CapCut.

| Area | Measure | Goal |
|---|---|---|
| **One-sitting completion** | User reaches a reel they'd post, in a single session, every decision theirs to approve | **primary signal** |
| Starting-point quality | Proposed selection/order kept or only lightly adjusted | majority of clips |
| Starting-point quality | Proposed trims kept or minor-adjusted | majority of clips |
| Starting-point quality | Proposed speed ramps kept | majority of clips |
| Transparency | Every pick/rejection/trim/speed shows a reason a user finds legible | required |
| Convenience | Import → approved reel, wall-clock | materially faster than the manual CapCut evening |
| Control & safety | Every proposal overridable; delete reversible; project round-trips losslessly | required |
| Render fidelity | Exported reel matches the timeline (trim/speed/beat alignment) | within tolerance |
| Music sync | Speed changes / cuts near a beat when sync is on; never forced | ≥70% within ~150 ms |
| Throughput | Stage 2–4 analysis and final render on a 50-clip day, Apple Silicon | a few minutes each |

These are product-acceptance goals checked as each stage is built — **not** pre-registered pivotal thresholds (that regime retired with validation-first). "Kept or minor-adjusted" is read from each proposal's `disposition` (ADR-010): `accepted` + `adjusted-within-tolerance` = kept. The pivotal belief and the competitive floor get their own lightweight checkpoints (ADR-012 CP-1/CP-2), and the ≤5-min throughput target a perf spike (CP-3); none blocks the ADP (see ROADMAP).

## Reasons to stop or de-scope

Lighter than the prior kill criteria, checked at stage boundaries rather than pre-committed and ADR-locked. Concluding on evidence remains a successful outcome.

1. **No convenience win.** If finishing a reel with the tool takes as long as the CapCut evening on real footage, it has no reason to exist over free tools → conclude as a portfolio piece.
2. **An assist is net-negative (stage-level de-scope, not a project kill).** If any assist — selection, trim, or speed — is wrong often enough that reviewing and fixing it costs more than doing it by hand, ship that stage manual-only (still transparent, still gated) and drop that AI. Recorded honestly, not argued around.
3. **Absorption (diminished risk).** If a platform ships this same *transparent, approvable, clip-by-clip staged flow*, reassess differentiation. More platform automation is not a threat here — it is the opposite of this product.

## Commercial posture

Conditional and deliberately deferred. This is a validation-and-portfolio project first. Known headwinds are recorded now so they are not rediscovered later: usage is 2–6 occasions per year (hostile to subscriptions); the free automation floor is high and improving; and the most-requested feature, real Instagram music, is legally unavailable to any third party. Plausible models if evidence ever supports one: one-time Mac purchase, or pay-per-render. Recorded in the risk register, not planned against.

## Portfolio intent

This project also demonstrates **architecture-led AI product delivery**: how an ambiguous AI idea becomes an evidence-led, governed system rather than a polished UI on untested assumptions — and how a mid-flight pivot is absorbed cleanly through superseding decision records rather than drift. The artifact trail is a deliverable in its own right.

## Open assumptions

Graded per the playbook's evidence discipline. Nothing below is measured.

- **Assumed (pivotal to the pivot):** users prefer transparent, approvable assistance to one-tap automation. The whole product rests on this; checked cheaply and early via ADR-012 **CP-1** on the WO-100 prototype, and by the binding real-user gate before the product is called *good*.
- **Assumed (adoption):** the pre-value workflow — moving iPhone clips into a Mac folder and supplying a rights-cleared track before any result — is tolerable to a real user. Tolerable to the owner now; a named adoption risk (risk register).
- **Hypothesis:** a legible selection/ordering heuristic makes a helpful, trusted first pass — good enough that reviewing it beats selecting from scratch. Untested, and the most ambitious assist.
- **Hypothesis:** deterministic trim detection is reliable enough to be a helpful starting point. Untested.
- **Hypothesis:** rules-based speed ramping (motion/audio/scene + beats) produces speed changes that read as intentional and musical. Untested.
- **Hypothesis:** a local web app + local FFmpeg backend gives acceptable preview and render performance on Apple Silicon. Untested.
- **TBD:** exact selection and interestingness heuristics; preview/scrubbing approach; project-file format; whether NLE export is ever needed.
