# AI Vacation Reel Agent — session instructions

Read `../_oversight/DELIVERY-PLAYBOOK.md`. We follow it for this project.

This file mirrors `CLAUDE.md` so that Codex, Antigravity, and Claude Code sessions operate under identical constraints. If the two ever diverge, `CLAUDE.md` is authoritative and this file is stale — say so rather than picking one.

## Where the project is

**Stage A — Direction.** Documents only. No code, no corpus, no experiments, no accepted ADRs. Read `handoff.md` before assuming anything exists.

## Framing

This is an **explainable, local-first assisted first-draft editor** for private family footage — not a claim of fully autonomous editorial intelligence. The repository name predates this framing; the framing governs. The system proposes, a human decides.

## Hard constraints

These are locked by ADR and may not be relaxed by an agent's own judgment. Each is a stop-and-ask.

- **No implementation or interface work is authorized.** Not until the ADRs are accepted, the validation plan is approved, and the owner authorizes an ADP.
- **No media collection before ADR-002 is accepted.** Consent must be recorded before any footage is copied.
- **Never commit media, consent records, or the identity map.** See `.gitignore`. Git history persists after deletion, and consent under ADR-002 is withdrawable — a commit makes that impossible to honour.
- **No face recognition or person identification, at any phase.** Detection and counting without identity only.
- **Original media never leaves the device.** ADR-002 permits extracted keyframes only, under explicit per-run opt-in, in one experiment.
- **Never relax a pre-registered threshold or touch the held-out day.** Both are drift; both are stop-and-ask.
- **No `madmom`** or any dependency whose licence would restrict distribution (ADR-003).

## Working discipline

- Preserve the distinction between **proposed**, **accepted**, **validated by evidence**, and **implemented**. Documents describing a thing are not the thing.
- Every load-bearing claim is graded in `docs/specs/EVIDENCE-LEDGER.md`. If you rely on a claim, check its grade. Today they are all `assumed`.
- A check that could not run is recorded with the exact command and the reason — never silently skipped.
- Kill criteria are real. Firing one is a successful outcome, not a problem to argue around.

## GitHub Actions posture

- Do not add or run GitHub Actions during Stage A. There is no authorized implementation or repeatable code-validation requirement.
- Do not introduce a workflow merely because implementation is being discussed. Validation apparatus begins only after the existing ADR, validation-plan, and ADP gates authorize it.
- When validation apparatus is authorized, run the Work Order's focused and full checks locally before the first push. GitHub Actions, if separately authorized, provides final evidence rather than failure discovery.
- Do not change workflows, required checks, runner selection, or branch protection without explicit owner authorization.
