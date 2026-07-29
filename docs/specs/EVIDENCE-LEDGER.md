# Evidence ledger

**Status:** **No experiment has ever run and no real footage has ever been processed. Every claim below is graded `assumed`.** A backend exists and its rebuilt lanes pass on synthetic fixtures (mid-realignment, parts of the suite are deliberately red — see `handoff.md`), which establishes that the code works — not that any claim here is true.
**Governing:** `_oversight/DELIVERY-PLAYBOOK.md` honesty disciplines and [`docs/CONSTRAINTS.md`](../CONSTRAINTS.md). Reviewed at every ADP closeout — the milestone gates are retired (DECISIONS A-5c).

Grades: **measured** (a checkpoint/gate reported it) · **estimated** (derived from measured data) · **assumed** (believed, untested) · **refuted** (disproved).

A claim used in an ADR, an ES, or a pitch must be traceable to a row here. The pre-pivot ledger graded an autonomous-ranking programme that ADR-006 retired; those claims (old C-01…C-11, tied to EXP-001…009 and kill criteria) are **withdrawn with that programme** and are not carried forward.

## Load-bearing claims (post-pivot)

| # | Claim | Grade | Moved by | Notes |
|---|---|---|---|---|
| C-01 | Users value explained, approvable assistance enough to review a first draft rather than take one-tap automation | **assumed** | The deferred real-user check — the binding gate before the product is called *good* | **Pivotal to the pivot.** The whole product rests here. The archived CP-1 preference probe never ran, and its WO-100 prototype was deleted in the clean cut; no cheaper instrument is currently scheduled. |
| C-02 | Incumbent free tools leave a real "would I post this?" gap on a real day | **assumed** | The owner's competitive-floor comparison on a real day (deferred; formerly the archived CP-2) | Competitive landscape reads vendor docs, not measured output. Re-checked deliberately at each ADP closeout (absorption) — no milestone boundaries remain (A-5c). |
| C-03 | A legible, deterministic trim heuristic is a helpful starting point (kept more than discarded) | **assumed** | **`SPEC.md` §4.5 — the export summary line** (*"Kept 14 of 19 AI trims"*), derived from `disposition` at export | **Weakened then repaired, 2026-07-28.** (1) Until WO-116 the proposer read exposure off the *letterboxed* proxy, so **every landscape clip was labelled `OVEREXPOSED`** on every second — the claim was resting on a proposer that mislabelled an entire orientation, and no test caught it because the only exposure assertion used a black *portrait* clip. Fixed (`3d0d0d6`); two regression tests now guard it. (2) v3z retired `disposition`, removing the measure — but **DECISIONS A-3/A-3b reversed that**, keeping the field and naming its three writers. The measure exists again in `SPEC.md` §4.5. **It is still not built, and cannot move the grade until a real-footage run under ADP-004.** Synthetic fixtures cannot support this claim. |
| C-04 | Manual curation + AI trim yields a short reel **evaluable against — and plausibly as good as** — that day's Apple Memory | **assumed** | `SPEC.md` §12's validation gates on a real day's footage (ADP-004 / WO-135) | Evaluable and plausibly useful; superiority is a later real-user question, not claimed here. The Apple Memory comparison is named in WO-135's scope. |
| C-05 | A local web app + local FFmpeg meets the "one sitting" performance bar on the target Apple Silicon Mac | **assumed** | WO-135's performance run on a real ~50-clip day (ADP-004; carries forward the archived CP-3 spike) | If false, `SPEC.md` §10's promise needs revision. Playback alone is measured (WO-124, synthetic proxies — `SPEC.md` §6); ingest/analysis/render on real footage are not. |
| C-06 | Centre-crop to 9:16 is acceptable on real, people-centred footage | **assumed** | `SPEC.md` §12 on a real day's footage (ADP-004 / WO-135) | Saliency reframing is deferred (`SPEC.md` §13); centre-crop is the fallback and can decapitate people at frame edges. |
| C-07 | ~~A legible selection/ordering heuristic makes a trusted first pass (review beats ordering from scratch)~~ | **withdrawn 2026-07-29** | Nothing — the assist it describes was **cancelled permanently** (DECISIONS A-5b) | The machine never proposes which clips belong in the reel, so the claim has no subject left in the product. Withdrawn rather than regraded, like the pre-pivot set; `PROJECT.md` records it as a retired assumption. |
| C-08 | Rules-based speed ramps (motion energy + audio level, `SPEC.md` §4.2) read as intentional rather than cheap | **assumed** | The §4.5 kept-count at export, read on a real-footage run (ADP-004) | Least-certain signal; **built last so the net-negative de-scope trigger can fire on it cheaply** (A-5a). Beat alignment is deferred and no longer part of this claim (`SPEC.md` §13). "A wrong ramp reads as kitsch instantly." |
| C-09 | The pre-value workflow (iPhone→Mac folder + user-supplied rights-cleared track) is tolerable to a real user | **assumed** | deferred real-user validation | Tolerable to the owner now; a named real-user adoption risk (risk register). |
| C-10 | Someone would pay for this | **assumed** | deferred | Weakest claim. 2–6 uses/year is hostile to subscriptions. |
| C-11 | Apple/Google will not absorb this *transparent, reversible* flow during the project's life | **assumed** | Re-checked deliberately at each ADP closeout — no milestone boundaries remain (A-5c) | Decays; cannot be settled once. More platform *automation* is not the trigger. ("Staged" dropped from the claim: the staged flow itself was retired.) |

## Implementation reality

Separate from claims, per the playbook's *committed is not shipped* discipline.

| Item | State |
|---|---|
| Product code | **Backend being realigned to schema v2 under ADP-002.** Contracts (WO-117), ingest (WO-116a) and the trim proposer (WO-118a) are v2 and merged; store, media, speed proposer, render, QA and the API are still v1, their Work Orders dependency-ready. The suite is **deliberately partly red across the version seam** — 45 pass, 10 fail, 5 modules do not import (`handoff.md` has the box). **Frontend: a stub** — `main.tsx` plus generated types; the rebuild is ADP-003, not yet written or authorized. |
| Media / corpus / consent records / annotations | **none** |
| Experiment / checkpoint results | **none** — no checkpoint has run. Every claim above is `assumed`, and nothing has been exercised against real footage. (WO-124 measured playback behaviour on synthetic proxies — an engineering measurement recorded in `SPEC.md` §6, not an evidence checkpoint; it moves nothing here.) |
| Governing decisions | The 2026-07-28 clean cut archived the thirteen ADRs (non-citable); the surviving guardrails are in [`docs/CONSTRAINTS.md`](../CONSTRAINTS.md). **The v3z departures are decided** — [`DECISIONS.md`](../DECISIONS.md), owner, 2026-07-28 — and **`SPEC.md` is accepted** (2026-07-28), its §14 fully closed as of 2026-07-29. The live build authorization is ADP-002, amended four times. |
| Git | Public remote `origin` → `github.com/vasudevap/KwikReel` (**PUBLIC**). Local `main` is ahead of `origin/main`; each push is a separate owner decision. |

## Log

| Date | Change |
|---|---|
| 2026-07-20 | Ledger initialized alongside the (now retired) Stage B validation plan. All claims graded `assumed`. |
| 2026-07-23 | Pivot to a human-directed, approval-gated editor (ADR-005/006/007/008). The autonomous-ranking claim set (old C-01…C-11 / EXP-001…009) is withdrawn with the programme. No media collected. |
| 2026-07-24 | Pre-ADP course correction (ADR-009–013). Ledger reset to the post-pivot load-bearing claims above; all `assumed`. Prior "no remote" note corrected — a public remote exists. PROP-01 participation was withdrawn by ADR-006, so no pilot-launch entry stands. No media collected; no experiment run. |
| 2026-07-28 | **Clean cut** ahead of the v3z rebuild: superseded documents archived and made non-citable, guardrails consolidated into `docs/CONSTRAINTS.md`, obsolete frontend deleted. **C-03 weakened** on two independent grounds (see its note) after the letterbox defect was found and fixed. `Product code` row corrected — it read **none** while a complete backend existed. No media collected; no experiment run. |
| 2026-07-28 | **`DECISIONS.md` decided, `SPEC.md` accepted, ADP-002 authorized** (amended same day: WO-118a and WO-116a added, WO-120 unheld). WO-117 froze schema v2; WO-116a gave proxies audio; WO-118a rebuilt the trim proposer to A-6; WO-124 measured the playback engine. No media collected; no experiment run; no grade moved — ADP-002 §7 forbids it on synthetic fixtures. |
| 2026-07-29 | `SPEC.md` §14 fully closed (SO-2 – SO-4; SO-1 closed 2026-07-28). **Ledger reconciled to the decided record:** the `Governing decisions` row still called the v3z departures *undecided* — corrected; instruments naming retired milestone gates (C-01, C-02, C-04, C-05, C-06, C-11) repointed at their live equivalents; **C-07 withdrawn** — its assist was cancelled permanently (A-5b); C-08 reworded to the beat-free `SPEC.md` §4.2 assist. Every grade stays `assumed`. |
