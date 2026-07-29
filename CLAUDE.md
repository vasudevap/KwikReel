# KwikReel — session instructions

Read `../_oversight/DELIVERY-PLAYBOOK.md`. We follow it for this project.

An **explainable, local-first, human-directed first-draft reel editor** for
private family footage — not a claim of autonomous editorial intelligence. It
runs as a local web app on a Mac. The AI proposes a first pass at the edit; the
human reviews it and overrides anything.

## Read these, in this order

1. **[docs/CONSTRAINTS.md](docs/CONSTRAINTS.md)** — the guardrails. Normative,
   binding, each one a stop-and-ask. Privacy, what may never be committed,
   licensing, local delivery security, and which actions need owner
   authorization. **Do not restate them elsewhere; cite this file.** Its *How a
   constraint changes* clause is the only legitimate amendment path.
2. **[handoff.md](handoff.md)** — what exists right now.
3. **[SPEC.md](SPEC.md)** — the product and the frozen contract. **Accepted
   2026-07-28.** The single normative document; it outranks everything except
   `CONSTRAINTS.md`. Its §14 records the four things it did not settle at
   acceptance — **all four now closed** (SO-1 2026-07-28; SO-2 – SO-4
   2026-07-29).
4. **[docs/DECISIONS.md](docs/DECISIONS.md)** — the v3z departures, **decided
   2026-07-28.** The record `SPEC.md` was written against, and the append-only
   log where any future decision goes.
5. **[docs/implementation-plans/ADP-002-contract-v2-and-backend.md](docs/implementation-plans/ADP-002-contract-v2-and-backend.md)**
   — the live authorization, and the Work Order set with its gates. **Authorized
   2026-07-28, amended through 2026-07-29,** for **WO-116a and WO-117 – WO-124,
   all unheld** — **local build to green on synthetic fixtures only.** Its §3 is
   the list of what is still withheld.
6. **[docs/implementation-plans/PLAN-v3z-rebuild.md](docs/implementation-plans/PLAN-v3z-rebuild.md)**
   — the plan that got us here. Largely discharged; kept for the ADP-003 and
   ADP-004 sequencing ADP-002 does not carry. Where it disagrees with `SPEC.md`,
   `SPEC.md` wins.
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
understand how the project got here is fine, and reading an archived ADR for the
*reasoning* behind a constraint is encouraged. Treating them as a source of
requirements is not: several contradict each other (D-04 reversed by O-18, D-07
by O-26, O-8 by O-20), which is exactly why they were archived.

To use something from the archive, **promote it into a live document first** —
`docs/CONSTRAINTS.md` for a guardrail, `SPEC.md` for product or contract
behaviour — and cite that.

**No ADR is live.** All thirteen are archived. A citation of the form "(ADR-006)"
in any document is a reference to history, never to authority — and if you find
one being used as a rule, that document is stale.

## Where the project is (2026-07-29)

**The backend rebuild is mid-flight under ADP-002.** Contracts (WO-117), ingest
(WO-116a) and the trim proposer (WO-118a) are v2 and merged; the WO-124 playback
spike has reported its numbers and the v3z design survived them. Store, media,
speed proposer, renderer, QA and the API are still v1 — WO-118, WO-119, WO-120
and WO-121 – WO-123 are dependency-ready and unstarted.

**The test suite is deliberately partly red** while the two halves speak
different schema versions. Read the warning box in `handoff.md` before treating
red as a regression, and run `pytest --continue-on-collection-errors` for the
whole-suite count — a bare `pytest` halts at the five expected import errors.

**`SPEC.md` §14 is fully closed** — SO-1 and SO-2 by owner decision, SO-3 and
SO-4 by measurement. **No experiment has ever run and no real footage has ever
been processed** — every claim in `docs/specs/EVIDENCE-LEDGER.md` is graded
`assumed`, and only ADP-004's real-footage run can move one.

**The frontend is a stub** — `main.tsx` and the generated types, nothing more.
Its rebuild is ADP-003: unblocked on the spec side, **not yet written or
authorized**. The 26-version design exploration ended at **v3z**, locked (A-8);
`disposition` is the one v3z removal the owner reversed (DECISIONS A-3).

**The decision session is done** ([docs/DECISIONS.md](docs/DECISIONS.md)) **and
`SPEC.md` is accepted** (2026-07-28). Together they are the whole normative
record for the rebuild, under `CONSTRAINTS.md`. Neither is to be amended backward
from the archived ES-001; amending inherits the ghosts the clean cut removed.

**Implementation is authorized, narrowly.** ADP-002 grants WO-116a and
WO-117 – WO-124, all unheld: **local build to green on synthetic fixtures.**
Still withheld and still stop-and-ask — **every push to `origin`**, CI, **any
run against real footage** (needs an ADR-002-style consent record first),
amending `SPEC.md`, and **any frontend work** beyond WO-117's generated types.

## Working discipline

The discipline that matters is in [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md).
Two points bear repeating here because they shape how sessions run:

- **Preserve the distinction between proposed, accepted, and implemented.** A
  document describing a thing is not the thing. This repository has repeatedly
  had far more specification than code.
- **Stop / de-scope triggers are real.** Firing one is a successful outcome, not
  a problem to argue around.

## More than one agent works in this directory

Codex, Antigravity and Claude Code sessions share this working tree, and they
have been active concurrently. Before you start, check `git log` and
`git status` rather than trusting a summary from earlier in your own session —
`HEAD` may have moved underneath you. Prefer small, committed increments over
long uncommitted edits, so a concurrent session does not lose your work or you
theirs.
