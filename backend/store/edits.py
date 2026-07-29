"""WO-118 · The controls that write state — `SPEC.md` §4.3 and §4.5.

Pure functions over a `Project`: each takes one and returns a **deep copy** with
the edit applied, leaving the caller to `FileProjectStore.save` it. They live
beside `derive.py` because most of them need the derivation to know what they
are changing — binning cannot stash "the previous effective value" without
first computing it.

Two jobs, both of them named in ADP-002 §4:

- **§4.3's controls** — bin and restore, the pair that makes removal genuinely
  non-destructive, plus the hand edits that set `origin.* = "user"` and with it
  the stickiness of §4.4.
- **§4.5's disposition writers.** `disposition` was retained against the v3z
  draft (DECISIONS A-3) because it is the only thing that measures whether the
  assists earn their place. A field with no writer measures nothing, so the
  writers are part of the contract.

## `dismissed` is not written here, deliberately

§4.5's four values have three writers after `pending`. **Two are implemented:**
`adjusted` (a handle moved) and `accepted` (at export). The third —
`dismissed`, written by reject (✕) — is **not**, because §4.3 and §3.1 cannot
both be satisfied as written and choosing between them is a product decision:

    §4.3  "Reject (✕) discards this clip's proposal — disposition: 'dismissed'.
           The clip reverts to whole (or to the user's own trim, if there is one)."
    §3.1   if project.trim_assist_on and clip.proposals.segments:
               return the proposal's value

A *retained* proposal marked `dismissed` still satisfies §3.1's second line, so
the clip does **not** revert to whole. At least three readings close the gap —
null the proposal (losing the very count A-3 kept `disposition` for), have the
derivation skip dismissed proposals (an amendment to a frozen §3.1), or have
reject write the whole clip as a user segment (locking the assist out of that
clip for good) — and they differ in what C-03 can later measure. Raised as a
stop-and-ask rather than guessed; see `handoff.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.contracts.models import AudioSettings, Clip, Project, Segment, SpeedRange
from backend.store.derive import effective_trim, whole_clip
from backend.store.project_store import StoreError


class EditError(StoreError):
    """A control was applied to a clip that cannot accept it."""


def _copy_with_clip(project: Project, source_id: str) -> tuple[Project, Clip]:
    out = project.model_copy(deep=True)
    for clip in out.clips:
        if clip.source_id == source_id:
            return out, clip
    raise EditError(f"no clip for source_id {source_id!r}")


def _mark_adjusted(clip: Clip, field: str) -> None:
    """§4.5: the user moved a handle on a clip carrying a proposal.

    Written whatever the proposal said before — the user has adjusted it now,
    and that is the truthful record. The proposal itself is **retained** (§3.1),
    which is what keeps reverting the toggle lossless.
    """
    proposal = getattr(clip.proposals, field)
    if proposal is not None:
        proposal.disposition = "adjusted"


# --- hand edits · the origin writers --------------------------------------

def set_user_segment(project: Project, source_id: str, segment: Segment) -> Project:
    """The user moves a trim handle. §3.1, §4.4, §4.5.

    From here on `origin.segments == "user"` and no assist can reach the field —
    not because anything checks, but because `derive.effective_trim` stops
    looking at the proposal.
    """
    out, clip = _copy_with_clip(project, source_id)
    clip.segment = segment
    clip.origin.segments = "user"
    _mark_adjusted(clip, "segments")
    return out


def set_user_speed_ranges(
    project: Project, source_id: str, ranges: list[SpeedRange]
) -> Project:
    """The user sets ramps by hand, in **source time** (§3.2).

    An empty list is a real edit, not a no-op: it means *I removed the assist's
    ramps*, and `origin.speed == "user"` keeps them removed.
    """
    out, clip = _copy_with_clip(project, source_id)
    clip.speed_ranges = list(ranges)
    clip.origin.speed = "user"
    _mark_adjusted(clip, "speed")
    return out


def set_user_audio(
    project: Project,
    source_id: str,
    *,
    retain: bool | None = None,
    gain_db: float | None = None,
) -> Project:
    """The row's mute switch and its gain (§5). No assist proposes either."""
    out, clip = _copy_with_clip(project, source_id)
    clip.audio = AudioSettings(
        retain=clip.audio.retain if retain is None else retain,
        gain_db=clip.audio.gain_db if gain_db is None else gain_db,
    )
    clip.origin.audio = "user"
    return out


def set_clip_order(project: Project, ordering: list[str]) -> Project:
    """Reorder the reel. `ordering` is every clip's `source_id`, in the new order.

    Only the clips that actually moved take `origin.order = "user"` — a
    reordering that leaves a clip where it was has not been an edit to it.
    """
    out = project.model_copy(deep=True)
    if sorted(ordering) != sorted(c.source_id for c in out.clips):
        raise EditError("ordering must name every clip exactly once")
    positions = {source_id: i + 1 for i, source_id in enumerate(ordering)}
    for clip in out.clips:
        new_order = positions[clip.source_id]
        if new_order != clip.order:
            clip.order = new_order
            clip.origin.order = "user"
    return out


# --- §4.3 · bin and restore ------------------------------------------------

def bin_clip(project: Project, source_id: str) -> Project:
    """Remove a clip from the reel by trimming it to nothing (§3.4, §4.3).

    **The previous effective value is stashed first** — that is the only reason
    `stashed_segment` exists and what makes removal reversible. `origin.segments`
    becomes `"user"` because it has to: with the trim assist on, a clip still
    marked `"proposed"` would derive the proposal straight back and the bin
    would not take.
    """
    out, clip = _copy_with_clip(project, source_id)
    if clip.stashed_segment is not None:
        raise EditError(f"clip {source_id!r} is already binned; restore it instead")
    clip.stashed_segment = effective_trim(project, clip)
    clip.segment = Segment(in_s=0.0, out_s=0.0)   # out_s <= in_s: out of the reel
    clip.origin.segments = "user"
    return out


def restore_clip(project: Project, source_id: str) -> Project:
    """Press bin again: put the stash back (§4.3).

    **The clip goes back to who owned it**, not just to the value it held. If
    the stash is one of the values the derivation itself can produce for this
    clip — the assist's proposal, or the whole clip — the user segment is
    dropped and ownership returns to the derivation. Writing the stash back as a
    user segment in that case would restore the picture while silently locking
    the trim assist out of that clip for good, which is not the "genuinely
    non-destructive" removal §4.3 describes.

    The test is against the derivation's *candidates* rather than against what
    it would return right now, so that toggling the assist between binning and
    restoring does not change who ends up owning the field.

    The one case this cannot tell apart: a user whose own trim happened to equal
    a derived value exactly. It returns to derived ownership. Distinguishing it
    would need the prior origin stored, and §3 is frozen.
    """
    out, clip = _copy_with_clip(project, source_id)
    stash = clip.stashed_segment
    if stash is None:
        raise EditError(f"clip {source_id!r} has nothing stashed")

    proposal = clip.proposals.segments
    derived_candidates = [whole_clip(out, clip)]
    if proposal is not None:
        derived_candidates.append(proposal.value)

    if any(stash == candidate for candidate in derived_candidates):
        clip.segment = None
        clip.origin.segments = "proposed" if proposal is not None else "default"
    else:
        clip.segment = stash
        clip.origin.segments = "user"
    clip.stashed_segment = None
    return out


def toggle_bin(project: Project, source_id: str) -> Project:
    """The bin key itself: one control, two directions (§4.3, v3z's row strip)."""
    _, clip = _copy_with_clip(project, source_id)
    if clip.stashed_segment is not None:
        return restore_clip(project, source_id)
    return bin_clip(project, source_id)


# --- §4.5 · the export writer ---------------------------------------------

@dataclass(frozen=True)
class AcceptanceSummary:
    """What `mark_proposals_accepted` did, for §4.5's one Log line.

    *"Kept 14 of 19 AI trims."* — the instrument for evidence claim **C-03**,
    and the reason `disposition` survived the v3z draft at all (A-3b).
    """

    trims_total: int
    trims_kept: int
    speeds_total: int
    speeds_kept: int

    def trim_line(self) -> str:
        return f"Kept {self.trims_kept} of {self.trims_total} AI trims."

    def speed_line(self) -> str:
        return f"Kept {self.speeds_kept} of {self.speeds_total} AI speed ramps."


def mark_proposals_accepted(project: Project) -> tuple[Project, AcceptanceSummary]:
    """At export: every proposal not adjusted or dismissed becomes `accepted` (§4.5).

    Read literally, as written. One consequence worth knowing when reading the
    summary: a **binned** clip's untouched proposal still counts as accepted,
    because binning is §4.3's own control and not the handle move §4.5 names —
    so "kept" counts proposals the user did not overrule, not proposals that
    reached the export. Flagged in `handoff.md` as a bias in the C-03
    instrument, not corrected here.
    """
    out = project.model_copy(deep=True)
    counts = {"segments": [0, 0], "speed": [0, 0]}   # [total, kept]
    for clip in out.clips:
        for field in ("segments", "speed"):
            proposal = getattr(clip.proposals, field)
            if proposal is None:
                continue
            counts[field][0] += 1
            if proposal.disposition == "pending":
                proposal.disposition = "accepted"
            if proposal.disposition == "accepted":
                counts[field][1] += 1
    return out, AcceptanceSummary(
        trims_total=counts["segments"][0],
        trims_kept=counts["segments"][1],
        speeds_total=counts["speed"][0],
        speeds_kept=counts["speed"][1],
    )
