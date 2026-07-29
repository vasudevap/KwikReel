# ADR-003 — Music and licensing posture

**Status:** Accepted — owner-approved 2026-07-23
**Risk addressed:** music/licensing infringement, rated High likelihood / High impact in `docs/research/risk-register.md`.

**On acceptance (2026-07-23):** the music/licensing posture is ratified — user-supplied rights-cleared track, a clean no-music export, Instagram's library as a timing reference only, and no commercial-track extraction at any phase. One correction was applied at ratification (resolving `phase-1-backlog-deltas.md` B-5): **Essentia is dropped from the approved path.** Its AGPLv3 copyleft is distribution-restricting — the same rule that excludes `madmom`, and verified against Essentia's published licensing terms. Beat/section detection uses **librosa (ISC)** only; adding Essentia later requires a new ADR.

## Context

Beat-synchronised cutting is central to how a reel is perceived, and the tracks users most want are the licensed songs available inside Instagram. Those tracks are usable only within Instagram's own applications. A third-party tool cannot legally export a rendered video containing them.

This creates a structural constraint that shapes the product rather than a detail to settle later: the single most-requested feature is legally unavailable, and adding an Instagram song after upload will not match beat-aligned cuts, because the in-app timing offset is user-controlled and approximate. Platform durations and policies also change without notice, so architecting around them invites silent breakage.

Two smaller hazards sit alongside it. Dependency licensing matters if this ever becomes a commercial product — `madmom`, an accurate beat-detection library, is GPL-licensed with patchy maintenance, and a GPL dependency in a distributed commercial binary is a real constraint rather than a theoretical one. And a beat-detection benchmark run against a corpus of commercial tracks would itself be a licensing problem.

## Options considered

1. **User-supplied rights-cleared track, plus a clean no-music export (recommended).**
2. Ship a bundled royalty-free library. Adds licensing administration and storage for no validation value; the question under test is editorial judgment, not music curation.
3. Attempt Instagram music integration. Not legally available to third parties. Rejected outright.
4. Match a temp track's BPM to a target Instagram song so the user can swap in-app. Fragile, oversold, and it degrades quietly — the user discovers the mismatch after posting.

## Proposed decision

Adopt option 1.

- The user supplies a track they hold rights to. Royalty-free libraries (Artlist, Epidemic, YouTube Audio Library) are the documented path.
- The system exports **with** that audio for personal and family sharing, and additionally exports a **clean no-music version** for users who intend to add an Instagram song in-app — with an explicit warning that beat sync is lost.
- Instagram's licensed library is treated as a **timing reference only**, never as exportable media.
- A beat-map JSON export is offered as a diagnostic, not promised as a feature.
- **No commercial-track extraction, and no claim of licensed-music support, at any phase.** Hard constraint; changeable only by a new ADR following legal review.
- The validation corpus uses rights-cleared tracks only, including for beat-detection benchmarking.

**Dependency licensing.** `madmom` is excluded as a core dependency (GPL, patchy maintenance) despite its accuracy. Beat and section detection uses **librosa (ISC)** only. **Essentia is excluded** on the same rule that excludes `madmom` — its AGPLv3 copyleft is distribution-restricting (more so than madmom's GPL); adopting it later requires a new ADR. Any dependency whose licence would restrict distribution requires an ADR before adoption; the previous draft of `prototype-definition.md` proposed benchmarking madmom and has been corrected.

## Consequences

- The project can never advertise the feature users most want. This caps consumer appeal and is a permanent, structural limit — recorded here so it is not rediscovered as a surprise during productization.
- Requiring the user to supply a track adds friction to the first run and must be handled well in the review experience.
- Exporting two variants doubles render time for a case many users will not need; this is accepted for validation and revisited if measured as a real cost.
- Licence hygiene is settled before any dependency is adopted, rather than discovered at packaging time when it is expensive to unwind.
