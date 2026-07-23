# ADR-002 — Privacy and data posture

**Status:** Accepted — owner-approved 2026-07-22
**Required by:** `_oversight/DELIVERY-PLAYBOOK.md` Stage A — a data and privacy posture ADR is mandatory before any data is collected where a project processes personal, third-party, or minors' data.
**Referenced by:** `docs/work-orders/phase-1-backlog.md` (WO-013 previously cited a "privacy ADR" that did not exist; this resolves that reference).

**On acceptance:** the posture below is ratified, including its hard constraints — no face recognition or person identification at any phase; originals opened read-only with no delete path and no default network egress; withdrawable written consent covering children's footage specifically; and the cloud comparison bounded to extracted keyframes in EXP-003 under per-run opt-in. Acceptance clears the corpus-collection gate **in principle only**: no media may be collected until the consent and deletion workflow (WO-002) exists and consent is recorded first. No media has been collected.

## Context

This project processes home video of private families, frequently including children, captured at identifiable locations with GPS trails that reveal where a family sleeps and eats. The test corpus is not synthetic — it is real footage belonging to the owner and to consenting friends and relatives.

The privacy exposure of the *test corpus* is therefore as real as that of any production system, and it exists from the first day of validation, before any product exists. Deferring this decision until productization would mean collecting sensitive data under no written posture at all.

The governed-systems principles *privacy-aware by default* and *reversible in its actions* apply directly.

## Options considered

1. **Local-first with opt-in derivative-only cloud comparison (recommended).** All processing on-device by default; a controlled experiment may send extracted keyframes — never original media — to a cloud model, under explicit per-run opt-in, to measure the quality gap.
2. Local-only, absolute. Simplest privacy story, but forecloses measuring how much draft quality depends on frontier models, which is a question the validation must answer.
3. Cloud-first. Best model access; requires uploading gigabytes of children's footage, which contradicts the trust story that is the project's differentiation.
4. Defer the decision until productization. Rejected: the corpus is collected during validation, so the exposure precedes the deferral.

## Proposed decision

Adopt option 1.

**Collection and consent**
- Corpus media is contributed by the owner and by consenting friends and relatives. Consent is written, covers footage of children specifically, names what the footage will be used for, and is recorded before the media is copied.
- Consent is withdrawable. On withdrawal, that contributor's media and derived artifacts are deleted and the deletion is recorded.
- Contributors are identified by synthetic IDs. The mapping is stored separately from the corpus.

**Processing**
- Originals are opened **read-only**. Derived data is written to a separate output directory. The system has no delete path for source media.
- Default processing is entirely on-device. No network egress of media, derivatives, or metadata in the default path.
- **No face recognition and no person identification, at any phase.** Face *detection and counting* without identity is permitted. This is a hard constraint under the playbook's rule: changeable only by a new ADR.

**The opt-in cloud comparison**
- Permitted **only** for the measurement in EXP-003 comparing local against frontier model quality.
- Sends extracted keyframes only. Original media, audio, and full video never upload — this is a hard boundary, not a default setting.
- Requires explicit per-run opt-in, never a persisted preference, and discloses in the interface exactly what will be sent.
- Uses endpoints under no-training and no-retention terms; those terms are verified and recorded in the EXP before the run.
- Contributors whose consent does not cover cloud processing are excluded from the cloud arm of the experiment.

**Outputs**
- GPS and identifying metadata are stripped from any rendered export.
- No telemetry containing media, derivatives, or file paths.
- Nothing is published, posted, or transmitted without an explicit human act. There is no auto-publish path.

**Excluded until a new ADR says otherwise:** face recognition or person naming, cloud library sync, auto-posting, audio transcription, and any preference learning that is not user-visible and user-editable.

## Consequences

- The validation corpus can be assembled lawfully and revocably, and the privacy story is demonstrably true rather than aspirational.
- Measuring the local-versus-frontier quality gap stays possible, bounded to keyframes and to one experiment.
- Cost: a consent and deletion workflow must exist before corpus assembly begins, which is real work in EXP-000 rather than a later cleanup.
- Cost: excluding face recognition forecloses per-person coverage guarantees, which is a feature users are likely to ask for. That trade is accepted deliberately, and reversing it requires a new ADR.
