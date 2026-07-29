# KwikReel — session instructions

Read `../_oversight/DELIVERY-PLAYBOOK.md`. We follow it for this project.

An **explainable, local-first, human-directed first-draft reel editor** for
private family footage — not a claim of autonomous editorial intelligence. It
runs as a local web app on a Mac. The AI proposes a first pass at the edit; the
human reviews it and overrides anything.

## Read these, in this order

1. **[docs/CONSTRAINTS.md](docs/CONSTRAINTS.md)** — the guardrails. Normative,
   binding, each one a stop-and-ask. Privacy, what may never be committed,
   licensing, local delivery security. **Do not restate them elsewhere; cite
   this file.**
2. **[handoff.md](handoff.md)** — what exists right now.
3. **[SPEC.md](SPEC.md)** — the product and the frozen contract. **Accepted
   2026-07-28.** The single normative document; it outranks everything except
   `CONSTRAINTS.md`. Its §14 lists the four things it does not yet settle.
4. **[docs/DECISIONS.md](docs/DECISIONS.md)** — the v3z departures, **decided
   2026-07-28.** The record `SPEC.md` was written against.
5. **[docs/implementation-plans/ADP-002-contract-v2-and-backend.md](docs/implementation-plans/ADP-002-contract-v2-and-backend.md)**
   — the live authorization, and the Work Order set with its gates. **Authorized
   2026-07-28** for WO-117 – WO-119 and WO-121 – WO-124, **local build to green
   on synthetic fixtures only.** Its §3 is the list of what is still withheld.
6. **[docs/implementation-plans/PLAN-v3z-rebuild.md](docs/implementation-plans/PLAN-v3z-rebuild.md)**
   — the plan that got us here. Largely discharged; kept for the parts ADP-002
   does not carry. Where it disagrees with `SPEC.md`, `SPEC.md` wins.
7. **`docs/design-claude/README.md`** — the v3z design, which is the frozen
   frontend baseline. **Local only — gitignored and not in the public repo**
   (see below).

`ROADMAP.md` and `PROJECT.md` are **not** on this list. Both carry supersession
banners: the roadmap's milestones are retired outright, and `PROJECT.md`'s
framing stands while its mechanism does not.

## The design files are not in the repo

`docs/design-claude/` and `docs/archive/design-claude/` hold v3z and its 25
predecessors. They are **gitignored by decision** — the mockups are the
product's look and feel, and the repository is public. They exist on the
owner's disk and nowhere else.

Documents here cite them by path because that is where they are. Those links
resolve locally and not on GitHub, which is intended, not an oversight. **Do
not "fix" it by committing them.**

## The archive rule

**Nothing in `docs/archive/` may be cited as authority.** That is where the
superseded record lives — all thirteen ADRs, ES-001, the v3s alignment register,
the v3t brief, the M1 backlog, ADP-001, and mockups v1–v3y. Reading them to
understand how the project got here is fine. Treating them as a source of
requirements is not: several contradict each other (D-04 reversed by O-18, D-07
by O-26, O-8 by O-20), which is exactly why they were archived.

To use something from the archive, **promote it into a live document first** —
`docs/CONSTRAINTS.md` for a guardrail, `SPEC.md` for product or contract
behaviour — and cite that.

## Where the project is (2026-07-28)

**A working M1 exists, built against a design that has been replaced.** The
backend pipe runs end to end on synthetic fixtures: ingest → analysis → trim
proposal → render → QA → export, behind an HTTP API with its security guards.
67 tests pass. **No experiment has ever run and no real footage has ever been
processed** — every claim in `docs/specs/EVIDENCE-LEDGER.md` is graded `assumed`.

**The frontend is gone.** A 26-version design exploration ended at **v3z**, which
is a different product: no approval gates, no staged pipeline, speed pulled into
one release, audio as two mix levels, no clip rename, no reasons on the editing
surface. The old frontend was deleted in the 2026-07-28 clean cut. (`disposition`
is the one v3z removal the owner reversed — see DECISIONS A-3.)

**The decision session is done** ([docs/DECISIONS.md](docs/DECISIONS.md)) **and
`SPEC.md` is accepted** (2026-07-28). Together they are the whole normative
record for the rebuild, under `CONSTRAINTS.md`. Neither is to be amended backward
from the archived ES-001; amending inherits the ghosts the clean cut removed.

**Implementation is authorized, narrowly.** ADP-002 grants WO-117 – WO-119 and
WO-121 – WO-124: **local build to green on synthetic fixtures.** Still withheld
and still stop-and-ask — **every push to `origin`**, CI, **any run against real
footage** (needs an ADR-002 consent record first), amending `SPEC.md`, and
**WO-120, the speed proposer**, which waits on `SPEC.md` §14 SO-1.

## Working discipline

The discipline that matters is in [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md).
Two points bear repeating here because they shape how sessions run:

- **Preserve the distinction between proposed, accepted, and implemented.** A
  document describing a thing is not the thing. This repository has repeatedly
  had far more specification than code.
- **Stop / de-scope triggers are real.** Firing one is a successful outcome, not
  a problem to argue around.
