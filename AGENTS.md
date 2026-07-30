# KwikReel — session instructions

Read `../_oversight/DELIVERY-PLAYBOOK.md`. We follow it for this project.

This file mirrors `CLAUDE.md` so that Codex, Antigravity, and Claude Code
sessions operate under identical constraints. **If the two diverge, `CLAUDE.md`
is authoritative and this file is stale — say so rather than picking one.**

> **This file used to restate the constraints, and drifted.** It carried a "Hard
> constraints" list asserting five approval gates, staged progression, and "no
> assist may act without user approval" — all retired by
> [`docs/DECISIONS.md`](docs/DECISIONS.md) on 2026-07-28 — plus "no code and no
> media exist", which was false while a complete backend sat beside it. Sessions
> reading this file were being briefed on a product that no longer exists. The
> constraints are **not** repeated here any more; they are cited. Duplicating
> them is what allowed them to rot.

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
   — the closed backend authorization and its Work Order gates. **Authorized
   2026-07-28, amended seven times, closed 2026-07-30.** Amendment 7 retains the
   WO-124 harness through WO-127 for the foreground rerun `SPEC.md` requires.
6. **[docs/implementation-plans/ADP-003-v3z-rack-frontend.md](docs/implementation-plans/ADP-003-v3z-rack-frontend.md)**
   — the live frontend authorization. **Authorized 2026-07-30 and amended once**
   to add WO-123a before WO-125; scope is WO-123a and WO-125 – WO-132, local
   mock/synthetic implementation only.
7. **[docs/implementation-plans/PLAN-v3z-rebuild.md](docs/implementation-plans/PLAN-v3z-rebuild.md)**
   — the plan that got us here. Largely discharged; kept for the ADP-003 and
   ADP-004 sequencing ADP-002 does not carry. Where it disagrees with `SPEC.md`,
   `SPEC.md` wins.
8. **`docs/design-claude/README.md`** — the v3z design, which is the frozen
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

## Where the project is (2026-07-30)

**The ADP-002 backend rebuild is complete and ADP-002 closed 2026-07-30.** Contracts
(WO-117), ingest (WO-116a), the trim proposer (WO-118a), the store (WO-118), reject semantics
(WO-118b), the media services (WO-119), speed proposer (WO-120), renderer
(WO-121), output QA (WO-122), and API (WO-123) are v2 and merged; the WO-124
playback spike has reported its numbers and the v3z design survived them.
Every ADP-002 implementation Work Order is complete on its own synthetic gate.
Amendment 7 retains the spike harness only through WO-127 for `SPEC.md` §6.7's
required foreground rerun and deletion.

**WO-123a has closed the post-authorization frontend-operability seam.** Reject,
reversible binning, the persistent Log, music probing and root-confined
content-hash repair now have guarded server actions; the binding `Referer`
check is implemented. The focused security/API gates and the synthetic
create→scan→analyze→propose→control→export→Log flow pass.

**In v2 what renders is derived, never stored.** `backend/store/derive.py` is
`SPEC.md` §3.1 and §3.4 as code; `clip.segment` holds *the user's* trim and is
not what plays. Anything reading it as "the trim" has carried a v1 habit into v2.

**The test suite is deliberately partly red** while the two halves speak
different schema versions. Read the warning box in `handoff.md` before treating
red as a regression, and run `pytest --continue-on-collection-errors` for the
whole-suite count. **168 tests pass; three legacy integration tests fail and one
legacy integration module cannot import.** They are owned by withheld WO-134,
not an authorized ADP-003 lane. One real-footage integration gate remains
owner-gated and skipped.

**`SPEC.md` §14 is fully closed** — SO-1 and SO-2 by owner decision, SO-3 and
SO-4 by measurement. **No experiment has ever run and no real footage has ever
been processed** — every claim in `docs/specs/EVIDENCE-LEDGER.md` is graded
`assumed`, and only ADP-004's real-footage run can move one.

**The frontend is a stub** — `main.tsx` and the generated types, nothing more.
Its rebuild is ADP-003: entry gates met, **authorized 2026-07-30, amended once,
with WO-123a merged locally and frontend work not yet begun**. WO-125 is next.
The 26-version design exploration ended at **v3z**, locked (A-8);
`disposition` is the one v3z removal the owner reversed (DECISIONS A-3).

**The decision session is done** ([docs/DECISIONS.md](docs/DECISIONS.md)) **and
`SPEC.md` is accepted** (2026-07-28). Together they are the whole normative
record for the rebuild, under `CONSTRAINTS.md`. Neither is to be amended backward
from the archived ES-001; amending inherits the ghosts the clean cut removed.

**Implementation is authorized narrowly under ADP-003.** WO-123a and
WO-125 – WO-132 may build locally on mock/synthetic state in the §5 dependency
order; WO-123a is complete and WO-125 is next. The foreground harness rerun and
deletion are authorized only inside WO-127.
Still stop-and-ask: **every push to `origin`**, CI, **any run against real
footage** (needs an ADR-002-style consent record first), new dependencies,
amending `SPEC.md`, changing the frozen contract/design, or leaving §4's scopes.

## Working discipline

The discipline that matters is in [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md).
Two points bear repeating here because they shape how sessions run:

- **Preserve the distinction between proposed, accepted, and implemented.** A
  document describing a thing is not the thing. This repository has repeatedly
  had far more specification than code.
- **Stop / de-scope triggers are real.** Firing one is a successful outcome, not
  a problem to argue around.

## How work is recorded

The record rotted once — 24 commits of build while the briefing docs still
described the pre-build world (found and fixed 2026-07-29). These obligations
exist so that cannot happen quietly again. This list is single-sourced in
`CLAUDE.md`; this file mirrors it.

**When state changes, the record changes in the same commit:**

- **A Work Order merges** → `handoff.md`: the module table, the suite box,
  "In flight", and the stop-and-ask ledger.
- **An ADP is amended** → a dated owner note at the ADP's head **and** its §8
  authorization block **and** `handoff.md`. An amendment recorded in one place
  and not the others is exactly how ADP-002's §8 drifted to "amended twice"
  while its head recorded three.
- **A decision lands** → a dated, append-only entry in `docs/DECISIONS.md`.
  `docs/CONSTRAINTS.md` is edited to match only when a guardrail changed,
  citing the entry.
- **A claim's instrument or implementation reality changes** →
  `docs/specs/EVIDENCE-LEDGER.md`: the affected rows plus a dated log line.
  Grades move only as the ledger's own rules allow.
- **An ADP closes** → `handoff.md`, the ledger log, `README.md`'s status
  section, and the *Where the project is* sections here and in `CLAUDE.md`.
  Closeout writes the next ADP, which **inherits ADP-002 §7's execution rules
  and this recording discipline** unless it explicitly says otherwise.

**Session entry:** before building, check *Where the project is* against
`git log`; if they disagree, fix the record first. **Session exit:** if you
changed project state, leave every section above true.

The drift check that verifies all of this is
[`.claude/skills/align-check/SKILL.md`](.claude/skills/align-check/SKILL.md) —
Claude sessions invoke it as `/align-check`; other agents follow it as a
checklist. Run it at session start and whenever the record smells stale.

## More than one agent works in this directory

Codex, Antigravity and Claude Code sessions share this working tree, and they
have been active concurrently. Before you start, check `git log` and
`git status` rather than trusting a summary from earlier in your own session —
`HEAD` may have moved underneath you. Prefer small, committed increments over
long uncommitted edits, so a concurrent session does not lose your work or you
theirs.
