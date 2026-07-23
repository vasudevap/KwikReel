# Notion project-tracking projection

**Status:** Active project-management record.
**Created:** 2026-07-21.
**Governing:** `handoff.md`, `PROJECT.md`, `ROADMAP.md`, accepted ADRs, and experiment reports remain authoritative.

## Purpose and boundary

Notion is the project's **tracking projection**: a readable surface for gates, deliverables, evidence, work-order readiness, risks, and kill criteria. The repository is the source of truth. A Notion property change is not an approval, evidence, implementation, or authorization on its own.

The projection must preserve the distinctions among `Draft`, `Proposed`, `Accepted`, `Evidence gathering`, `Validated — continue/revise/stop`, and `Implemented`.

## Data boundary

Never put any of the following in Notion:

- original or derivative media, audio, proxies, keyframes, or annotations that could identify a person;
- consent records, identity maps, participant names, or contact details;
- credentials, access tokens, or private keys;
- an experimental result that has not first been recorded in the repository evidence record.

Notion may hold only non-sensitive project metadata and summaries. The source files named below remain in the repository.

## Hub and databases

The private Notion hub is [AI Vacation Reel Agent — Delivery Hub](https://app.notion.com/p/3a4e3a7fd96481b29af7f4ba709c866a).

| Notion database | Repository source | Update trigger |
|---|---|---|
| Phase Roadmap | `ROADMAP.md` | Phase boundary, exit criterion, or gate outcome changes. Add schedule dates only after the owner chooses them. |
| Deliverables & Gates | `PROJECT.md`, `ROADMAP.md`, `docs/decisions/`, `docs/specs/`, `handoff.md` | Artifact is drafted, proposed, accepted, superseded, or otherwise changes status. |
| Evidence Scorecard | `docs/specs/VALIDATION-PLAN.md`, experiment reports, `docs/specs/EVIDENCE-LEDGER.md` | Pre-registration, experiment status, result, or verdict changes. Never edit a threshold after observation without recording drift and an owner decision. |
| Work Orders | `docs/work-orders/` and a future accepted ES/ADP | A work order is created, its definition of ready changes, or an ADP authorizes execution. |
| Risk & Kill Criteria | `PROJECT.md`, ADRs, risk register | A risk, hard constraint, or kill criterion is added, triggered, mitigated, or retired. |

## Update protocol

1. Update the authoritative repository document first.
2. For a phase close, update `handoff.md` with what is real, proposed, and absent.
3. Reconcile the corresponding Notion row or create a new row; do not overwrite unrelated Notion content.
4. Record the same status and source path in Notion. Link to the repository path; do not paste sensitive material.
5. If the change needs owner approval, retain `Proposed` or `Awaiting owner approval` until the owner explicitly accepts it. If it changes an ADR, threshold, held-out discipline, privacy posture, or scope, stop and ask rather than inferring approval.

## Current baseline

The project is in **Stage A — Direction**. All four ADRs (`ADR-001`–`ADR-004`) are accepted (owner-approved 2026-07-22–23; ADR-003 with Essentia dropped, librosa/ISC only); `PROJECT.md`, `ROADMAP.md`, and `VALIDATION-PLAN.md` are not yet accepted; Phase 1 work orders are a draft backlog and are not authorized. No media, corpus, consent record, experiment, implementation, engineering specification, ADP, or product interface exists.

## Setup verification

On 2026-07-21, creation responses confirmed six phase records, nine deliverables, ten experiment records, twelve draft work orders, and eight risk/constraint records, together with their configured views. A subsequent SQL count check through `mcp__codex_apps__notion_notion_query_data_sources` could not run because the connected service returned `MCP error -32602: Tool notion-query-data-sources not found`. Treat the creation responses as the baseline and re-run database counts through the Notion connector or UI before relying on an automated audit.
