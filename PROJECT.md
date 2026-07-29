# Project — KwikReel

**Status: current as of 2026-07-29.** Direction, not mechanism.
**Guardrails:** [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md).
**Governing methodology:** `_oversight/DELIVERY-PLAYBOOK.md`.

> **This file no longer describes how the product works.** It used to carry a
> nine-stage pipeline table, five approval gates and three audio modes, all
> retired on 2026-07-28 by [DECISIONS.md](docs/DECISIONS.md). Restating
> mechanism here is what let this file rot while the product moved, so the
> mechanism sections are gone rather than corrected. **[SPEC.md](SPEC.md) is the
> mechanism** — what the product does, its contract, its assists, its gates on
> quality. This file keeps what SPEC deliberately does not cover: why the
> project exists, who it is for, what counts as success, and when to stop.
>
> **No ADR is live.** All thirteen are archived; ADR numbers below refer to
> history, never to authority.

## Framing

Build an **explainable, local-first, human-directed first-draft reel editor for
private family footage.** The system proposes a transparent first pass at the
edit — **where to trim, where to change speed** — and the human reviews every
proposal and overrides anything. The AI proposes; the human decides.

Three words are load-bearing. *Human-directed* — the user makes every editorial
decision. *Assisted* — the heavy first pass is done for them, as a starting
point. *Transparent* — every trim and speed change carries a plain-language
reason and is auditable.

**How "the human decides" is enforced changed on 2026-07-28.** It used to be a
workflow step: five approval gates the user clicked through. It is now a
property of the controls — the assists are reversible, and they never touch a
clip the user edited by hand ([SPEC.md](SPEC.md) §3.1, §4.4). That is a tested
requirement rather than a described behaviour, which is the stronger form: a
gate clicked through by habit protects nobody.

## Problem

Turning a day's vacation clips into a reel you're proud to post still costs a
tedious evening in CapCut or iMovie. The **mechanical grind** is what the
memory-keeper resents: scrubbing each clip for the usable few seconds, timing
speed changes so the boring parts fly by and the good moments land, and redoing
it all when one change throws off the rest.

**What is already served, and must not be claimed as a gap.** Fully automated
assembly-to-music is commodity: Apple Photos Memory Movies, Google Photos
Highlight Videos, CapCut AutoCut, GoPro Quik. They are free, fast, pre-installed
— and they take control *away* and explain nothing. You get a montage, not a say
and not a reason.

**The candidate gap:** a tool that does the heavy first pass *and shows its
work*, while keeping the human in control and able to overturn any of it — trim
and speed, each with a recorded rationale, on a convenient timeline, every
decision reversible, the whole project saved and re-editable. The differentiator
is **transparent, reversible assistance — not autonomous judgment, and not a
black box.** This is a hypothesis until real users confirm they value it over
one-tap automation.

This reframing also lowers platform-absorption risk: incumbents are racing
toward *more* automation and *less* visibility — the opposite direction.

## Primary user

The **memory-keeper parent**: 30–50, shoots on iPhone, captures 20–100 clips per
vacation day, owns an Apple Silicon Mac, wants to share a reel with family and
friends. Currently either never edits, or burns 2–4 evening hours in
CapCut/iMovie once per trip.

**Job:** "Turn today's footage into a shareable 60–90 second reel in one sitting
— with the app doing the grunt work, but every call still mine to change."

**Quality bar:** proud to post. Better than an Apple Memory *because I directed
it and can see how it was built*.

Deliberately not targeted: professional creators (have NLEs and standards this
won't meet); users who genuinely want one-tap automation (well served by
Apple/Google/CapCut); action-camera users (Quik).

## Product promise

Propose and record a reason for every proposal; never publish automatically;
never destructively modify or discard originals; never overwrite an edit the
user made by hand. Every trim and speed change is reversible, and the entire
project is save-able and re-editable later.

## Scope

**The mechanism is [SPEC.md](SPEC.md) §1 and §2.** In one line: four controls —
Sources, Trim, Speed, Save — over one screen, in a single release.

**Out of scope, and these are the ones that keep getting proposed back in:**

- **Choosing which clips belong in the reel.** Cancelled permanently
  (DECISIONS A-5b), not deferred. The machine only ever adjusts timing within
  clips the user chose. This was once the project's central bet; it is now
  deliberately not attempted.
- **Face recognition or person identification of any kind.** Assists may detect
  and count people, never identify them. A guardrail, not a scope call — see
  `CONSTRAINTS.md`.
- Cloud processing of originals · commercial Instagram music · filters ·
  multiple editorial styles · opaque preference learning · publishing of any
  kind.

**Baseline for the assists: deterministic and transparent first.** For trim,
quality and static detection; for speed, motion energy and audio level. ML-based
"interestingness" is a later enhancement, not a first release.

## Success measures

Primary bar: **control plus a good starting point.** Success is not minimising
the user's edits — editing is the point — it is that the assists give a
good-enough, recorded start that a proud reel is finished **in one sitting, in
the user's control**, without dropping back to CapCut.

| Area | Measure | Goal |
|---|---|---|
| **One-sitting completion** | User reaches a reel they'd post, in a single session | **primary signal** |
| Starting-point quality | Proposed trims kept or minor-adjusted | majority of clips |
| Starting-point quality | Proposed speed ramps kept | majority of clips |
| Transparency | Every trim and speed change has a reason a user finds legible in the Log | required |
| Convenience | Import → finished reel, wall-clock | materially faster than the manual CapCut evening |
| Control & safety | Every proposal overridable; removal reversible; a hand edit never overwritten; project round-trips losslessly | required |
| Render fidelity | Exported reel matches the preview | within tolerance |
| Throughput | Analysis and final render on a 50-clip day, Apple Silicon | a few minutes each |

These are product-acceptance goals checked as the product is built, not
pre-registered thresholds. **"Kept" is measured at export** — every AI value not
adjusted or rejected by then counts as accepted, and the export writes the count
to the Log (DECISIONS A-3b, [SPEC.md](SPEC.md) §4.5). That summary is the whole
instrument for judging whether the assists earn their place; without it the
*assist is net-negative* trigger below cannot fire on evidence.

**Music sync is not measured, because it is not built.** Beat and section
detection are deferred.

## Reasons to stop or de-scope

Checked at real milestones, not pre-committed. Concluding on evidence remains a
successful outcome.

1. **No convenience win.** If finishing a reel with the tool takes as long as
   the CapCut evening on real footage, it has no reason to exist over free tools
   → conclude as a portfolio piece.
2. **An assist is net-negative.** If trim or speed is wrong often enough that
   reviewing and fixing it costs more than doing it by hand, ship that part
   manual-only and drop the assist. Recorded honestly, not argued around.
   **Speed is sequenced last precisely so this trigger can fire on it cheaply**
   (DECISIONS A-5a).
3. **Absorption (diminished risk).** If a platform ships this same transparent,
   reversible, clip-by-clip flow, reassess differentiation. More platform
   automation is not a threat here — it is the opposite of this product.

> **One trigger got harder to fire.** With the staged roadmap retired (A-5c)
> there is no milestone boundary at which de-scoping is naturally considered.
> These have to be checked deliberately now, or they will not be checked.

## Commercial posture

Conditional and deliberately deferred. This is a validation-and-portfolio
project first. Known headwinds are recorded now so they are not rediscovered
later: usage is 2–6 occasions per year (hostile to subscriptions); the free
automation floor is high and improving; and the most-requested feature, real
Instagram music, is legally unavailable to any third party. Plausible models if
evidence ever supports one: one-time Mac purchase, or pay-per-render. Recorded
in the risk register, not planned against.

## Portfolio intent

This project also demonstrates **architecture-led AI product delivery**: how an
ambiguous AI idea becomes an evidence-led, governed system rather than a polished
UI on untested assumptions. Two mid-flight reversals are part of that record —
the 2026-07-23 pivot away from autonomous ranking, and the 2026-07-28 removal of
the approval gates that pivot introduced. Both were absorbed by superseding the
record rather than letting it drift.

## Open assumptions

Graded per the playbook's evidence discipline. **Nothing below is measured, and
no experiment has ever run** — see [EVIDENCE-LEDGER.md](docs/specs/EVIDENCE-LEDGER.md),
where every claim is graded `assumed`.

- **Assumed (pivotal):** users prefer transparent, reversible assistance to
  one-tap automation. The whole product rests on this. Untested, and the binding
  real-user check is owed before the product is called *good*.
- **Assumed (adoption):** the pre-value workflow — moving iPhone clips into a
  Mac folder and supplying a rights-cleared track before any result — is
  tolerable to a real user. Tolerable to the owner; a named adoption risk.
- **Hypothesis:** deterministic trim detection is a helpful starting point.
  Untested — and it spent weeks resting on a proposer that mislabelled every
  landscape clip before that was found and fixed.
- **Hypothesis:** rules-based speed ramping reads as intentional rather than
  cheap. Untested, least certain of the assists, and sequenced last for that
  reason.
- **Hypothesis:** a local web app with a local FFmpeg backend gives acceptable
  preview and render performance on Apple Silicon. Partly measured for playback
  ([SPEC.md](SPEC.md) §6); unmeasured on real footage end to end.
- **Retired assumption:** that a legible selection heuristic could make a
  trusted first pass at *which clips to include*. Never tested; the assist was
  cancelled instead (A-5b).
