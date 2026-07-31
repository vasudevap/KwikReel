# KwikReel

An **explainable, local-first, human-directed first-draft reel editor** for
private family footage. It reads a folder of clips, proposes where to trim and
where to speed up, and the person editing accepts, adjusts or ignores any of it.

Not an autonomous editor, and not a claim of editorial intelligence. It runs as
a local web app on a Mac; original footage is opened read-only and never leaves
the device.

## Status — honest version

**The ADP-002 backend is realigned to the accepted spec and closed. The narrow
WO-123a frontend-operability API correction, WO-125 rack design system and
WO-126 shared app kernel are merged locally; the six product modules remain
honest placeholders. Nothing has ever run against real footage.**

- The pipe runs end to end **on synthetic fixtures**: ingest → analysis → trim
  proposal → render → QA → export, behind a local HTTP API with its security
  guards. Every ADP-002 synthetic gate passes; parts of the whole suite are
  **deliberately red** in legacy integration tests withheld to WO-134 —
  [handoff.md](handoff.md) has the exact state.
- The frontend was deleted on 2026-07-28 when a 26-version design exploration
  landed on a materially different product. Rebuilding it against that design is
  authorized locally on mock/synthetic state under
  [ADP-003](docs/implementation-plans/ADP-003-v3z-rack-frontend.md). Amendment 1
  added WO-123a as the first barrier; it now exposes and guards the required
  reject, reversible-bin, Log, music-probe and root-confined link-repair
  operations. WO-125 provides the typed v3z rack primitives, fixed geometry and
  embedded visual assets. WO-126 adds the six-state one-view shell, typed module
  slots, mock/live client boundary and ordered optimistic writes with visible
  conflict recovery. WO-127 – WO-132 now own the actual product modules.
- **No experiment has ever run and no real footage has ever been processed.**
  Every claim in [EVIDENCE-LEDGER.md](docs/specs/EVIDENCE-LEDGER.md) is graded
  `assumed`. That the code passes its tests establishes that it works, not that
  any belief about the product is true.

[handoff.md](handoff.md) is the current state in detail.

## How control works

There are four controls — **Sources · Trim · Speed · Save** — and no approval
gates. Trim and Speed are reversible assists that apply to every clip at once
and **never touch a clip edited by hand**. That property, not a checkpoint, is
what keeps the person editing in charge, so it is a tested requirement rather
than a described behaviour.

Every proposal records a plain-language reason, and those reasons are written to
the rig's Log — the audit trail for what the machine proposed and what was done
about it.

## Thesis

Strong AI products are **governed systems**: deterministic where possible,
probabilistic where useful, measurable throughout, privacy-aware by default, and
reversible in their actions. The differentiator **under test** is transparent,
reversible, auditable, local-first assistance — not autonomous judgment, and not
a black box.

That incumbents (Apple Photos, Google Photos, CapCut, Quik) already ship free
one-tap montage-to-music is treated as **fact**, not a gap to claim. Whether
anyone values explanation and control enough to review a first draft rather than
take the one-tap version is an **open belief**, and it is graded `assumed`.

## The normative documents

| Document | What it is |
|---|---|
| [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md) | The guardrails — privacy, what may never be committed, licensing, local delivery security. Binding. Changeable only through the path its own *How a constraint changes* clause defines |
| [SPEC.md](SPEC.md) | The product and the frozen contract. Outranks everything except the constraints |
| [docs/DECISIONS.md](docs/DECISIONS.md) | The dated, append-only decision log |
| [handoff.md](handoff.md) | What exists right now |

**[docs/archive/](docs/archive/) is history and may not be cited as authority** —
that is where all thirteen ADRs, the previous specification, and the superseded
backlogs live. Several contradict each other, which is why they were archived. A
citation of the form "(ADR-006)" anywhere in this repository refers to history,
never to a live rule.

## The design files are not in this repository

The mockups that define the product's look and feel are **deliberately
gitignored**. They exist on the owner's machine and nowhere else. Documents here
cite them by path, so those particular links resolve locally and not on GitHub —
that is intended, not an oversight.

## Commercial posture

Conditional and deferred — a validation and portfolio project first.
Auto-assembly and beat sync are commodity; the most-wanted feature (Instagram
songs) is legally unavailable to any third party; usage is 2–6 occasions a year.
Known headwinds are recorded in the
[risk register](docs/research/risk-register.md), not planned against.
