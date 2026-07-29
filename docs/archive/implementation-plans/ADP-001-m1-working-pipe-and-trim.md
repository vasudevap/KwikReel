# ADP-001: M1 — Working Pipe + AI Trim

**Status:** Authorized
**Authorized:** 2026-07-24 by the Repository Owner, as drafted (via session chat). Scope: the WO-100 – WO-114 set under the §2 grant (local build to green). Does **not** extend to pushes to the public `origin`, CI/Actions, or execution against real media — all of which remain the gates in §3.
**Program ID:** ADP-001
**Type:** Autonomous Delivery Program
**Owner:** Repository Owner
**Created:** 2026-07-24
**Execution Window:** From authorization until WO-114 (M1 integration verification) passes and M1 closes, or until a stop-and-ask trigger applies.
**Governing docs:** [ES-001](../specs/ES-001-manual-editor-core.md) · [ROADMAP.md](../../ROADMAP.md) · ADR-005/006/007/008/009/010/011/012/013
**Work Order backlog:** [m1-backlog.md](../work-orders/m1-backlog.md) (Approved)

---

## 1. Purpose

Collect the 15 accepted M1 Work Orders (WO-100 – WO-114) into one execution
program with a defined authority scope, ordered gates, and stop-and-ask
triggers. This is the artifact that turns "documents only" into "authorized to
build."

This ADP does not replace the Work Orders. Each WO remains the scope authority
for its own files, exclusions, validation gates, and stop-and-ask triggers.
The backlog's directory layout and lane rules are the mechanism that keeps
parallel work safe; this ADP grants the authority to execute it.

## 2. Execution Authority (what this ADP grants)

Under this ADP the assistant may proceed **locally** and without voluntary
pauses through the WO sequence in §4:

- implement WO scope on a short-lived per-WO branch;
- run the WO's local validation gates;
- write and update the WO's docs and review records in the same change;
- commit to the branch and merge to **local** `main` when the WO's gates pass;
- start the next dependency-ready WO.

That is the whole grant: **local build to green.** It is limited to the WOs
listed in §4 and the dependency set WO-101 pre-declares.

## 3. Withheld — stop-and-ask, not judgment calls

This ADP grants **no** authority over any of the following. Each is a
stop-and-ask that overrides autonomous continuation until explicitly resolved:

**Per-action owner authorization required (external / consequential):**
- **Every push to the public `origin`.** Prior authorization never carries to
  the next push (project rule; ADR/handoff). Commits are local until a named,
  per-push authorization.
- **Adding or running GitHub Actions / any CI.** None exists; it is not to be
  introduced ambiently (CLAUDE.md GitHub Actions posture).
- Any other consequential external write per the playbook's non-delegable class.

**Blocked until a prior gate clears:**
- **Executing any WO against real footage** (the "real ~50-clip day" gates in
  WO-102 / WO-111 / WO-114, and real-footage centre-crop review in WO-104)
  requires an **ADR-002 consent + lifecycle record first.** Code may be written
  and tested against synthetic fixtures before then; it may not be *run against
  real media* until that record exists.

**New governance (anything requiring a new ADR / ES / WO):**
- New product scope, architecture changes, relaxing any validation gate, or the
  10 backlog stop-and-ask triggers (person identification, writes beneath
  `media_root`, outbound network from the media path, relaxing local-delivery
  security, committing real footage/thumbnails, dependencies outside WO-101's
  set, changing a frozen schema/interface, etc.).

## 4. Work Order set and completion gates

| Order | WO | Lane | Completion gate (from backlog) |
|---|---|---|---|
| 1 | WO-100 Clickable prototype | — (alone) | Full flow clickable incl. manual curation; **owner walks it and agrees**; written ES-001 schema-gap list produced; no real footage committed |
| 2 | WO-101 Contract kernel + scaffold | — (alone) | Schemas validate the §4.1 example; round-trip byte-equivalent; TS/Pydantic one source of truth |
| 3 | WO-102 Ingest + proxies | A | Real 50-clip day probes clean; corrupt file reported not crashed; read-only enforced |
| 4 | WO-103 Project store | B | save→load byte-equivalent; refuses to overwrite `origin:"user"`; delete→restore exact |
| 5 | WO-104 Renderer + exporter | C | Duration ±0.5s; 1080×1920 H.264/AAC; all three audio modes correct |
| 6 | WO-105 Output QA | C | Catches black / truncated / silent-music renders; passes correct silent + all-audio-less clip renders |
| 7 | WO-106 HTTP API + job runner | D | Every §6 endpoint; localhost-only; cross-origin + bad-token rejected; no wildcard CORS; no path leaks |
| 8 | WO-107 App shell + API client | E | Runs fully in mock mode; real client swaps in with no component change |
| 9 | WO-108 Timeline + preview | E | 50 clips no stall; proxy scrub responsive |
| 10 | WO-109 Manual curation + edit + approval | E | Edits survive reload; exclude/delete→restore exact; excluded absent from render |
| 11 | WO-111 Per-clip analysis | A | Real 50-clip day ≤ ~5 min; per-second arrays; **`people_count` stays `null`** |
| 12 | WO-113 Guards + build gates | F | Each guard **fails** when deliberately violated |
| — | **CHECKPOINT (ADR-007)** | — | WO-102/103/104/105/106/107/108/109 merged + green: import→timeline→render→export proven |
| 13 | WO-112 Trim proposer | A | Every clip gets a proposal + honest `ReasonRecord`; full-clip fallback fires visibly |
| 14 | WO-110 Trim proposal UI | E | Reasonless proposal fails build; adjust/remove set `origin:"user"` + `disposition`; re-run is only overwrite path |
| 15 | WO-114 Integration verification | — (alone) | All eight ES-001 §10 checks pass on a real 50-clip day, incl. judge-vs-Apple-Memory |

## 5. Sequence and gates

```
WO-100 (alone) ──► [OWNER GATE: walk prototype] ──► [amend ES-001 with gap list]
      │
      ▼
WO-101 (alone, contract freeze)
      │
  ┌───┬───┬───────────┬────────┬────────┐
 102 103 104         106      107      113
  │       │                    │
 111     105                  108
  │                            │
  │                          109
  └────► [CHECKPOINT: pipeline green] ◄──┘
              │                 │
            112 ───────────────►110
              │                 │
              └──── WO-114 (alone) ────┘
```

**Two gates interrupt autonomy by design and are not stop-and-asks I invent —
they are built into the program:**

1. **After WO-100 — owner walk + contract amendment.** The owner walks the
   clickable prototype and agrees the flow. The schema-gap list is amended into
   ES-001. WO-101 does not start until ES-001 reflects what the screen needs.
   (ADR-008.)
2. **The checkpoint (ADR-007).** WO-110 and WO-112 do not merge until the media
   pipeline is proven end to end — so the renderer and the trim proposer are
   never being debugged at the same time.

Plus the **consent gate (§3):** WO-102 / WO-111 / WO-114 may be *built* against
synthetic fixtures at any time, but may not be *run against the real 50-clip
day* until an ADR-002 consent + lifecycle record exists.

## 6. Execution rules (per WO)

- Branch `wo-NNN-<slug>` off local `main`; keep changes within the WO's file scope.
- Add the dependency only if WO-101 pre-declared it — otherwise stop-and-ask.
- Run the WO's stated local validation before merging to local `main`.
- Merge to **local** `main` when gates pass; **do not push** without a per-push
  authorization (§3).
- Record honest outcomes: a gate that could not run is logged with the exact
  command and reason, never silently skipped.

## 7. Closeout

M1 (this ADP) closes when **WO-114 passes all eight ES-001 §10 checks** on a
real 50-clip day. Failures WO-114 finds become new Work Orders, not silent
fixes. Closeout updates `handoff.md` and the EVIDENCE-LEDGER grades for any
claim WO-114 exercised. M2 (AI selection + ordering) is a separate future ADP.
