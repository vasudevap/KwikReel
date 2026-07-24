# Handoff

**Updated:** 2026-07-23 — **direction pivoted** to a human-directed, approval-gated staged editor, and **Stage A closed.** `PROJECT.md`, `ROADMAP.md`, ADR-005 and ADR-006 all accepted; ADR-001 and ADR-004 superseded; `VALIDATION-PLAN.md` retired. Still documents only. **Correction: a GitHub remote does exist and was pushed through `8b51a8b`** — earlier handoffs claiming otherwise were stale. The pivot itself is committed locally and **not pushed**.

## What is real

- **The pivot (2026-07-23).** The product is a **human-directed, transparent, approval-gated nine-stage reel editor.** The system proposes selection/ordering, trims, and speed ramps — each with a plain-language reason — and the user reviews, overrides anything, and approves each stage before the next runs. This replaces the previous framing, in which model-assisted ranking acted autonomously and was the project's pivotal bet.
- **`PROJECT.md` and `ROADMAP.md` are Accepted (owner-approved 2026-07-23).** With the ADRs below, this **closes Stage A — Direction.** Stage B (Specification) is next; the gate before any building is an authorized ADP.
- **Four accepted ADRs:** ADR-002 (privacy, 2026-07-22), ADR-003 (music/licensing, 2026-07-23), **ADR-005** (local web app form factor, 2026-07-23), **ADR-006** (incremental staged build with per-stage approval, 2026-07-23). **None authorizes implementation** — that requires an authorized ADP.
- **Two superseded ADRs, retained with their original text and a why-superseded note:** ADR-001 (CLI-first prototype shape) → ADR-005; ADR-004 (validation-first sequencing) → ADR-006.
- **`VALIDATION-PLAN.md` is retired** and this project is withdrawn from the PROP-01 Validation-stage pilot. General acceptance of PROP-01 remains an MD-002 matter, unaffected by this project.
- A folder of Stage A direction documents. **Documents only.**
- A competitive review based on **vendor documentation**, not measured output.
- A private Notion tracking projection; the repository remains authoritative (`docs/NOTION-PROJECTION.md`) — **now stale against the pivot.**
- **A GitHub remote exists.** `origin` → `https://github.com/vasudevap/ai-vacation-reel-agent.git`, last pushed at `8b51a8b` (git reflog records `update by push`). Handoffs before 2026-07-23 stated no remote existed; **that was stale, not accurate**. Repository visibility is not verifiable from the working tree — confirm it directly. The pivot commit is **local and unpushed**.

That is the complete list.

## What is only proposed

- `docs/specs/COMPONENT-DECOMPOSITION.md` — rewritten 2026-07-23. Forward-looking design, owner approval required. Unlocks nothing.

## What does not exist

Stated plainly so it is not inferred from the volume of documentation:

- **No product code.** No UI, no `project.json` implementation, no renderer, no exporter.
- **No media has been collected.** No corpus, no consent records, no annotations.
- **No experiment ever ran** — under the retired validation plan or otherwise. Every claim in `docs/specs/EVIDENCE-LEDGER.md` is graded `assumed`.
- No Engineering Specification, approved Work Order, or ADP.

## Stale, pending cleanup

- `docs/work-orders/phase-1-backlog.md` and `phase-1-backlog-deltas.md` — **retired.** They decompose the withdrawn validation apparatus (corpus, scorer A/B, comparison harness, held-out discipline). A fresh backlog is drawn after an ADP is authorized.
- `docs/specs/prototype-definition.md`, `docs/specs/sample-media-test-strategy.md`, `docs/vision/*`, `docs/research/*`, `docs/NOTION-PROJECTION.md`, `docs/specs/EVIDENCE-LEDGER.md` — **not yet reviewed against the pivot.** Treat their claims as pre-pivot until checked.

## Owner actions required

1. **Approve the M1–M3 Engineering Specification** once drafted, then **authorize an ADP.** ADR-005 and ADR-006 fix the shape and the method; neither authorizes building.
2. **Confirm the existing remote, and authorize any push separately.** Creation is no longer the open question — `origin` exists and was pushed through `8b51a8b`. Verify the repository's visibility directly, since it is not observable from the working tree. The pivot commit is unpushed; **each push is its own consequential action requiring explicit authorization**, and prior authorization does not carry forward.
3. **Register the project in `_oversight/STATUS.md`.** It is still absent from the overseer roster and therefore invisible to status and drift passes.
4. **Plan the real-user check.** ADR-006 makes it binding that owner approval is a *build* gate, not evidence of product quality. Roadmap milestones M3.5 and M7 require real users other than the owner.

*Closed 2026-07-23: `PROJECT.md` and `ROADMAP.md` accepted, closing Stage A — Direction.*

## Next artifact

Once `PROJECT.md` and `ROADMAP.md` are accepted: a light **Engineering Specification for M1–M3** (import, project store, timeline editor, render/export) that freezes the `project.json` schema and the component contracts in `COMPONENT-DECOMPOSITION.md` §1 — then a Work Order backlog, then an ADP.

**The M1–M3 manual editor comes before any assist.** Building the manual capability first is what gives each later assist an honest baseline to be judged against (see ROADMAP, *"Build order is not runtime order"*).
