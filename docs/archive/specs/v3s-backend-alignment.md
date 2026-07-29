# v3s → backend alignment · decisions register

**Status: decided, not built. No code has been changed.** Owner interview 2026-07-28.

This is the record of the frontend/backend reconciliation. Group **1** is the
owner's direction, obtained decision by decision. Group **2** is the one item
left open, which **blocks implementation**. Group **3** is what the frontend
still has to change — v3s as drawn no longer expresses all of these decisions,
so it is **not yet the locked design**. Group **4** is the resulting backend
work.

Nothing here is authorised for build. ES-001 §4 is frozen; the schema changes in
group 4 need an ES-001 amendment, and D-01, D-02 and D-11 need ADR action.

---

## 1 · Decisions

| # | Decision | Was |
|---|---|---|
| **D-01** | **Reasons are recorded, not displayed.** The proposer keeps producing a `ReasonRecord` per contributing factor and `project.json` keeps storing them, so they remain inspectable and available to a later UI. Nothing renders them in M1. | ADR-006 required every proposal to display its `human_text` inline; ES-001 §5.3 called a reasonless proposal "a bug, not a cosmetic gap" |
| **D-02** | **Audio is two independent level sliders.** Music and Clip each get a 0–100% loudness slider — vertical, tick-marked, each with an LED that is off at 0% and on above it. The Music/Clip toggle buttons, the Balance knob and the Duck knob are all removed; the sliders subsume them. Per-clip mute (the row speaker) is retained. One reel exports as one file. | Three mutually-exclusive modes (`music`/`clip`/`silent`), one export file per mode (G-5); ducking deferred to §12 |
| **D-03** | **"Remove suggestion" and "Suggest again" go on the Trim desk**, which already operates on one loaded clip and has header room. Index rows stay single-line. | Neither control existed in v3s; `disposition="dismissed"` and per-clip re-run were both unreachable |
| **D-04** | **Remove = exclude.** The single Remove / Put back verb writes `included`, preserving ADR-007's pairing rule so M2's selection assist has a control to be overridden by. `deleted` and its store invariant stay in the schema, unused in M1. | ES-001 §5.5 defined both operations; §10 exercised both |
| **D-05** | **Pre-folder state is client-side.** The Add screen's target, track and levels live in the browser and are written when Sources returns a folder. `media_root` stays required; `Project.music` becomes optional, since the track can be chosen before a project exists. | `POST /api/project` required both `media_root` and `track_ref` |
| **D-06** | **Thumbnails and peaks are computed on demand and cached.** Ingest gains no new work — relevant to WO-115a. Music peaks are keyed by **content hash**, not `project_id`, because the track can be chosen on the Add screen before any project exists. | No thumbnails at all; audio only as 1 Hz `Signals.audio_rms` behind `/api/analyze` |
| **D-07** | **Clips get an editable name.** Shown as the base name on ingest; renaming stores the new name in `project.json` against the source, and **never touches the original file**. The project keeps its link to the source on reopen. | G-3 fixed the display label to `basename(path)`; `Clip` forbids extra fields |
| **D-08** | **Narrow PATCH endpoints** for the hot fields, rather than a client write queue over the full-document PUT. | One `PUT /api/project/{id}`, optimistic-concurrency guarded |
| **D-09** | **Path is the primary source link, with hash repair on failure.** A dead path is re-found by content hash; a file that cannot be found comes back as unlinked. | `source_id` derived from content hash; `path` stored alongside |
| **D-10** | **One folder per project.** A second Sources pick replaces the root and restarts the reel, behind an explicit confirmation. Multi-folder is an M2 question, recorded as a de-scope. | Already implicit; now explicit, and the confirmation is new |
| **D-11** | **The 1.0 s minimum window is retired outright — for the user *and* the machine.** No floor anywhere. Sub-second and empty results are **flagged with a warning**, never blocked. | G-9 made the floor universal; §5.2 rule 5 bound the proposer to it and to "never emit an empty or silent result" |
| **D-12** | **Trimmed-to-nothing is derived, not stored.** `out_s <= in_s` means the clip is not in the reel: it greys out in the Clip index, the renderer and the duration sum skip it, and moving a handle back revives it for free. No schema change, no state to keep in sync. | No such state existed |
| **D-13** | **Relink lives on the damaged row.** An unlinked clip greys out and its row carries a Relink control opening a file picker. | No relink path existed |
| **D-14** | **Proxies while editing, real draft at Build.** The Monitor sequences proxies client-side, seeking each to its in/out, so edits show instantly. Build produces the real render that Review approves — so the thing approved is the thing that exports. | Proxies served per source; a draft render existed only after finalize |

---

## 2 · Open — blocks implementation

### OPEN-01 · Gate enforcement and where `finalize` sits

**Left open by explicit owner direction: do not begin implementation until this is closed.**

The facts it has to resolve:

- No endpoint reads `stage_approvals`. `propose_trim`, `finalize` and `export`
  all run regardless of whether anything was ever approved.
- [`app.py:221`](../../backend/api/app.py:221) — the scan job ends with
  `project.stage_approvals.ingest = _now_iso()`, so the Check gate approves
  itself. This also breaks G-8's derived resume point, which reads the earliest
  live stage whose gate is still null.
- `approve` accepts stages in any order.
- `approve('trim')` does not promote pending proposals to `accepted`, though
  ES-001 §5.3 states the rule. Under D-03 the gate is now the **only** producer
  of the green "Accepted" state the Clip index displays, since v3s has no accept
  button.
- v3s splits ES-001 §7.1's stage 8 into **Build → Review → Save** and puts the
  `▲` on Review. That changes what `finalize` means — "the draft was reviewed",
  gating export rather than render — and D-14 depends on that reading.

Until this closes, three `▲` marks in the masthead rail are decoration, and
ADR-006's constraint that nothing advances a stage without explicit approval is
unenforced.

---

## 3 · The frontend is not yet locked

v3s no longer expresses the decisions above. These changes are needed before
"frontend design locked" is true — call the result **v3t**.

1. **Sound panel rebuilt (D-02).** Two vertical 0–100% sliders with tick marks
   and per-slider LEDs, in theme. Remove the Music/Clip toggle buttons, the
   Balance knob and the Duck knob.
2. **Trim desk gains two controls (D-03)** — Remove suggestion, Suggest again.
3. **A warning surface (D-11).** With the floor gone for both the user and the
   machine, sub-second and empty results must be flagged somewhere. v3s has no
   warning affordance anywhere; one has to be designed.
4. **Relink control on the damaged row (D-13).**
5. **A confirmation for re-picking Sources (D-10).** v3s has no modal or
   confirmation pattern at all; this is the first.
6. **The greyed row now means four different things** — damaged source,
   removed by the user, trimmed to nothing, and unlinked. They currently share
   one visual treatment and need to be distinguishable, since three of the four
   are fixed in completely different ways.

### Recorded honestly, not argued around

D-01 takes reasons off the screen. D-11 lets the proposer return an empty
segment. Together they permit **AI trim to make a clip disappear from the reel
with no explanation shown** — the user sees a greyed row where a clip used to
be, and the reason it happened exists only inside `project.json`. Item 3 above
is the only thing standing between that combination and a silent surprise, which
is why it is listed as a design requirement rather than a nicety.

---

## 4 · Backend work implied

### 4.1 · Frozen-schema changes (one ES-001 §4 amendment)

| Change | Driver |
|---|---|
| `Project.music: Optional[Music]` | D-05 |
| `Clip.name: Optional[str] = None`, falling back to `basename(path)` | D-07 |
| New `AudioMix` on `Project`: `music_level: float`, `clip_level: float` (0.0–1.0). No `on`/`off` booleans — lit is derived from `level > 0` | D-02 |
| `Clip.audio.retain` becomes live, **default flipped to `True`** (every clip starts audible); drop the "not consulted in M1" note | D-02 |
| `AudioMode` retired. `Export.audio_modes` retired. `Export.last_render` collapses from a per-mode map to one `RenderRecord` — G-5 is retired with it | D-02 |
| G-9 retired from §4.5 and §5.2; §5.2 rule 5's "never emit an empty or silent result" retired | D-11 |
| No peaks field on `Music` — peaks are computed on demand, not stored | D-06 |

### 4.2 · New and changed endpoints

| Endpoint | Note |
|---|---|
| `GET /api/media/thumb/{source_id}` | On demand, cached (D-06) |
| `GET /api/media/peaks/{source_id}` | On demand, cached (D-06) |
| Track probe + peaks, keyed by **content hash** | Must work with no project in existence (D-05/D-06) |
| `POST /api/pick-file` | `osascript … choose file`; serves both track selection and relink. Only `choose folder` exists today |
| `PATCH /api/project/{id}` | name, target, audio mix (D-08) |
| `PATCH /api/project/{id}/clip/{source_id}` | name, order, included, segments, audio (D-08) |
| `POST /api/project/{id}/relink/{source_id}` | D-13 |
| `GET /api/export/{id}/download` | Replaces `/download/{audio_mode}` (D-02) |
| `POST /api/export/{id}` | Body loses `audio_mode` (D-02) |

Each new mutating route needs its own ADR-011 capability-token guard test — four
PATCH/POST routes, four guards. That is the cost of D-08 over a client write
queue, and it is real.

### 4.3 · Behaviour changes

- **Renderer** — `amix` weighted by the two levels, replacing the three
  non-composable mode branches in `_render`. Skip clips where `out_s <= in_s`
  (D-12). Fail with a stated reason when every clip is zero-length, rather than
  handing ffmpeg an empty concat.
- **`_timeline_clips`** — additionally skip `out_s <= in_s` (D-12).
- **QA** — `audio_ok` is "matched to the mode's expectation" today (§8.3). With
  no modes it must be re-derived from the levels: `music_level > 0` means the
  output must not be silent; both at 0 means it must be silent **and** still
  carry a valid AAC track.
- **`_music_for`** — currently hardcodes `duration_s=0.0` and never probes the
  file. Must probe for real (D-02/D-06).
- **Load-time relink** — dead paths searched by content hash under `media_root`,
  repaired silently where found (D-09).
- **Damaged sources** — `scan` currently builds `Segment(in_s=0, out_s=0)` for
  unreadable files. Under D-12 that is now *meaningful* rather than a latent
  bug: a damaged clip is naturally zero-length and greys out by the same rule.
  It still needs a distinct label from "trimmed away" (group 3, item 6).
- **All of OPEN-01**, once closed.

### 4.4 · Documents to amend

| Document | Why |
|---|---|
| ADR-006 | Narrowed by D-01: "every proposal carries a reason" stays, "shown inline" goes |
| New ADR | The audio model (D-02) — mix levels replacing modes, ducking still out |
| New ADR or ADR-008 amendment | Retiring G-9 (D-11) and locking the frontend baseline |
| ES-001 §4, §4.5 | The schema changes in 4.1 |
| ES-001 §5.2, §5.3 | G-9, rule 5, and the Trim desk's control set |
| ES-001 §5.5, §10 | D-04 — delete/restore de-scoped from M1's acceptance test |
| ES-001 §6 | The endpoint table in 4.2 |
| ES-001 §7.1 | The stage mapping below |
| ES-001 §8.1–8.3, §12 | The audio model and the QA expectation |
| `docs/work-orders/m1-backlog.md` | WO-102 (relink), WO-104/105 (audio), WO-106 (PATCH routes, gates), WO-108/109/110 (the v3t changes); new WOs for thumbnails and peaks |

### 4.5 · The stage mapping

v3s's rail has nine steps and ES-001 §7.1 has nine stages, but not the same nine.

| v3s step | Gate | ES-001 §7.1 |
|---|---|---|
| Sources | — | 2 · Sources (pick folder ~~+ track~~ — D-05) |
| Check | **▲ ingest** | 3 · Import (probe, proxies) |
| Choose *(M2)* | — | 4 · AI-select / order — inert |
| Clips | — | 5 · Curate |
| Trim | **▲ trim** | 6 · AI-trim |
| Speed *(M3)* | — | 7 · Speed — inert |
| Build | — | 8 · Finalize (render) |
| Review | **▲ finalize** | *(no ES-001 stage — see OPEN-01)* |
| Save | — | 9 · Export |

"Create project" (stage 1) has no step in the rail, and "Import" folds into
Check because sources import the moment they are selected.

---

## 5 · Sequence

1. **Close OPEN-01.** Nothing starts before this.
2. **Build v3t** — the six frontend changes in group 3. Until they exist, there
   is no locked design to implement against, and items 3 and 6 are genuine
   design problems rather than mechanical edits.
3. **Amend the documents** in 4.4 as one pass, so ES-001 and the ADRs describe
   the product being built rather than the one specified in July.
4. **Then build**, in the existing lane order, with the schema changes (4.1)
   landing first because everything else codes against them.
