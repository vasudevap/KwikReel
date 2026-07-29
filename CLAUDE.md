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
3. **[SPEC.md](SPEC.md)** — the product and the frozen contract. **Draft, pending
   owner acceptance.** Once accepted it is the single normative document and
   outranks everything except `CONSTRAINTS.md`.
4. **[docs/DECISIONS.md](docs/DECISIONS.md)** — the v3z departures, **decided
   2026-07-28.** The record `SPEC.md` was written against.
5. **[docs/implementation-plans/PLAN-v3z-rebuild.md](docs/implementation-plans/PLAN-v3z-rebuild.md)**
   — the plan for the work in front of us. Proposed, not authorized.
6. **[docs/design-claude/README.md](docs/design-claude/README.md)** — the v3z
   design, which is the frozen frontend baseline.

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
M1, audio as two mix levels, no proposal `disposition`, no clip rename, no
displayed reasons. The old frontend was deleted in the 2026-07-28 clean cut.

**The decision session is done** ([docs/DECISIONS.md](docs/DECISIONS.md)). The
next artifact is **`SPEC.md`** — the single normative product and contract
document, which does not exist yet. It is to be written **forward from v3z and
DECISIONS.md**, never amended backward from the archived ES-001; amending
inherits the ghosts the clean cut just removed.

**No implementation beyond WO-116 is authorized.**

## Working discipline

The discipline that matters is in [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md).
Two points bear repeating here because they shape how sessions run:

- **Preserve the distinction between proposed, accepted, and implemented.** A
  document describing a thing is not the thing. This repository has repeatedly
  had far more specification than code.
- **Stop / de-scope triggers are real.** Firing one is a successful outcome, not
  a problem to argue around.
