"""WO-118 · The derivations — `SPEC.md` §3.1 and §3.4. Nothing here is stored.

This module is the load-bearing half of schema v2. §3.1 says the assists do not
mutate clips: `clip.segment` and `clip.speed_ranges` hold **the user's** value,
and what actually renders is worked out at render time from the user's value,
the retained proposal, and the assist toggle. Every consumer — renderer, QA,
reel clock, Log — must ask this module rather than read `clip.segment`.

Three consequences follow, and they are why this file exists rather than the
logic being inlined where it is needed:

1. **Reverting an assist is lossless** because nothing was ever overwritten.
2. **Stickiness is structural** (§4.4): once `origin.segments == "user"` the
   derivation stops looking at proposals, so an assist *cannot* reach the field.
   That is a property of these functions, not of a check someone remembered to
   write, which is why the §4.4 tests exercise the derivation directly.
3. `clip.segment` is **not** "what renders". Reading it as if it were is the
   single most likely v1 habit to carry into v2 code.

`effective_trim` and `effective_speed` are transcribed from `SPEC.md` §3.1
line for line. **They are deliberately not clever** — if a case feels missing,
the spec is what changes, not this file. The one explicit exception is a trim
proposal the user rejected: it remains in state for the audit trail, but it is
not an effective value (DECISIONS §4, 2026-07-30).

## The two field invariants these rely on

`SPEC.md` §3.2 annotates the fields: `segment` is "the USER's trim; null unless
`origin.segments == "user"`" and `speed_ranges` is "the USER's ramps; empty
unless `origin.speed == "user"`". `project_store` enforces both, which is what
makes the derivation total — there is no undefined fourth case to guess at.

Note the asymmetry, which is real and not an oversight: a user may hold
`origin.speed == "user"` with **no** ramps (they removed the assist's ramps by
hand, and no assist may put them back), but there is no control that leaves a
user-owned clip with a null `segment` — binning writes a zero-length one.
"""

from __future__ import annotations

import os
from typing import Literal, Optional

from backend.contracts.models import Clip, Project, Segment, SourceIndex, SpeedRange

# §3.4's three reasons a clip is out of the reel, **in precedence order**. The
# index draws each in its own colour — amber, yellow, red — because they are
# fixed three completely different ways.
OutReason = Literal["trimmed", "unlinked", "damaged"]

_OUT_PRECEDENCE: tuple[OutReason, ...] = ("trimmed", "unlinked", "damaged")


def source_for(project: Project, clip: Clip) -> SourceIndex:
    """The `SourceIndex` behind a clip. `project_store` guarantees one exists."""
    for source in project.sources:
        if source.source_id == clip.source_id:
            return source
    raise KeyError(f"clip references unknown source_id {clip.source_id!r}")


def whole_clip(project: Project, clip: Clip) -> Segment:
    """§3.1's fallback: `0 .. duration_s`."""
    return Segment(in_s=0.0, out_s=source_for(project, clip).duration_s)


# --- §3.1 · the derivation, verbatim --------------------------------------

def effective_trim(project: Project, clip: Clip) -> Segment:
    """What actually renders for this clip. `SPEC.md` §3.1.

        if clip.origin.segments == "user":  return clip.segment
        if project.trim_assist_on and clip.proposals.segments and
           clip.proposals.segments.disposition != "dismissed":
                                            return the proposal's value
        return whole clip
    """
    if clip.origin.segments == "user" and clip.segment is not None:
        return clip.segment                                   # yours always wins
    if (
        project.trim_assist_on
        and clip.proposals.segments is not None
        and clip.proposals.segments.disposition != "dismissed"
    ):
        return clip.proposals.segments.value
    return whole_clip(project, clip)


def effective_speed(project: Project, clip: Clip) -> list[SpeedRange]:
    """The ramps that actually render, in **source time**. `SPEC.md` §3.1.

        if clip.origin.speed == "user":     return clip.speed_ranges
        if project.speed_assist_on and clip.proposals.speed:
                                            return the proposal's value
        return []                                              # 1.0x throughout
    """
    if clip.origin.speed == "user":
        return list(clip.speed_ranges)
    if project.speed_assist_on and clip.proposals.speed is not None:
        return list(clip.proposals.speed.value)
    return []


# --- §3.4 · derived state, never stored -----------------------------------

def unlinked_source_ids(project: Project) -> frozenset[str]:
    """Sources whose file is not where the index says it is (§3.4, §8.3).

    Read-only: `os.path.exists` and nothing more. Callers that already know the
    link state — the API after a relink sweep, a test — pass it to the functions
    below instead of paying for a stat per clip.
    """
    return frozenset(s.source_id for s in project.sources if not os.path.exists(s.path))


def out_reason(
    project: Project,
    clip: Clip,
    unlinked: frozenset[str] = frozenset(),
) -> Optional[OutReason]:
    """Why this clip is out of the reel, or `None` when it is in.

    §3.4's precedence, in its order: **trimmed out** (`out_s <= in_s`) beats
    **unlinked** beats **damaged** (`readable: false`). A clip can be more than
    one at once; the row reports the first.
    """
    trim = effective_trim(project, clip)
    reasons: dict[OutReason, bool] = {
        "trimmed": trim.out_s <= trim.in_s,
        "unlinked": clip.source_id in unlinked,
        "damaged": not source_for(project, clip).readable,
    }
    for reason in _OUT_PRECEDENCE:
        if reasons[reason]:
            return reason
    return None


def in_reel(project: Project, clip: Clip, unlinked: frozenset[str] = frozenset()) -> bool:
    """§3.4. There is no `included` field — membership is derived, always."""
    return out_reason(project, clip, unlinked) is None


def played_duration_s(project: Project, clip: Clip) -> float:
    """§3.4: `Σ (overlap with a ramp) / rate + (kept time under no ramp)`.

    Ranges are stored in source time and **clipped to the kept region here**,
    which is the same arithmetic WO-121 renders against and WO-122 checks the
    output length with. A clip that is out of the reel still has a played
    duration of 0.0 because its kept region is empty; `reel_length_s` skips it
    for the unlinked and damaged cases, where the kept region is not.
    """
    trim = effective_trim(project, clip)
    kept = max(0.0, trim.out_s - trim.in_s)
    if kept == 0.0:
        return 0.0

    ramped = 0.0
    played = 0.0
    for rng in effective_speed(project, clip):
        overlap = min(rng.to_s, trim.out_s) - max(rng.from_s, trim.in_s)
        if overlap <= 0.0:
            continue                      # the ramp is outside the kept region
        ramped += overlap
        played += overlap / rng.rate
    return played + (kept - ramped)


def reel_length_s(project: Project, unlinked: frozenset[str] = frozenset()) -> float:
    """§3.4: played duration summed over in-reel clips, in `order`.

    This is the number the user reads (§2.4) as well as the one QA checks the
    export against (§9), which is why WO-121 clamps each ramped clip to
    `-t (kept_duration / rate)`: the two must be the same number.
    """
    return sum(
        played_duration_s(project, clip)
        for clip in sorted(project.clips, key=lambda c: c.order)
        if in_reel(project, clip, unlinked)
    )
