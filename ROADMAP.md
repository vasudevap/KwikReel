# Roadmap — AI Vacation Reel Agent

**Status:** **Accepted — owner-approved 2026-07-23.** Rewritten 2026-07-23 for the pivot to a human-directed, approval-gated editor.
**Governing:** `_oversight/DELIVERY-PLAYBOOK.md` (normal Direction → Specification → build flow); build method locked by **ADR-006**; form factor by **ADR-005**.

**Sequencing change from the previous draft.** The previous roadmap was validation-first: a pivotal ranking experiment gated everything, because the product's value rested on a model out-selecting a human. The pivot removed that autonomy — every assist is now a proposal the user approves — so there is no single pivotal capability to pre-validate. Validation-first is retired by ADR-006 along with `VALIDATION-PLAN.md`, the pivotal experiment, and the ranking corpus. **No experiment ever ran.**

## Build order is not runtime order

The user experiences nine stages in order. We **build them in a different order on purpose**: mechanically simpler, higher-certainty capabilities first, and the assists layered on afterwards.

This produces a property worth stating explicitly: **because the manual capability is built before the assist that proposes it, every assist has a natural baseline — the user's own manual behaviour.** How often a proposal is kept, adjusted, or discarded is measured directly against what the user does by hand. That replaces the retired formal heuristic-baseline A/B with something cheaper, continuous, and more honest.

A working product exists at every milestone from M3 onward.

## Milestones

| # | Milestone | Runtime stages | Scope | Exit criteria |
|---|---|---|---|---|
| **M0** | **Direction close** | — | `PROJECT.md` + this roadmap accepted; ADR-005/006 accepted; owner authorizes an ADP | Owner accepts both documents and authorizes implementation |
| **M1** | Import & project spine | 1, 9 | Ingest user-selected clips + one track; probe duration/timestamp/orientation/codec; build preview proxies; report unreadable items; `project.json` save/load round-trip | Import a real folder, save, reopen, and see identical state |
| **M2** | Timeline & manual edit | 5, 6 | Clips laid out in sequence (chronological default) with the music track; select a clip to set trim in/out and speed by hand; delete; **restore a deleted clip** | Owner hand-edits a real day's footage end to end on the timeline |
| **M3** | **Finalize & export** | 7, 8 | Explicit Finalize renders a draft cut to the track; output QA (not black/silent/truncated, duration, safe-title margins); export 1080×1920 H.264/AAC **with and without music** | **First shippable thing: a complete manual reel editor.** Owner produces a reel they'd post |
| **M3.5** | **Real-user check** | — | A small number of real users edit their own footage with the manual editor | Convenience signal measured against their current CapCut/iMovie workflow. **Stop-trigger 1 checked here** |
| **M4** | Trim assist | 3 | Quality/duplicate/static analysis proposes in/out per clip, each with a plain-language reason; user confirms or adjusts before the stage advances | Proposed trims kept or minor-adjusted on a majority of clips, measured against M2 manual behaviour |
| **M5** | Speed assist | 4 | Beat/section detection (librosa, ADR-003) + motion/audio/scene signals propose speed ramps — faster through low-interest spans, slower on key moments; beat-aligned on opt-in | Proposed ramps kept on a majority of clips; cuts/ramps land near a beat when sync is on, never forced |
| **M6** | Selection & ordering assist | 2 | A legible heuristic proposes which clips to include and their sequence, with a reason for every pick **and every rejection**; user reviews, reorders, and approves | Proposed selection kept or lightly adjusted; reviewing it beats selecting from scratch |
| **M7** | **Real-user check, assisted** | — | The same users run the fully assisted flow on their own footage | One-sitting completion signal. **Stop-triggers 1 and 2 re-checked** |
| — | *Future* | — | Filters; ML-based interestingness; NLE export; packaging and distribution | Each requires its own decision; none is authorized here |

No milestone authorizes the next until its exit criteria are met and the owner approves. Every gate may return **stop** or **de-scope**, and doing so on evidence is a successful outcome.

## The assist milestones are individually disposable

M4, M5, and M6 each sit on top of a manual capability that already works. If an assist is wrong often enough that reviewing and correcting it costs more than doing that step by hand, **that stage ships manual-only** — still transparent, still gated — and the AI is dropped from it (ADR-006). The product survives the loss of any assist, or of all three.

M6 is sequenced last because it is the most ambitious: cross-clip judgment is the capability the previous roadmap treated as pivotal. Placing it after a working editor means it is a genuine enhancement rather than a precondition.

## Stop / de-scope triggers

From `PROJECT.md`, locked by ADR-006, checked at the milestone boundaries named above:

1. **No convenience win.** Finishing a reel takes as long as the manual CapCut evening → conclude as a portfolio piece. *(Checked at M3.5 and M7.)*
2. **An assist is net-negative** → de-scope that stage to manual. Stage-level, not project-level. *(Checked at M4, M5, M6.)*
3. **Absorption.** A platform ships this same transparent, approvable, clip-by-clip staged flow → reassess differentiation. More platform *automation* is explicitly not a trigger. *(Re-checked at every milestone close.)*

## The drift risk this roadmap carries

Validation-first guarded against apparatus quietly becoming product. That risk is gone; a different one replaces it. **Owner approval is the acceptance gate at M1–M6, and approving one's own work reliably overestimates its quality** (ADR-006). M3.5 and M7 exist specifically to counter that, and they are not optional: until real users other than the owner have edited their own footage, no claim about convenience or acceptance is evidence.
