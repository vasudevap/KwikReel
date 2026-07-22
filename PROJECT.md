# Project — AI Vacation Reel Agent

**Status:** Draft — owner approval required
**Governing methodology:** `_oversight/DELIVERY-PLAYBOOK.md`. The Validation stage this project uses (PROP-01) is **piloting on Vacation Reel Stage B only** per MD-001 (owner-accepted 2026-07-20); general acceptance is deferred to MD-002. This project is at **Stage A — Direction**. Stage B (Validation) is triggered and not yet started. No implementation is authorized.

## Framing

Build and validate an **explainable, local-first assisted first-draft editor for private family footage** — not a claim of fully autonomous editorial intelligence.

The word *assisted* is load-bearing. The system produces one defensible draft and an honest account of its reasoning; a human accepts, corrects, or rejects it. The review and correction path is the product. The automated pipeline is what makes the review cheap.

> **Naming note.** The repository is `ai-vacation-reel-agent` and predates this framing. The folder name is retained to avoid breaking paths; wherever the product is described, the framing above governs. "Agent" here means a governed pipeline that proposes, not an autonomous editor that decides.

## Architectural thesis

Strong AI products are **governed systems**: deterministic where possible, probabilistic where useful, measurable throughout, privacy-aware by default, reversible in their actions, and human-approved at consequential points.

This project is a test of that thesis on a domain where the probabilistic part is genuinely hard and the consequences of getting it wrong are personal rather than commercial. The six principles are defined in the playbook's *Governed-systems design principles* and are cited by ADR rather than restated here.

## Problem

Turning a day's worth of independently captured vacation clips into a satisfying, chronological Reel requires disproportionate manual review and editorial judgment. Existing editors automate the *mechanics* of finishing — cuts, templates, reframing, beat sync — but the user still chooses meaningful subclips, balances people and activities, and constructs the day's story.

**What is already served, and must not be claimed as a gap:** automated assembly-to-music is commodity. Apple Photos Memory Movies, Google Photos Highlight Videos, CapCut AutoCut, GoPro Quik, and pay-per-render services such as AidVid all produce a music-synced montage from a batch of clips, several of them free and pre-installed. Positioning this project as though generic automated montage creation were unserved would be false.

**The candidate gap** is narrower and harder: *explainable editorial judgment*. Chronology-aware event coverage, auditable selects and rejects with plain-language reasons, local-first privacy, recoverable decisions, and lightweight human correction. No incumbent output is reviewable — you get a montage, not an account of why those clips.

This gap is a **hypothesis, not a finding**. It is not established until the competitive floor is measured (EXP-001) and the ranking claim is tested (EXP-003).

## Primary user

The **memory-keeper parent**: 30–50, shoots on iPhone, captures 20–100 clips per vacation day, owns an Apple Silicon Mac, wants to share a reel with family and friends. Currently either never edits, or burns 2–4 evening hours in CapCut/iMovie once per trip and resents it.

Deliberately not targeted, and why: professional travel creators have workflows and standards this will not meet; casual creators are adequately served by CapCut templates; action-camera users belong to Quik; frequent business travellers do not make reels.

**Job:** "Turn today's footage into a shareable 60–90 second story of our day before the trip glow fades — without giving up an evening."

**Quality bar:** proud to post. Noticeably better than an Apple Memory; not Sundance.

## Product promise

Create an explainable draft; never publish automatically; never destructively discard originals; retain a recoverable audit trail for every selection and rejection.

## Validation scope

- 20–50 clips from one day, capped at 60; 60–90 second target; 9:16 H.264 draft.
- Local-first on Apple Silicon. Original media does not upload by default. A controlled, opt-in cloud-VLM-on-keyframes comparison is permitted solely to measure the quality/privacy trade-off, governed by ADR-002.
- One user-supplied royalty-free track. Instagram's licensed in-app music is a timing reference, not exportable media (ADR-003).
- Deterministic floor first: metadata, visual quality, duplicates, event grouping, beat markers, chronological constrained selection. Model-based judgment is layered on top and must beat that floor to earn its place.
- One draft, not several. Multiple drafts create decision fatigue and contradict the value proposition.
- User marks 3–10 "must-include" clips upfront. This is cheap insurance against ranking failure and is in scope from the first working version.
- Review via manifest, rendered draft, and lock/remove/restore/regenerate controls.

**Out of validation scope:** automatic speed changes (advisory flags only), multiple editorial styles, opaque preference learning, face recognition, commercial Instagram music, publishing, and polished interface work.

## Representative user stories and acceptance criteria

| Story | Acceptance criteria |
|---|---|
| Import a day | Given 20–50 common mobile clips, the system inventories duration, timestamp, orientation, and a proxy without modifying originals. Unsupported/corrupt items are reported. |
| Mark what matters | Before analysis, the user may mark 3–10 must-include clips. Marked clips are never rejected and their inclusion is recorded as user-declared, not inferred. |
| Understand quality | Each clip receives interpretable blur, exposure, shake, duration, and duplicate indicators; candidates are recoverably rejected, never deleted. |
| Preserve a story | Given dated clips, the proposed order is chronological by default and exposes event groups plus selected/rejected rationale. |
| Stay concise | Given a 60–90 s target, the selected timeline does not exceed it and records each duration/speed decision. |
| Edit to music | Given a local track, the draft includes beat/section markers and most cuts land within a defined tolerance of eligible beats; it does not force every beat. |
| Review safely | The user can inspect source-to-subclip provenance and regenerate after changing a lock, style, or target duration. Export requires explicit approval. |
| Export | A successful run renders a playable 1080×1920 H.264/AAC draft with safe-title margins and a JSON decision manifest. |

## Success measures

**North-star metric: corrections-to-acceptance** — the count of discrete changes a user makes before they would post the draft. Instrumented from the first working version, not retrofitted. Every other measure below is diagnostic; this one decides whether the product has a reason to exist. If correcting the draft costs as much as editing in CapCut, the pipeline is a demo rather than a product.

| Area | Measure | Target |
|---|---|---|
| **Acceptance** | **Corrections to acceptance, median** | **≤5** |
| **Acceptance** | **"Would post after tweaks", 1–10** | **≥7** |
| Ranking | Rank correlation vs. pooled human ranking | Spearman ≥0.6 **and beats the heuristic baseline** |
| Filtering | Must-keep recall / seeded-unusable precision | ≥95% / ≥80% |
| Duplicates | Duplicate pairs represented twice without justification | ≤10% |
| Chronology | Correct adjacent event transitions | ≥90% |
| Coverage | User-designated essential events represented | ≥80%; 100% of must-includes |
| Subclip | Overlap with human-chosen windows | ≥70% |
| Duration | Absolute error from target | ≤0.5 s, or a recorded shorter decision |
| Music | Eligible cuts near an allowed beat | ≥70% within 150 ms |
| Throughput | 50-clip day, end to end, Apple Silicon | ≤15 min |

All targets are **pre-registered thresholds**. Moving one after seeing a result is drift and is recorded as drift in the evidence ledger.

## Kill criteria

Pre-committed under the playbook's Stage A rule and locked by **ADR-004**. These can only be relaxed by a new ADR stating what changed. A project with no written stopping condition does not stop.

1. **Ranking fails to beat the baseline.** If model-assisted cross-clip ranking cannot outperform a transparent metadata/CV heuristic by a meaningful margin (EXP-003), the differentiating claim is false. Conclude as a portfolio proof of concept.
2. **Correction burden stays high.** If median corrections-to-acceptance exceeds 8 on real users' own footage (EXP-008), the review workflow costs what manual editing costs and the product has no reason to exist.
3. **Platform absorption.** If Apple or Google ships reviewable, explainable editorial reels natively, the remaining differentiation is gone. Re-measured at every phase close, not discovered late.

Firing a kill criterion is a **successful** use of the methodology. The project is explicitly funded to be able to conclude "the differentiating claim is false."

## Commercial posture

**Conditional and deliberately deferred.** This is a validation and portfolio project first. Productization requires evidence on four fronts — editorial quality, user acceptance, willingness to pay, and continued differentiation from platform incumbents — and no such evidence exists today.

The known headwinds are recorded now so they are not rediscovered as surprises: usage frequency is 2–6 occasions per year, which is hostile to subscription models; the free floor is high and improving each OS cycle; and the single most-requested feature, real Instagram music, is legally unavailable to any third party. Plausible models if evidence supports one at all: one-time Mac purchase, or pay-per-render. These are recorded in the risk register, not planned against.

## Portfolio intent

This project is also intended as a demonstration of **architecture-led AI product delivery**: how an ambiguous AI idea becomes an evidence-led system design, rather than a polished UI built on untested assumptions. The artifact trail — decisions with their reasoning, experiments with pre-registered thresholds, and honest verdicts including negative ones — is a deliverable in its own right. A kill decision reached on evidence demonstrates the thesis as well as a ship decision would.

## Open assumptions

Graded per the playbook's evidence discipline. Nothing below is measured.

- **Hypothesis (pivotal):** model-assisted ranking and subclip selection outperform a transparent metadata/CV heuristic baseline by enough to reduce corrections meaningfully. Untested; EXP-003 and EXP-004.
- **Hypothesis:** explainability and control, not montage quality, are what incumbents fail to provide. Untested; EXP-001 measures the competitive floor.
- **Hypothesis:** local Apple Silicon throughput is acceptable for a 50-clip day. Untested; EXP-007.
- **Assumed:** users prefer an assisted draft to full automation. Untested; EXP-009.
- **TBD:** target hardware specifics, local model licensing, music source, and whether NLE handoff is required at all.
