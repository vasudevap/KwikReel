# Handoff

**Updated:** 2026-07-23, all four ADRs (ADR-001–004) accepted by owner — ADR-003 accepted with Essentia dropped (librosa/ISC only); PROP-01 Validation-stage pilot launched; repository still has no remote.

## What is real

- **All four ADRs (ADR-001–004) are Accepted** — ADR-001/002/004 owner-approved 2026-07-22, ADR-003 (music/licensing) on 2026-07-23 with Essentia dropped for its AGPLv3 licence (librosa/ISC only). This is the Stage A decision set. It authorizes no implementation (that needs the validation plan approved and an ADP) and has collected no media (the WO-002 consent workflow does not exist).
- The **PROP-01 Validation-stage pilot is now launched** — accepting all four ADRs was its trigger (authorized via MD-001; general-policy acceptance still deferred to MD-002). No experiment has run.
- A folder of Stage A direction documents and one Stage B validation plan. **Documents only.**
- A competitive review based on **vendor documentation**, not measured output.
- A private Notion tracking projection for phases, gates, evidence, work-order readiness, and risks. The repository remains authoritative; see `docs/NOTION-PROJECTION.md`.

That is the complete list.

## What is only proposed

- `PROJECT.md`, `ROADMAP.md`, and `VALIDATION-PLAN.md` are Drafts awaiting owner approval. (All four ADRs are now Accepted — see *What is real*.)
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
2. **The Validation-stage pilot (PROP-01) is authorized (MD-001) and now launched.** All four ADRs are accepted, which was its trigger; general acceptance is a later MD-002 decision that does not gate this project. No separate methodology decision is required.
3. **Gate the four ADRs — done.** ADR-001, ADR-002, ADR-004 accepted 2026-07-22; ADR-003 accepted 2026-07-23 (Essentia dropped, librosa/ISC only). ADR-002's acceptance clears the corpus-collection gate **in principle only** — no media may be collected until the consent/deletion workflow (WO-002) exists and consent is recorded first.
4. **Accept or revise `VALIDATION-PLAN.md`, including its pre-registered thresholds.** Thresholds must be settled before the first experiment, not after.
5. **Register the project in `_oversight/STATUS.md`.** It is currently absent from the overseer roster and therefore invisible to status and drift passes.

## Next artifact

Once the gates above pass: Phase 1 Work Orders decomposed from `docs/work-orders/phase-1-backlog.md`, with allowed file scopes frozen and the AI-component gate checklist applied to WO-007, WO-008, and WO-009.

**The Engineering Specification comes after EXP-003 reports, not before.** Writing it earlier would mean specifying an architecture around an unproven claim — which is the sequencing error ADR-004 exists to prevent.
