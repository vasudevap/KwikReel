# Evidence ledger

**Status:** **No experiment has ever run and no real footage has ever been processed. Every claim below is graded `assumed`.** A backend exists and passes its tests on synthetic fixtures, which establishes that the code works — not that any claim here is true.
**Governing:** `_oversight/DELIVERY-PLAYBOOK.md` honesty disciplines and [`docs/CONSTRAINTS.md`](../CONSTRAINTS.md). Reviewed at every milestone gate.

Grades: **measured** (a checkpoint/gate reported it) · **estimated** (derived from measured data) · **assumed** (believed, untested) · **refuted** (disproved).

A claim used in an ADR, an ES, or a pitch must be traceable to a row here. The pre-pivot ledger graded an autonomous-ranking programme that ADR-006 retired; those claims (old C-01…C-11, tied to EXP-001…009 and kill criteria) are **withdrawn with that programme** and are not carried forward.

## Load-bearing claims (post-pivot)

| # | Claim | Grade | Moved by | Notes |
|---|---|---|---|---|
| C-01 | Users value explained, approvable assistance enough to review a first draft rather than take one-tap automation | **assumed** | ADR-012 **CP-1** (preference probe on the WO-100 prototype) | **Pivotal to the pivot.** The whole product rests here. A cheap early read — *not* the binding real-user gate. |
| C-02 | Incumbent free tools leave a real "would I post this?" gap on a real day | **assumed** | ADR-012 **CP-2** (competitive-floor comparison) | Competitive landscape reads vendor docs, not measured output. Re-checked each milestone (absorption). |
| C-03 | A legible, deterministic trim heuristic is a helpful starting point (kept more than discarded) | **assumed** | ~~M1 `disposition` rates~~ — **no mechanism currently defined** | **Weakened twice, 2026-07-28.** (1) Until WO-116 the proposer read exposure off the *letterboxed* proxy, so **every landscape clip was labelled `OVEREXPOSED`** on every second — the claim was resting on a proposer that mislabelled an entire orientation, and no test caught it because the only exposure assertion used a black *portrait* clip. Fixed; two regression tests now guard it. (2) v3z retires `disposition`, which was the thing that would have measured this claim. A replacement measure — countable from `origin` alone — must be named in `SPEC.md` or the claim has no path off `assumed`. |
| C-04 | Manual curation + AI trim yields a short reel **evaluable against — and plausibly as good as** — that day's Apple Memory | **assumed** | M1 exit gate (ES-001 §10; ADR-009) | Evaluable and plausibly useful; superiority is a later real-user question, not claimed here. |
| C-05 | A local web app + local FFmpeg meets the ≤5-min proxy/analysis/render targets on the target Apple Silicon Mac | **assumed** | ADR-012 **CP-3** (perf spike at the M1 internal checkpoint) | If false, the "one sitting" promise and the §9 gates need revision. |
| C-06 | Centre-crop to 9:16 is acceptable on real, people-centred footage | **assumed** | M1 exit gate; WO-104 stop-and-ask | Saliency reframing is deferred; centre-crop is the M1 fallback. |
| C-07 | A legible selection/ordering heuristic makes a trusted first pass (review beats ordering from scratch) | **assumed** | M2 exit gate | The most ambitious assist; sequenced second. |
| C-08 | Rules-based speed ramps (motion/audio/scene + beats) read as intentional and musical | **assumed** | M3 exit gate | Least-certain signal; sequenced last. "A wrong ramp reads as kitsch instantly." |
| C-09 | The pre-value workflow (iPhone→Mac folder + user-supplied rights-cleared track) is tolerable to a real user | **assumed** | deferred real-user validation | Tolerable to the owner now; a named real-user adoption risk (risk register). |
| C-10 | Someone would pay for this | **assumed** | deferred | Weakest claim. 2–6 uses/year is hostile to subscriptions. |
| C-11 | Apple/Google will not absorb this *transparent, approvable, staged* flow during the project's life | **assumed** | re-measured each milestone close | Decays; cannot be settled once. More platform *automation* is not the trigger. |

## Implementation reality

Separate from claims, per the playbook's *committed is not shipped* discipline.

| Item | State |
|---|---|
| Product code | **Backend complete on synthetic fixtures** — ingest, analysis, trim proposer, store, render, QA, HTTP API with security guards. **72 tests pass, 1 owner-gated skip.** **Frontend: none** — the WO-107–110 app was deleted in the 2026-07-28 clean cut and the v3z rack is not built. |
| Media / corpus / consent records / annotations | **none** |
| Experiment / checkpoint results | **none** — no checkpoint has run. Every claim above is `assumed`, and nothing has been exercised against real footage. |
| Governing decisions | Superseded by the 2026-07-28 clean cut. The surviving guardrails are in [`docs/CONSTRAINTS.md`](../CONSTRAINTS.md); the thirteen ADRs are archived and non-citable. The v3z departures — gates, `disposition`, displayed reasons, speed-in-M1, the audio model — are **undecided**. |
| Git | Public remote `origin` → `github.com/vasudevap/KwikReel` (**PUBLIC**). Local `main` is ahead of `origin/main`; each push is a separate owner decision. |

## Log

| Date | Change |
|---|---|
| 2026-07-20 | Ledger initialized alongside the (now retired) Stage B validation plan. All claims graded `assumed`. |
| 2026-07-23 | Pivot to a human-directed, approval-gated editor (ADR-005/006/007/008). The autonomous-ranking claim set (old C-01…C-11 / EXP-001…009) is withdrawn with the programme. No media collected. |
| 2026-07-24 | Pre-ADP course correction (ADR-009–013). Ledger reset to the post-pivot load-bearing claims above; all `assumed`. Prior "no remote" note corrected — a public remote exists. PROP-01 participation was withdrawn by ADR-006, so no pilot-launch entry stands. No media collected; no experiment run. |
| 2026-07-28 | **Clean cut** ahead of the v3z rebuild: superseded documents archived and made non-citable, guardrails consolidated into `docs/CONSTRAINTS.md`, obsolete frontend deleted. **C-03 weakened** on two independent grounds (see its note) after the letterbox defect was found and fixed. `Product code` row corrected — it read **none** while a complete backend existed. No media collected; no experiment run. |
