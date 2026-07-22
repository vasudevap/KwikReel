# AI Vacation Reel Agent

An **explainable, local-first assisted first-draft editor** for private family footage. It turns one day of vacation clips into a single defensible draft Reel plus an honest account of what it chose, what it rejected, and why — for a human to accept, correct, or throw away.

Not an autonomous editor. The system proposes; a person decides.

## Status

**Stage A — Direction.** Documents only: no code, no test corpus, no experiments, no accepted decisions. See [handoff.md](handoff.md) for the precise state and the owner actions required to move.

The next gate is owner approval of `PROJECT.md`, `ROADMAP.md`, ADR-001 through ADR-004, and the validation plan with its pre-registered thresholds.

## Thesis

Strong AI products are **governed systems**: deterministic where possible, probabilistic where useful, measurable throughout, privacy-aware by default, reversible in their actions, and human-approved at consequential points.

Roughly 60% of this pipeline is well-understood computer vision and signal processing and should be boring and bulletproof. The interesting question is whether model-based judgment earns its place on top of that floor — which is what the validation phase exists to answer, before anything is built around the assumption that it does.

## Method

This project follows the [AI-Parallel Delivery Playbook](../_oversight/DELIVERY-PLAYBOOK.md). Validation precedes specification: the pivotal experiment runs before the product is specified, and the project carries **pre-committed kill criteria** that can end it on evidence.

## Documents

**Direction (Stage A)**
- [PROJECT.md](PROJECT.md) — framing, primary user, success measures, kill criteria
- [ROADMAP.md](ROADMAP.md) — phases, gates, and the continue/revise/stop decision at each
- [ADR-001](docs/decisions/ADR-001-prototype-shape.md) — local CLI pipeline first
- [ADR-002](docs/decisions/ADR-002-privacy-and-data-posture.md) — privacy and data posture *(blocks corpus collection)*
- [ADR-003](docs/decisions/ADR-003-music-and-licensing-posture.md) — music and licensing
- [ADR-004](docs/decisions/ADR-004-validation-first-sequencing.md) — validation-first sequencing and kill criteria

**Validation (Stage B)**
- [VALIDATION-PLAN.md](docs/specs/VALIDATION-PLAN.md) — hypotheses ordered pivotal-first, with pre-registered thresholds
- [EVIDENCE-LEDGER.md](docs/specs/EVIDENCE-LEDGER.md) — what is measured vs. assumed *(currently: everything is assumed)*
- [sample-media-test-strategy.md](docs/specs/sample-media-test-strategy.md) — corpus and evaluation protocol

**Supporting**
- [prototype-definition.md](docs/specs/prototype-definition.md) — POC shape and technology assessment
- [competitive-landscape.md](docs/research/competitive-landscape.md) — incumbents and the absorption risk
- [risk-register.md](docs/research/risk-register.md) — technical, privacy, quality, licensing, and commercial risks
- [phase-1-backlog.md](docs/work-orders/phase-1-backlog.md) — validation apparatus backlog *(not yet approved Work Orders)*

**Systems view — forward-looking projection** *(not accepted; the Atlas dock is deferred by ADR-001 and is a Phase 5 decision)*
- [SYSTEM-VISION.md](docs/vision/SYSTEM-VISION.md) — the two components, their capabilities, and the linkage contract
- [INTEGRATION-PLAN.md](docs/vision/INTEGRATION-PLAN.md) — where the Atlas dock sits in the roadmap, and the open decisions before it
- [reel-atlas-overview.html](docs/vision/reel-atlas-overview.html) — human-friendly visual overview *(open in a browser)*
- [reel-agent-ui-mockup.html](docs/vision/reel-agent-ui-mockup.html) — agent-side UI mockup: the authorized CLI today + a projected review app *(open in a browser)*

## Commercial posture

Conditional and deferred. This is a validation and portfolio project first. Auto-assembly and beat sync are already commodity — Apple, Google, CapCut, and Quik all ship it free. Productization requires evidence of editorial quality, user acceptance, willingness to pay, and continued differentiation from platform incumbents. None of that evidence exists yet.
