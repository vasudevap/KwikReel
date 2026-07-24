# Pre‑ADP Review — AI Vacation Reel Agent

**Status:** **Independent review — advisory.** Introduces **no accepted decision**, authorizes nothing, and relaxes no constraint. This document is *input to the owner's ADP decision*; it does not itself gate, approve, or supersede anything. Findings are recommendations, not applied changes.
**Actioned 2026-07-24:** the owner accepted the REVISE verdict and applied a course correction — ADR-009 (manual curation in M1), ADR-010 (proposal `disposition`), ADR-011 (local delivery security), ADR-012 (evidence checkpoints), ADR-013 (prototype thumbnails under ADR-002), plus amendments to ES-001 / ROADMAP / PROJECT / m1-backlog and a pivot pass over README / EVIDENCE-LEDGER / risk-register. Blocking levels were re-calibrated (evidence probes are checkpoints, **not** ADP blockers; "nine gates" → five; **bounded**, not unbounded, proposal history). See `handoff.md`.
**Reviewer:** Independent product / UX / architecture / privacy / delivery review, commissioned by the owner.
**Date:** 2026-07-24
**Repository state reviewed:** local `main` @ `933a067`; public `origin/main` @ `174d43e` (three commits behind local — see Finding §6).
**Governing documents assessed:** [PROJECT.md](../../PROJECT.md), [ROADMAP.md](../../ROADMAP.md), [handoff.md](../../handoff.md), [README.md](../../README.md), [AGENTS.md](../../AGENTS.md), ADR‑002/003/005/006/007/008, [ES‑001](../specs/ES-001-manual-editor-core.md), [m1-backlog.md](../work-orders/m1-backlog.md), [COMPONENT-DECOMPOSITION.md](../specs/COMPONENT-DECOMPOSITION.md), [EVIDENCE-LEDGER.md](../specs/EVIDENCE-LEDGER.md), [risk-register.md](../research/risk-register.md), [competitive-landscape.md](../research/competitive-landscape.md), the pre‑pivot vision/spec set, and [`_oversight/DELIVERY-PLAYBOOK.md`](../../../_oversight/DELIVERY-PLAYBOOK.md).

---

## Verdict up front: **REVISE**

The governance is genuinely strong and the pivot reasoning is honest and mostly correct — but **M1 as specified cannot produce the deliverable its own exit gate demands**, the audit schema cannot measure the thing the whole product is built to measure, and the public repository currently contradicts itself at the front door. All three are cheap to fix now and expensive after WO‑101 freezes contracts. Resolve them, run two near‑free evidence probes, then authorize the ADP.

## What is already right (so the criticism is calibrated)

- The ADR chain is disciplined: one decision per record, supersession is explicit, and the retired records (ADR‑001, ADR‑004, VALIDATION‑PLAN, phase‑1 backlogs) all carry honest banners. The pivot was absorbed in the *decision* layer exactly as the playbook intends.
- ADR‑006's core reasoning is sound: with an approval gate on every assist, there is no single autonomy claim left to pre‑validate, so retiring the 30–40h annotation corpus and pivotal ranking experiment is justified, not lazy.
- The privacy posture is real, not aspirational: the `.gitignore` is thorough, "no identity, count only" is a hard constraint, originals are read‑only, and `project.json` is correctly kept out of git.
- The honesty disciplines are live: `PROJECT.md` grades its own load‑bearing beliefs as `assumed`, and ADR‑006/007 explicitly name "approving one's own work overestimates quality" as the drift risk that replaces the old one.

That is a better‑governed pre‑code repo than most. The findings below are what a pre‑ADP review exists to catch.

---

## 1 · Product thesis

**Is a local, explainable, human‑directed reel editor the right product?** Defensible *as the current framing states it* — a portfolio demonstration of governed‑systems delivery plus a tool the owner personally wants — and honestly hedged everywhere as a hypothesis. It is **not** yet defensible as a product with a real competitive wedge, and the docs mostly agree.

**Is "transparent, approval‑gated assistance" a real differentiator vs Apple/Google/CapCut/Adobe?** This is the weakest load‑bearing belief and it is under‑argued.

- **Evidence:** `competitive-landscape.md` correctly grades the gap "hypothesis, not finding" and concedes auto‑assembly + beat sync are commodity. But note *what the incumbents already do*: Apple Photos Memory Movies is editable after generation (length, songs, add/remove items); Google Photos lets you review/reorder/remove; CapCut hands you a full manual timeline. **"Keep the human in control and able to override" is already provided.** The only thing no incumbent ships is the *persisted, plain‑language rationale per decision*.
- **Why this matters:** the pivot narrowed the differentiator from a *capability* moat ("AI selects better than you," pre‑pivot) to a *preference* bet ("you'll prefer reviewing explained proposals to one‑tap"). A preference bet that asks the user to do **more** work than one tap, in exchange for reasons they may not read, is a harder and softer sell — and it runs against the incumbents' trend (more automation, less friction), which `PROJECT.md` frames as a strength but is equally a headwind.
- **Uniquely underserved:** not "control" (served), but (a) **auditable, saved rationale** and (b) **local‑first privacy for family footage**. The docs treat local‑first as a *constraint* rather than the *wedge*. Against Google/CapCut/cloud tools, privacy is arguably the stronger real differentiator than explainability — and it's underplayed.
- **Alternative:** reposition around "the explainable, auditable, local‑first layer" as the identity, rather than "a first‑draft editor that competes with Apple." Trade‑off: narrower appeal, but it's the only claim that is actually unserved and it stops inviting the "but Apple already does this" collapse on first contact with an iPhone owner.
- **Classification: Watch item** (thesis honesty is a strength) — but the pivotal assumption is untested with *no scheduled test*, which is escalated under §5.

**iPhone→Mac + rights‑cleared music: acceptable, or fatal friction?** This is the sleeper risk and it's fragmented across docs instead of totalled.

- The primary user "shoots on iPhone," but the product is a Mac local web app importing "from a chosen folder," with phone access deferred (ES‑001 §12). So before any value, the user must **(1)** move 20–100 clips off the phone into a Mac folder, and **(2)** source an Artlist/Epidemic track because the Instagram song they actually want is legally impossible (ADR‑003, correctly). Two friction walls stand *in front of* the first result, for a product whose promise is "in one sitting."
- **Why it's not fatal *now*:** the owner is the sole user and tolerates it. **Why it's serious later:** the single most‑wanted feature is permanently unavailable *and* its substitute is itself friction — together they cap real‑user appeal hard.
- **Classification: Watch (M1, owner‑only) / Required before any real‑user claim.** Name "pre‑value friction" as a first‑tier risk rather than three scattered acknowledgements.

---

## 2 · UX and the approval model

**The "nine gates" claim is a real mismatch with the actual state model — and it's the front‑door framing.**

- **Evidence:** `AGENTS.md`, `PROJECT.md`, and `handoff.md` all say the user "approves each of **nine** stages before the next runs." But the `PROJECT.md` pipeline table shows stage 5 (Timeline) is "(presentation)", stage 6 (Manual edit) is "user drives", and stages 8–9 have no approve gate. The canonical schema confirms it: `ES-001` `stage_approvals` has **five** keys — `ingest, trim, selection, speed, finalize` — of which only three are live in M1.
- **Why it matters:** "nine gates" makes the product sound like a nine‑step bureaucratic review it isn't, and it's repeated on a public repo. The real review burden isn't the *stage* gate anyway — it's the **50 per‑clip proposals inside** the trim stage.
- **Alternative / smallest model that preserves trust:** state it honestly as **five approval gates** (the schema is already correct), gate only stages that mutate state, and *within* a stage offer "approve all with exceptions" rather than forced clip‑by‑clip. Trade‑off: "approve all" slightly weakens the per‑item‑consent story — mitigated by surfacing exceptions.
- **Classification: Blocker before ADP** (cheap doc/framing fix; it's wrong on the public repo and WO‑100 will collide with it).

**Inline explanations always, or confidence‑ranked?**

- **Evidence:** ES‑001 §5.3 mandates every proposal's `human_text` inline, always ("a proposal with no readable reason is a bug"). Meanwhile `ReasonRecord.confidence` (high/med/low) is **frozen into the schema but has no specified behaviour anywhere** — a latent unused field.
- **Why "always inline" backfires:** 50 always‑expanded rationales become a wall of text; users bulk‑approve without reading, which both defeats transparency *and* biases the "proposals kept" metric (unread bulk‑accept looks like "kept").
- **Recommendation:** **persist** the reason always (audit), **display** on demand, and **auto‑surface low‑confidence proposals first** — using the `confidence` field that already exists. Trade‑off: always‑inline is simpler and maximally auditable; confidence‑first is more usable but risks the user never seeing high‑confidence reasons. Prototype both in WO‑100.
- **Classification: Required before a later milestone** (M1 can ship always‑inline; the 50‑clip trim stage will already feel the pain).

---

## 3 · M1 direction — the central finding

**M1, exactly as specified, cannot produce "a reel worth keeping," because it gives the user no way to remove a clip.**

- **Evidence:** M1 scope is import → AI trim → timeline → render → export. Selection/ordering is deferred to M2 (ES‑001 §1). The M1 manual controls (WO‑109) are "**trim handles, reorder, and the stage‑approval UI**" — no delete, no include/exclude. ROADMAP puts "include/exclude … delete, restore" in **M2**. COMPONENT‑DECOMPOSITION C‑3 says `delete/restore` "extend it at M2–M3." Yet the M1 exit gate (ES‑001 §10.8; ROADMAP) is "**export a reel worth keeping**," and the primary user wants a **60–90s** reel.
- **Why this is fatal to the gate:** AI trim removes dead air *within* a clip; it cannot remove a *clip*. A real 50‑clip day, each trimmed to ~3–5s, is a **150–250s concatenation of every clip in capture order**. `target_duration_s: 75` sits in the schema with **no consumer in M1** (nothing selects to a budget). That output is precisely the "montage, not a say" that `PROJECT.md` says is commodity — and it is plausibly **worse** than an Apple Memory of the same day (which is shorter, curated, music‑synced). ADR‑007's whole justification — "the first delivery is genuinely better than the free alternatives" — is **not met**.
- **Internal contradiction to resolve:** ES‑001 §12 defers "undo history *beyond* delete/restore," implying delete/restore *is* in M1 — directly contradicting WO‑109's scope, ROADMAP, and COMPONENT‑DECOMPOSITION, which all put it in M2. So the backlog wouldn't even build it. Either reading fails: no delete → gate unreachable; delete intended → WO‑109 is under‑scoped and the backlog is wrong.

**Is AI trim the right first assist? For and against.**

- **For:** it's the most tractable signal (deterministic blur/shake/exposure/static), it's individually disposable, it ships with its override controls (pairing rule satisfied), and it addresses the grind the owner *named first* — scrubbing each clip for its usable seconds.
- **Against:** it is the **lowest‑leverage** assist for "a reel worth keeping." The reel is made or broken by *which clips and in what order* (M2), not by shaving 2s of blur. Viewers never notice a loose trim; they very much notice a boring clip that shouldn't be there. So M1 optimizes the assist that matters least and defers the one that matters most.
- **Resolution (recommended): keep trim‑first, but add *manual* selection to M1.** The schema already has `included`, `deleted`, and their `origin` fields. This is *manual* curation, not the M2 *assist*, so it doesn't violate "selection assist is M2." M1 becomes **import → user curates which clips → AI trims the keepers → render → export** — which *can* hit 60–90s and *is* genuinely better than free tools (curated + explained trims + local). Cost: extend WO‑109; no new schema. **Alternative:** honestly downgrade the M1 gate to "a correctly trimmed, correctly rendered full‑day sequence + lossless round‑trip" and move "reel worth keeping" to M2 — intellectually honest but concedes M1 has no product value, resurrecting the exact ADR‑006 problem ADR‑007 killed. The first option dominates.
- **Classification: Blocker before ADP.**

**Center‑crop, no clip audio, mandatory music, limited edits vs the exit gate:**

- **No clip audio in M1 is justified by an M3 reason that is inert in M1.** ES‑001 §8.2 justifies muting all clip audio because "at 4× speech is unintelligible" — but **M1 has no speed ramps (all rate 1.0)**. The only M1‑valid reason is "ambience jump at cuts." For family footage, the kid's laugh or the wave *is* the memory; mandating music + silence is a strong editorial claim for a tool whose identity is "the user directs." The `audio.retain` field exists, frozen to false. **Recommend** reconsidering clip‑audio retention on rate‑1.0 segments for M1. Trade‑off: ducking/mixing is real work. **Classification: Required before a real‑user claim / Watch for owner‑M1.**
- **Center‑crop** will decapitate people at frame edges in landscape clips — and people are the subject. WO‑104's "stop‑and‑ask if centre‑crop proves unacceptable" is the right guard; saliency reframing is correctly deferred. **Watch.**
- **Honest M1 success criterion:** replace "export a reel worth keeping" with: *on a real 50‑clip day — every clip probed or flagged; user curates to a short set; AI proposes a legible trim per keeper; keep/adjust/dismiss all persist and round‑trip byte‑identical; both export variants pass QA; **and the owner rates the result at least as good as the same day's Apple Memory, or records specifically why not.*** The comparison‑to‑Apple bar is the actual test and should be *in* the gate, not implicit.

---

## 4 · Architecture and data contracts

**The explicit test requested — can `origin` + "last proposal" distinguish accepted / adjusted / dismissed / rerun / superseded? No. It cleanly distinguishes two of the five.**

Per field, state = (`origin`: `proposed|user`) + (`proposals.<field>`: a *single* `{value, at, reasons}`).

| Intended state | Representable? | Why |
|---|---|---|
| **Accepted** (proposed, unchanged) | ✅ | `origin=proposed`, `proposals.value == segments` |
| **Adjusted** (user tuned handles) | ⚠️ collides | `origin=user`, proposal retained, `effective ≠ proposal` |
| **Dismissed** (reverted to full clip) | ⚠️ collides | `origin=user`, proposal retained, `effective = full clip` |
| **Rerun** | ❌ | re‑run **overwrites** the prior proposal (ES‑001 §5.3); no count, no prior value |
| **Superseded** | ❌ | only "what the AI *last* proposed" is kept; superseded proposals are destroyed |

- **The adjusted/dismissed collision:** both are `origin=user` with a retained proposal. The only discriminator is "is effective == full clip?" — which **collides** with (a) a user legitimately adjusting *to* the full clip and (b) the §5.2.5 fallback where the *proposal itself* is the full clip. So you cannot robustly separate "the AI was basically right, I nudged it" from "I threw the AI away."
- **Why this is load‑bearing, not academic:** ADR‑006 and ROADMAP §"Stop/de‑scope" both claim the assists‑earn‑their‑place trigger is "readable **directly from `origin`** … proposals kept versus discarded." But `origin` is binary and conflates a 0.2s nudge (assist succeeded) with a total re‑do (assist failed). **The metric that fires the de‑scope decision is under‑determined by the exact field the docs say makes it "a query, not a study."** ADR‑008 caught *half* of this (added `proposals`) but stopped at the *last* proposal, not a disposition or history.
- **This is unlikely to be caught by the WO‑100 clicking prototype** — it's an audit/measurement gap, not a flow/screen gap. Relying on ADR‑008's prototype to surface it is optimistic; put it on the gap list explicitly.
- **Fix (before WO‑101 freezes §4):** add a per‑field **`disposition`** enum (`pending | accepted | adjusted | dismissed`) set on the user's terminal action, and make `proposals.<field>` a small **append‑only history** (`{value, at, reasons, disposition, superseded_by}`) so rerun/superseded are first‑class. Then restate the trigger as "readable from `disposition`," with a defined adjusted‑vs‑kept tolerance. Trade‑off: larger `project.json`, more write logic — but this *is* the audit trail the product's identity promises.
- **Classification: Blocker before ADP** for `disposition`; **Required before M2** for full history (M2 multiplies this across selection/order proposals).

**Other schema gaps to resolve before WO‑101:**

- **`target_duration_s` has no consumer in M1** — wire it to a warning ("3:40 vs 1:15 target") or mark it M2‑only. Don't freeze a dead field silently.
- **`stage_approvals.trim` is one timestamp, but trim is per‑clip.** §7 says a clip edit invalidates only `finalize`, so trim approval can go stale w.r.t. later per‑clip edits. Define whether post‑approval per‑clip edits re‑open the trim gate.
- **`segments[]` is an array but "v1 UI enforces exactly one"** — make that a validated invariant, or WO‑104/112 can emit multi‑segment and break M1 assumptions.
- **`content_hash` = "sha256 of bytes"** — full‑file hashing of 50 large videos isn't budgeted in the ≤5‑min proxy target (§9). Specify full vs sampled.
- **Absolute paths everywhere** (`media_root`, `sources[].path`, `music.track_ref`) with **no re‑link flow.** The product promises faithful reload "for later editing," but a memory‑keeper reorganizing folders breaks every project, and there's no relocation UI.

**Local privacy/security beyond "bind to 127.0.0.1":**

- **Local browser access is an unhandled attack surface.** Binding to `127.0.0.1` blocks *remote* hosts, but **any website the user has open in a browser can issue requests to `http://127.0.0.1:PORT`** (localhost CSRF / DNS‑rebinding class). A malicious page could POST `/api/export`, or probe `/api/project/{id}` to enumerate the absolute media paths — which by ADR‑002's *own* threat model reveal "where a family sleeps." ES‑001 §9 says "binds 127.0.0.1 / no outbound network" and is **silent on protecting the local API from other local origins.** For a privacy‑branded product this is a genuine gap the "localhost" framing hides. **Fix:** Origin allowlist + a random per‑launch token in the URL + CORS default‑deny, specified in §9 and guarded in WO‑113. **Classification: Required before ADP** (retrofitting auth after WO‑106 is painful; owner‑only threat is low but the spec must precede the build).
- **Proxy/render lifecycle:** proxies (540p) and renders are **derivatives of children's footage** with no location policy, no cleanup, and — critically — **no deletion path for consent withdrawal** (ADR‑002 requires derivatives be deletable). See §6/WO‑100. **Required before a later milestone.**
- **Path leakage in surfaced errors:** the `{error_code, human_text, remediation}` envelope, job errors, and `last_render.path` can surface absolute media paths into UI/logs on a repo people screenshot. **Scrub paths in surfaced errors. Watch → Required.**

---

## 5 · Validation and evidence

**Was retiring the autonomous‑ranking programme correct? Yes — but the pivot over‑corrected and now schedules *no* early evidence at all, including for its own pivotal assumption.**

- **Evidence:** ADR‑006 rightly retires the ranking corpus/experiment. But `PROJECT.md` grades the pivot's *new* pivotal belief — "users prefer transparent, approvable assistance to one‑tap automation … **the whole product rests on this**; check with real users early" — as `assumed`, with **no experiment, no gate, and no date.** The old regime at least had EXP‑009 for "prefer assisted to automation." **The project retired a test for the old pivotal claim and scheduled none for the new one.**
- **What was dropped that shouldn't have been:** **EXP‑001, the competitive‑floor comparison** (run one real day through Apple/Google/CapCut and score against "would I post this?"), was *not* autonomy‑dependent — it measures the floor the product must beat *regardless* of framing. It costs an afternoon and is the single highest‑value pre‑ADP evidence. Retiring it with the rest was over‑correction.
- **What lightweight evidence should be required:**
  - **Before ADP (both near‑free):** (1) the competitive‑floor scoring above; (2) a 30‑minute paper/prototype preference probe with 1–2 real memory‑keeper friends — "would you review explained proposals, or do you just want one tap?" — directly testing the pivotal assumption the whole roadmap rests on. Plus a small **perf spike** to confirm the ≤5‑min §9 targets before they're frozen as NFRs (if a 50‑clip day is 20 min, the "one sitting" promise breaks).
  - **Before M2:** the trim keep/adjust/dismiss rates on M1's real day (needs the §4 `disposition` fix).
  - **Before any "is it good" claim:** the deferred real‑user check — already binding per ADR‑006/007. **This owner‑vs‑real‑user separation is a genuine strength** and is well articulated ("owner approval is a build gate, not evidence of quality").
- **Claims treated as decided but still `assumed`:** transparency‑is‑preferred (whole roadmap built on it); "a legible selection heuristic makes a trusted first pass" (M2 built on it); "local web app + FFmpeg hits ≤5 min on Apple Silicon" (a *requirement* number that's actually an untested assumption); "rules‑based speed ramps read as intentional" (M3 — and `prototype-definition.md` itself warns "a wrong speed ramp reads as kitsch instantly").
- **Classification: Required before ADP** for the two probes + perf spike (low cost, high leverage; `PROJECT.md` itself says to check the pivotal assumption "early"). The stale ledger that *should* track these is a Blocker — see §6.

---

## 6 · Delivery governance and documentation quality

**The pivot was absorbed in the decision records but not in the narrative records — and the repo is public, where `PROJECT.md` itself says "the artifact trail is a deliverable in its own right."** `origin/main` is at the pivot commit `174d43e` and is **even staler than local** — it lacks ES‑001, ADR‑007, ADR‑008, the 3‑milestone roadmap, and the M1 backlog (all in the three unpushed commits). So a visitor today sees the pivot ADRs *and* a validation‑first README, with none of the specs that explain the current direction.

**Contradiction inventory (public‑facing unless noted):**

| # | Contradiction | Disposition |
|---|---|---|
| 1 | **README** — "no accepted decisions … next gate is approval of PROJECT.md, ROADMAP.md, and the validation plan … all four ADRs … validation precedes specification … pre‑committed kill criteria" — entirely pre‑pivot | **Update — Blocker** (front door) |
| 2 | **EVIDENCE‑LEDGER** — lists only ADR‑001–004 "all Accepted"; C‑01 "ranking … pivotal … the project's entire differentiation rests here" (the *retired* claim); "no remote or published branch" (contradicts the public remote); log ends "PROP‑01 pilot launched" (ADR‑006 *withdrew* the project from PROP‑01). And `AGENTS.md` actively tells agents to trust this file. | **Rewrite — Blocker** |
| 3 | **risk-register** — kill criteria "locked by ADR‑004" (superseded); EXP‑001/003/008/009; "corrections > 8" — asserts *retired* kill criteria as live policy | **Update — Blocker** |
| 4 | **COMPONENT‑DECOMPOSITION** — `project.json` sketch uses `trim`+`speed` with **no `proposals`** (repeats the exact pre‑ADR‑008 gap) and §4 restates "origin makes it a query"; §4/§5 "manual capability … built first (M2–M3)" contradicts ADR‑007 | **Reconcile to ES‑001 — Required before ADP** |
| 5 | **SYSTEM‑VISION** — "today's plan is a local CLI … ADR‑001 operative … `timeline.json`" — false post‑ADR‑005 | Banner + retire‑in‑place |
| 6 | **prototype-definition** — CLI POC; "**speed changes are advisory flags only, never applied automatically**" — contradicts M3 core speed ramps | Banner + retire‑in‑place |
| 7 | **sample-media-test-strategy** — "VALIDATION‑PLAN is authoritative for thresholds" (retired); ≥95% recall gates | Banner + retire‑in‑place |
| 8 | **NOTION‑PROJECTION** — "four ADRs … PROJECT/ROADMAP/VALIDATION not yet accepted" | Update or mark projection‑only |
| 9 | **INTEGRATION‑PLAN** — preconditions cite ADR‑001–004 + validation plan; Phases 1–5 (now 3 milestones) | Banner + retire‑in‑place |
| 10 | **"approves each of NINE stages"** (AGENTS/PROJECT/handoff) vs 5‑key `stage_approvals` | **Fix wording — Blocker** (§2) |
| 11 | **ADR‑002 names "WO‑002" consent workflow** that no longer exists in the M1 backlog | **Restore a consent WO — Blocker** (below) |
| 12 | 2 HTML vision files render the CLI framing | Banner or archive |

The retired ADRs/VALIDATION‑PLAN got clean banners — **apply the same treatment to the un‑bannered stale set.** Update README/ledger/risk‑register content; banner or move the rest to `docs/archive/`; reconcile COMPONENT‑DECOMPOSITION to ES‑001. Cost is low; the reputational cost of a self‑contradicting public repo undercuts the very "clean pivot via superseding records" the portfolio is meant to demonstrate.

**WO‑100 "real thumbnails" vs consent‑before‑media — a real conflict, and WO‑100 is the *first* work.**

- **Evidence:** ADR‑002 (and CLAUDE.md/AGENTS.md) hard constraint — "**no media collection before consent is recorded; consent precedes any copying of footage**," derivatives deletable on withdrawal. ADR‑008/WO‑100/handoff rule 3 — "**use real thumbnails from actual footage.**" A thumbnail is a frame extracted from footage = a **media derivative** = personal data (possibly a child's face).
- **Three ways it bites:** (1) the M1 backlog has **no consent/deletion WO** — the old WO‑002 lived in the retired phase‑1 backlog and wasn't carried forward, so ADR‑002's own precondition references a WO that doesn't exist; (2) `.gitignore` globally ignores `*.png/*.jpg`, so thumbnails **can't be committed** to `fixtures/` without a dangerous `git add -f` — meaning a fresh clone of the public prototype shows grey boxes, defeating rule 3; (3) creating thumbnails at all is "copying footage" gated behind a consent workflow that doesn't exist.
- **Resolution:** restrict WO‑100 thumbnails to **the owner's own footage containing no other identifiable people/children**, record a lightweight self‑consent note *first*, extract **locally**, add `fixtures/` to `.gitignore` with a documented "populate locally" step and a committed grey‑box fallback; and **restore a minimal consent/deletion WO to M1** ahead of WO‑100. **Alternative:** ship rights‑cleared synthetic/stock thumbnails (no real people) for the committed artifact and do "real thumbnail" readability testing only in a local owner session. Trade‑off: weaker readability test on the public artifact, zero ADR‑002 exposure.
- **Classification: Blocker before ADP** (the first task cannot start honestly otherwise).

---

## Final recommendation

### 1 · Go / Revise / Stop → **REVISE**

Continue — the direction is largely right and the governance is strong — but **resolve the blockers below before authorizing the ADP.** They are cheap now (spec/doc edits) and become migrations across every saved project and a self‑contradicting public repo after WO‑101. Do **not** stop: none of the findings is a killed premise; they're pre‑code corrections, which is exactly what this gate is for. Do **not** go as‑is: authorizing the ADP today freezes an M1 that can't meet its own exit gate and an audit schema that can't measure its own de‑scope trigger.

### 2 · Five highest‑leverage changes before ADP

1. **Add *manual* clip selection/delete/restore to M1** (extend WO‑109; schema already has `included`/`deleted`/`origin`). Without it, M1's "reel worth keeping" gate is unreachable and M1 is plausibly worse than a free Apple Memory. This is the single change that makes M1 real.
2. **Fix proposal provenance before WO‑101 freezes §4:** add a per‑field `disposition` (`pending/accepted/adjusted/dismissed`) and a small append‑only proposal history; restate "assists earn their place" on `disposition`, not binary `origin`. Otherwise the product can't measure the thing it exists to measure.
3. **Bring the public repo into one voice:** rewrite README + EVIDENCE‑LEDGER + risk‑register to the pivot; fix "nine gates → five"; banner/archive SYSTEM‑VISION, INTEGRATION‑PLAN, prototype‑definition, sample‑media‑test‑strategy, NOTION, the HTML files; reconcile COMPONENT‑DECOMPOSITION to ES‑001 — before the next push.
4. **Reconcile WO‑100 with ADR‑002:** restore a minimal consent/deletion WO ahead of WO‑100, scope thumbnails to owner‑only no‑third‑party footage kept local, and add `fixtures/` handling to `.gitignore` with a grey‑box fallback.
5. **Harden the local surface beyond `127.0.0.1`:** Origin allowlist + per‑launch token + CORS deny + path‑scrubbed errors, specified in ES‑001 §9 and guarded by WO‑113, before the API is built.

Plus two near‑free evidence probes (§5) that gate nothing but should precede committing three milestones of build: the **competitive‑floor scoring** of one real day, and a **30‑minute preference probe** with 1–2 friends. And a **perf spike** before freezing the ≤5‑min §9 numbers.

### 3 · Revised direction statement

> An **explainable, local‑first, auditable** first‑draft reel editor for private family footage, run as a Mac‑local web app. Its identity is **privacy + a persisted, plain‑language record of every edit decision** — the two things incumbents don't provide — not "control," which they already do. The user **curates** which clips make the reel and the AI does the **mechanical tidying** (trim first, selection and speed later), each proposal carrying a reason the user keeps, adjusts, or dismisses, with the disposition recorded. There are **five approval gates**, not nine. **M1's honest bar is: on a real 50‑clip day, curate + AI‑trim to a short reel the owner rates at least as good as that day's Apple Memory, saved and reopened byte‑identical** — not a trimmed dump of every clip. Whether a memory‑keeper values explanation enough to review, rather than tap once, is the **one belief the whole product rests on and is currently untested** — it gets a cheap real‑user probe before the ADP, and a binding real‑user gate before anyone calls the product good. It remains a governed‑systems portfolio piece and a tool the owner wants; commercial viability stays deferred behind the permanent constraints (2–6 uses/year; no Instagram music; iPhone→Mac + BYO‑track friction) recorded honestly rather than wished away.

---

## Classification summary

| # | Finding | Class |
|---|---|---|
| §3 | M1 has no clip removal → "reel worth keeping" gate unreachable | **Blocker before ADP** |
| §4 | `origin` + last‑proposal can't distinguish 5 proposal states; add `disposition` before §4 freeze | **Blocker before ADP** |
| §6 | Public repo self‑contradicts (README, EVIDENCE‑LEDGER, risk‑register) | **Blocker before ADP** |
| §6 | WO‑100 real thumbnails vs ADR‑002 consent; no consent WO in M1 | **Blocker before ADP** |
| §2 | "Nine gates" wording vs five‑key `stage_approvals` | **Blocker before ADP** (doc) |
| §4 | Local API unprotected against other browser origins (localhost CSRF) | **Required before ADP** |
| §5 | Two cheap evidence probes + perf spike before ADP | **Required before ADP** |
| §6 | COMPONENT‑DECOMPOSITION reconciled to ES‑001 | **Required before ADP** |
| §4 | Proposal history (rerun/superseded); proxy/render deletion path; source re‑link | **Required before M2** |
| §2 | Confidence‑ranked review + on‑demand reasons | **Required before a later milestone** |
| §3 | Clip‑audio retention on rate‑1.0 segments in M1 | **Required before a real‑user claim / Watch (owner‑M1)** |
| §1 | Preference bet unproven; reposition around privacy+audit as the wedge | **Watch** |
| §1 | iPhone→folder + BYO‑music pre‑value friction | **Watch (M1) / Required before real‑user claim** |
| §3 | Center‑crop decapitation on people‑at‑edges | **Watch** |
| §4 | Absolute‑path leakage in surfaced errors/logs | **Watch → Required** |

---

*This review authorizes nothing. It is advisory input to the owner's decision on whether to authorize an ADP for M1, and should be reconciled into the Notion "Deliverables & Gates" projection as a review record, not as an approval.*
