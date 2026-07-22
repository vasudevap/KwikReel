# Handoff

**Updated:** 2026-07-22, initial project documents committed locally; repository still has no remote.

## What is real

- A folder of Stage A direction documents and one Stage B validation plan. **Documents only.**
- A competitive review based on **vendor documentation**, not measured output.
- A private Notion tracking projection for phases, gates, evidence, work-order readiness, and risks. The repository remains authoritative; see `docs/NOTION-PROJECTION.md`.

That is the complete list.

## What is only proposed

- **ADR-001 through ADR-004 are all Proposed. None is accepted.**
- `PROJECT.md`, `ROADMAP.md`, and `VALIDATION-PLAN.md` are Drafts awaiting owner approval.
- The Validation stage this project depends on (PROP-01, Stage B) is **authorized for pilot on this project via MD-001, but not accepted as general policy** — general acceptance is deferred to MD-002. ADR-004 stands or falls with it.

## What does not exist

Stated plainly so it is not inferred from the volume of documentation:

- No product code and no evaluation apparatus.
- No test corpus, no consent records, no annotations. **No media has been collected.**
- No experiment has run. Every claim in `docs/specs/EVIDENCE-LEDGER.md` is graded `assumed`.
- No Engineering Specification, approved Work Order, ADP, model, benchmark run, or interface.
- No remote repository or published branch. The initial local commit is `e234a12` (`Initialize project direction artifacts`); the worktree is clean.

## Owner actions required

1. **Create the public remote repository.** The local repository is ready to connect and push; public-repository creation is a human-initiated, consequential external action under the governing playbook.
2. **The Validation-stage pilot is already authorized (MD-001).** Piloting PROP-01 on this project is contingent on the ADRs below being accepted; general acceptance is a later MD-002 decision that does not gate this project now. Accepting the ADRs launches the pilot — no separate methodology decision is required here.
3. **Gate the four ADRs.** ADR-002 (privacy) blocks corpus collection specifically — no media may be gathered before it is accepted.
4. **Accept or revise `VALIDATION-PLAN.md`, including its pre-registered thresholds.** Thresholds must be settled before the first experiment, not after.
5. **Register the project in `_oversight/STATUS.md`.** It is currently absent from the overseer roster and therefore invisible to status and drift passes.

## Next artifact

Once the gates above pass: Phase 1 Work Orders decomposed from `docs/work-orders/phase-1-backlog.md`, with allowed file scopes frozen and the AI-component gate checklist applied to WO-007, WO-008, and WO-009.

**The Engineering Specification comes after EXP-003 reports, not before.** Writing it earlier would mean specifying an architecture around an unproven claim — which is the sequencing error ADR-004 exists to prevent.
