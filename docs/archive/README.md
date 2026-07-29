# Archive — historical record, not authority

**Nothing in this directory is normative. Nothing here may be cited as authority.**

If you need something from a file in here, **promote it into a live document
first** — `docs/CONSTRAINTS.md` for a guardrail, `SPEC.md` for product or
contract behaviour — and cite that instead.

That rule exists because the way obsolete decisions leak into new work is by
being cited. Every document below was true when written and is not true now, or
is superseded by a document that is. Reading them to understand *how the project
got here* is fine and often useful. Treating them as a source of requirements is
not.

Archived 2026-07-28, in the clean cut that preceded the v3z rebuild.

## Why each group is here

| Group | Superseded by |
|---|---|
| `decisions/` — all thirteen ADRs | The surviving guardrails are transcribed into [`docs/CONSTRAINTS.md`](../CONSTRAINTS.md). The rest — gates, staged progression, `disposition`, manual curation, build sequencing — are retired or in flux pending the v3z decision session |
| `specs/ES-001-manual-editor-core.md` | `SPEC.md` (not yet written), which is cut from v3z forward rather than amended from ES-001 backward |
| `specs/v3s-backend-alignment.md` | Its own decisions D-04 and D-07 were reversed by `v3t-brief.md` O-18 and O-26. The register contradicts itself and must not be read as current |
| `specs/VALIDATION-PLAN.md`, `specs/sample-media-test-strategy.md`, `specs/prototype-definition.md` | Retired regimes. No experiment ever ran; no corpus was collected |
| `specs/COMPONENT-DECOMPOSITION.md` | Forward-looking design against a product shape that no longer exists |
| `specs/WO-100-schema-gaps.md` | Resolved into ES-001 §4.5, which is itself archived |
| `work-orders/m1-backlog.md` | WO-100–114, complete. Its successor backlog is in `docs/implementation-plans/PLAN-v3z-rebuild.md` |
| `work-orders/phase-1-backlog*.md` | Retired pre-pivot |
| `implementation-plans/ADP-001-*.md` | Complete. Its grant is spent |
| `reviews/` | Point-in-time review of a plan that has since changed |
| `vision/`, `NOTION-PROJECTION.md` | Pre-pivot (2026-07-23) |
| `design-claude/` — v1, v2, v3a–v3y, the 218-line version README, `v3t-brief.md` | **v3z is the design.** The rest is the record of how it got there. `v3t-brief.md` in particular carries O- and N-numbers that supersede each other (O-8 by O-20, O-9 by O-18) and must not be read as a decision list |
