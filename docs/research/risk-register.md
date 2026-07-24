# Risk register

**Status:** Re-based for the 2026-07-23 pivot and the 2026-07-24 course correction. Ratings are assessments, not measurements.

**Stop / de-scope triggers, not kill criteria.** The pivot (ADR-006) replaced ADR-004's pre-committed kill criteria with stage-boundary **stop/de-scope triggers**: *no convenience win* → conclude as a portfolio piece; *an assist is net-negative* → de-scope that stage to manual (stage-level, not project-level); *platform absorption of this transparent, approvable flow* → reassess differentiation. Firing one is a successful outcome, not a failure to argue around.

| Risk | Type | Likelihood / impact | Mitigation / trigger |
|---|---|---|---|
| **Users don't value explained, approvable assistance over one-tap** | Product | **Medium / Critical** | The pivot's pivotal belief (EVIDENCE-LEDGER C-01). Cheap early read via ADR-012 **CP-1** on the WO-100 prototype; binding real-user gate before the product is called *good*. If false → the review burden isn't worth it → reassess the wedge. |
| **Platform absorption: Apple/Google ship reviewable, explainable editorial reels natively** | Product | **High / Critical** | Largest product risk. Free, pre-installed, improving each OS cycle at zero acquisition cost. Competitive floor measured in **CP-2**, re-measured each milestone close. More platform *automation* is explicitly not the trigger. |
| Incumbent free tools already clear "would I post this?" on a real day | Product | Medium / High | CP-2 scores a real day through Apple/Google/CapCut blind against the same bar; if an incumbent clears it, revise framing before M2. |
| Weak trim/selection/speed proposals cost more to fix than to do by hand | Quality | Medium / High | Every proposal is overridable and gated; kept-vs-discarded is read from `disposition` (ADR-010); a net-negative assist de-scopes to manual (stage-level). |
| Quality signals discard a meaningful low-quality family moment | Quality | Medium / High | Trim is a *proposal*, never a delete; the full clip is always one control away; the §5.2.5 fallback proposes the whole clip when nothing clears the floors. |
| Music / licensing infringement | Legal | **High / High** | User-supplied rights-cleared track only; clean no-music export; Instagram library as a **timing reference only**; no commercial-track extraction at any phase (ADR-003). Beat/section detection uses **librosa (ISC)** only — no `madmom`, no Essentia. |
| Private footage, location, children, or paths leak | Privacy | **Medium / Critical** | Local-first; originals read-only, no delete path beneath `media_root`; no egress from the media path; `project.json` (absolute paths) gitignored and never committed (ADR-002). |
| **Local API reachable from other browser origins** (localhost CSRF / DNS-rebinding) | Privacy / security | Medium / High | "Bound to `127.0.0.1`" is necessary but not sufficient. Origin/Host allow-listing, no permissive CORS, per-launch capability token, path-scrubbed errors, guard tests (ADR-011; ES-001 §9; WO-113). |
| Incorrect chronology from timestamp/timezone metadata | Technical | Medium / Medium | Preserve raw metadata; capture-time order is user-editable; folder-order fallback; no silent reorder. |
| Near-duplicate detection collapses meaningful variation | Quality | Medium / Medium | Threshold calibration; restore-able decisions; duplicate *grouping*, not deletion. |
| Local hardware/codec variability → slow or failed renders | Technical | Medium / Medium | FFmpeg capability checks; proxy first; VideoToolbox where available; perf spike **CP-3**; measured on the target Mac. |
| Centre-crop decapitates people at frame edges | Quality | Medium / Medium | Acceptable for M1 with a WO-104 stop-and-ask; saliency reframing deferred. |
| **Owner approval overestimates quality** (approving one's own work) | Delivery | High / High | ADR-006 binding: owner approval is a build gate, not evidence of quality. CP-1 + the deferred real-user gate are the mitigation; it stops being acceptable the moment anyone claims the product is good. |
| **Pre-value friction:** iPhone→Mac folder export + supplying a rights-cleared track before any result | Product | High / Medium | Tolerable for the owner (sole user); a real adoption tax later. Named now, not planned against; phone access deferred pending the capture-timestamp test (ES-001 §12). |
| Usage frequency too low to sustain a business | Commercial | **High / High** | 2–6 occasions/year → subscription retention implausible. One-time purchase or pay-per-render if evidence ever supports it; the engine is occasion-agnostic (birthdays, sports days, year-in-review). Deferred; build no variant before the wedge is evidenced. |
| Scope creep into a polished consumer editor too soon | Delivery | Medium / High | ADR-006/007 staged build; WO-100 is flow + data, and visual polish is an explicit stop-and-ask. |

## Privacy baseline

Originals processed locally and opened read-only; derivatives written to a separate directory; no automatic upload, publish, or delete; only consented owner media in any local test (ADR-002; owner-only real thumbnails under ADR-013). This is a design constraint, not a claim of production compliance.
