# Constraints — the guardrails

**Normative.** These bind implementation and may not be relaxed by an agent's own
judgment. Each is a **stop-and-ask**: if the work seems to require breaking one,
stop and put the question to the owner.

Transcribed 2026-07-28 from ADR-002, ADR-003, ADR-005 and ADR-011/013, which are
now in [`docs/archive/decisions/`](archive/decisions/). **The archived ADRs are
history; this file is the authority.** They are transcribed rather than
reinterpreted — the v3z redesign changes the product's shape, not its posture,
so none of these were up for revision in that redesign.

Constraints that v3z *does* put in play — approval gates, staged progression,
proposal `disposition`, whether reasons are displayed — are deliberately **not**
here. They are open, and belong to the decision session recorded in
[PLAN-v3z-rebuild.md §1](implementation-plans/PLAN-v3z-rebuild.md).

---

## Privacy and data posture

- **No face recognition and no person identification, at any phase.** Face
  *detection and counting* without identity is permitted.
- **No media collection before consent is recorded.** Consent is written, covers
  footage of children specifically, names what the footage is used for, and is
  recorded *before* media is copied. It is withdrawable; on withdrawal that
  contributor's media and derived artifacts are deleted and the deletion
  recorded.
- **Originals are opened read-only**, read in place, never modified. Derived data
  is written to a separate output directory. **The system has no delete path for
  source media**, and nothing is ever written beneath `media_root`.
- **Original media never leaves the device.** No network egress of media,
  derivatives, or metadata in the default path. Cloud processing of originals is
  out of scope.
- **GPS and identifying metadata are stripped from any rendered export.** No
  telemetry containing media, derivatives, or file paths.
- **Nothing is published, posted, or transmitted without an explicit human act.**
  There is no auto-publish path.
- **Excluded until a new decision says otherwise:** face recognition or person
  naming, cloud library sync, auto-posting, audio transcription, and any
  preference learning that is not user-visible and user-editable.

## What must never be committed

The repository is **public** (`origin` → `github.com/vasudevap/KwikReel`).

- **Never commit media, consent records, or any identity map.** Git history
  persists after deletion, and consent is withdrawable — a commit makes that
  impossible to honour.
- `project.json` contains absolute paths to private footage. It is gitignored;
  keep it that way.
- **Fixtures:** only `fixtures/synthetic/` is committed — synthetic or
  rights-cleared, with no real footage and no identifiable real people. Real
  thumbnails are the owner's own, generated into `fixtures/local/` (gitignored,
  never committed), behind a recorded self-consent + lifecycle note written
  *before* extraction.

## Music and licensing

- The user supplies a track they hold rights to. Royalty-free libraries are the
  documented path.
- **No commercial-track extraction and no claim of licensed-music support, at any
  phase.** Instagram's library is a **timing reference only**, never exportable
  media.
- **No `madmom`, no Essentia**, and no dependency whose licence would restrict
  distribution. Beat and section detection uses **librosa (ISC)** only. Adopting
  any distribution-restricting dependency requires an explicit decision first.

## Form factor and state

- A **local web application**: a browser UI served by a local backend on
  localhost, with FFmpeg-based ingest, analysis and render in that backend
  process.
- **Canonical state is a versioned `project.json`** that round-trips losslessly.
- The analysis and proposal layer stays independent of both the UI and the
  renderer, so a native shell or an NLE export adapter can be added later without
  rewriting the assists.

## Local delivery security

Binding to `127.0.0.1` is necessary but **not sufficient** — any web page open in
the user's browser can issue requests to `http://127.0.0.1:PORT`.

- **Host / Origin allow-listing.** Reject cross-site `Origin`/`Referer`; validate
  `Host` against an allow-list (blunts DNS-rebinding).
- **No permissive CORS.** No `Access-Control-Allow-Origin: *`, no wildcard
  credentials. Default-deny; the local frontend is same-origin.
- **Capability token per launch**, delivered same-origin and **required on every
  state-changing endpoint**, so a blind cross-site `POST` cannot act.
- **Path scrubbing.** No absolute media path appears in any error envelope, job
  error, log, or surfaced field — basenames or redaction only.
- **Every protection is a guard test that fails when the protection is removed.**
  A new mutating route without its own guard test is an incomplete route.
- **Binding beyond `127.0.0.1` is a stop-and-ask.**

## Working discipline

- **Nothing in `docs/archive/` may be cited as authority.** To use something from
  it, promote it into a live document first.
- Preserve the distinction between **proposed**, **accepted**, and
  **implemented**. A document describing a thing is not the thing.
- **Owner approval is a build gate, not evidence of product quality.** Subjective
  judgment of one's own output reliably overestimates it; real users must
  exercise the tool before it is called good.
- **Assists earn their place.** An assist that costs more to review and correct
  than to do by hand is de-scoped to manual — recorded honestly, not argued
  around.
- **A check that could not run is recorded with the exact command and the
  reason** — never silently skipped.
- Load-bearing claims are graded in
  [`docs/specs/EVIDENCE-LEDGER.md`](specs/EVIDENCE-LEDGER.md). If you rely on a
  claim, check its grade.

## Authorization required

- **Creating or changing a public remote repository**, and **every push to
  `origin`**, is a separate decision. Present owner, name, visibility, the exact
  command, expected effect and rollback path before acting. Authorization for one
  push is not standing permission for the next.
- **No GitHub Actions**, workflow, required-check, runner or branch-protection
  change without explicit owner authorization.
