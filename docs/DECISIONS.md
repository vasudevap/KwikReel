# Decisions — the v3z departures

**Status: DECIDED — owner, 2026-07-28. Normative.**

This is the record `SPEC.md` is written against. It outranks anything older.
Where it disagrees with an archived document, this file wins and the archived
one is not to be cited.

**This file is append-only, and it is also the amendment path for
[`CONSTRAINTS.md`](CONSTRAINTS.md).** New decisions are added as dated sections
below; existing entries are never rewritten. Where two entries touch the same
subject, the later one governs — **nothing supersedes by cross-reference**,
because a web of records pointing at each other is precisely the document graph
the 2026-07-28 clean cut removed.

A decision that changes a guardrail must **name the constraint and say what is
being given up**. One that only records a preference needs neither.

---

## 1 · What was decided

| # | Decision |
|---|---|
| **A-1** | **The five approval gates are removed.** Nothing advances by being signed off. Control lives in the toggles instead: nothing happens until Trim or Speed is pressed, pressing again undoes it, and neither ever touches a clip edited by hand |
| **A-2** | **Proposal reasons are not shown in the editing surface — they are written to the Log.** The Log is where you read back what the machine proposed and why |
| **A-3** | **`disposition` is kept**, against the v3z draft, and is written to the Log as it changes. The Log is the audit trail — the way to learn whether the assists are earning their place |
| **A-3b** | **`accepted` is written at export.** Every AI value not adjusted or rejected by the time you export counts as accepted, and the export writes one summary line to the Log (*"kept 14 of 19 AI trims"*). `adjusted` is written when a handle moves; `dismissed` when the reject key is pressed |
| **A-4** | **Audio becomes two 0–100% levels, Music and Clip, and one exported file.** The three mutually exclusive modes, the per-mode exports, Balance and Duck are all retired. Both levels at zero is silent |
| **A-5a** | **Speed ships in the first release, built last** — after trim is built and proven, so it can be de-scoped to manual without holding anything else up |
| **A-5b** | **The clip-selection and ordering assist is cancelled permanently.** The machine never proposes which clips belong in the reel, only how they are timed |
| **A-5c** | **There is one product, not three milestones.** With selection cancelled and speed pulled forward, the staged roadmap is retired |
| **A-6** | **The 1.0-second minimum trim is retired for user and machine alike.** The machine may trim a clip to nothing, which removes it from the reel. Sub-second and empty results are warned in the Log, never blocked |
| **A-7** | **The originals-are-read-only assurance goes in the Log**, as a **pinned line** — always present at the foot of the Log, never aged out. (Pinning is the mechanism; the placement is the decision. Without it the line would be the oldest entry in a three-line newest-first display and would vanish within seconds of opening the app.) |
| **A-8** | **v3z is the locked design.** Mockup iteration stops. A correction pass is expected and accepted once the rig is operable, because v3z has never been operated |
| **N-4** | **When the reel outruns the music, the track stops and the reel plays on with clip audio only.** A fade-out is a **shelved refinement**, not an open question — revisit after real use |
| **N-6** | **No cap on speed.** The assist's own rule still tops out at 2×, so this governs hand-set rates only. Past ~2× the audio filter must be chained and degrades audibly: **recorded as a known, accepted cost** |
| **N-7** | **The HUD row stays**, carrying LOCAL and the nameplate |
| **N-9** | **Saves are optimistic with a visible failure path.** A control responds the instant it is touched; if the write fails it visibly reverts and the Log says why. **A silent save failure is never acceptable** |

---

## 2 · What this obliges `SPEC.md` to carry

Three commitments fall out of the answers above. They are the load-bearing part
of this document.

### 2.1 · The Log is the audit trail — and it is now the biggest new unit

It was drawn as three lines of glass for occasional warnings. These decisions
give it **six distinct jobs**:

1. Proposal reasons (A-2)
2. Warnings when a clip is trimmed to nothing or sub-second (A-6)
3. Disposition changes as they happen (A-3)
4. The kept-count summary at export (A-3b)
5. Save failures (N-9)
6. The pinned read-only line (A-7)

**`SPEC.md` must specify:** the event vocabulary, ordering, how deep it scrolls,
whether it survives reopening a project, and how pinning works against a
newest-first list.

**Flagged honestly:** this is the most likely thing to need the correction pass
A-8 authorises. A forty-clip reel writes forty-odd reason lines into a three-line
window, and the same window is where a save failure has to be noticed. Reading
back an audit trail and catching a live warning are different jobs, and one strip
is now doing both.

### 2.2 · "An assist never overwrites a hand-edited clip" is a tested requirement

Not a behaviour — a correctness requirement with its own tests. With the gates
gone (A-1) this is the entire mechanism by which the human stays in charge. If it
is buggy, the machine silently overwrites your work, which is precisely the
failure the gates existed to prevent.

### 2.3 · `disposition` keeps its writers

It survives (A-3) but the thing that used to write `accepted` does not. The three
writers are now: **handle movement → `adjusted`**, **reject key → `dismissed`**,
**export → `accepted`** for everything untouched (A-3b). A field with no writer
measures nothing, so this is not an implementation detail.

---

## 3 · Consequences worth stating plainly

- **The staged roadmap is gone.** There is no second release to defer a problem
  into. Anything cut is cut.
- **Ledger claim C-03** — *a legible trim heuristic is a helpful starting point* —
  now has a path off `assumed` again, via the export summary in A-3b. Keeping
  `disposition` is what restored it.
- **Speed carries the most risk of any decision here.** It is the least
  predictable assist, it reopens the settled question of natural clip audio, and
  A-5a's "built last" is what preserves the option to drop it.
- **v3z is locked but unproven.** Six static renders, no interaction logic. The
  design is settled; whether it is *good* is untested, and A-8 accepts that
  trade knowingly.

---

**Decided:** owner, 2026-07-28. `SPEC.md` may now be written.
