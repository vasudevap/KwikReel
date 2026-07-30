"""WO-118 gates · §4.3's controls and §4.5's disposition writers.

The ADP-002 §4 gate this file carries is **bin -> restore exact**. "Exact" is
read as the spec describes the control — *genuinely non-destructive* — so it
covers who owns the field afterwards, not only what value it holds. A restore
that gave the picture back but left the trim assist permanently locked out of
that clip would pass a value-only test and fail the sentence it comes from.
"""

from __future__ import annotations

import pytest

from backend.contracts.models import Project, Segment, SpeedRange
from backend.store import (
    EditError,
    FileProjectStore,
    bin_clip,
    effective_trim,
    in_reel,
    mark_proposals_accepted,
    reject_trim_proposal,
    restore_clip,
    set_clip_order,
    set_user_audio,
    set_user_segment,
    set_user_speed_ranges,
    toggle_bin,
)
from tests.contracts.canonical_example import build_example


def _clip(project: Project, source_id: str):
    return next(c for c in project.clips if c.source_id == source_id)


# --- the hand edits · §3.1, §4.4, §4.5 ------------------------------------

def test_a_hand_trim_takes_the_field_and_marks_the_proposal_adjusted() -> None:
    project = build_example()
    edited = set_user_segment(project, "s1", Segment(in_s=3.0, out_s=8.0))
    clip = _clip(edited, "s1")

    assert clip.segment == Segment(in_s=3.0, out_s=8.0)
    assert clip.origin.segments == "user"
    assert clip.proposals.segments.disposition == "adjusted"
    # Retained, not discarded — that is what keeps reverting the toggle lossless.
    assert clip.proposals.segments.value == Segment(in_s=2.4, out_s=9.1)
    assert effective_trim(edited, clip) == Segment(in_s=3.0, out_s=8.0)

    # Pure: the project handed in is untouched.
    assert _clip(project, "s1").segment is None


def test_reject_retains_the_proposal_but_reverts_the_effective_trim() -> None:
    project = build_example()
    rejected = reject_trim_proposal(project, "s1")
    clip = _clip(rejected, "s1")

    assert clip.proposals.segments is not None
    assert clip.proposals.segments.disposition == "dismissed"
    assert clip.origin.segments == "proposed"
    assert effective_trim(rejected, clip) == Segment(in_s=0.0, out_s=12.4)
    assert _clip(project, "s1").proposals.segments.disposition == "pending"


def test_reject_does_not_override_a_user_trim() -> None:
    project = build_example()
    rejected = reject_trim_proposal(project, "s2")
    clip = _clip(rejected, "s2")

    assert clip.proposals.segments is not None
    assert clip.proposals.segments.disposition == "dismissed"
    assert effective_trim(rejected, clip) == Segment(in_s=1.5, out_s=16.0)


def test_rejecting_without_a_trim_proposal_is_refused() -> None:
    with pytest.raises(EditError):
        reject_trim_proposal(build_example(), "s3")


def test_removing_every_ramp_by_hand_is_an_edit_not_a_no_op() -> None:
    project = build_example()
    project.speed_assist_on = True
    edited = set_user_speed_ranges(project, "s1", [])
    clip = _clip(edited, "s1")

    assert clip.speed_ranges == []
    assert clip.origin.speed == "user"       # and no assist may put them back


def test_a_hand_set_ramp_is_uncapped() -> None:
    # N-6: the assist never proposes above 2.0x; hand-set rates have no cap.
    project = build_example()
    edited = set_user_speed_ranges(project, "s1", [SpeedRange(from_s=1.0, to_s=4.0, rate=3.5)])
    assert _clip(edited, "s1").speed_ranges[0].rate == 3.5


def test_muting_a_row_takes_the_audio_field() -> None:
    project = build_example()
    edited = set_user_audio(project, "s1", retain=False)
    clip = _clip(edited, "s1")
    assert clip.audio.retain is False
    assert clip.audio.gain_db == 0.0          # untouched
    assert clip.origin.audio == "user"


def test_reordering_marks_only_the_clips_that_moved() -> None:
    project = build_example()
    reordered = set_clip_order(project, ["s2", "s1", "s3", "s4"])

    assert [(c.source_id, c.order) for c in reordered.clips] == [
        ("s1", 2), ("s2", 1), ("s3", 3), ("s4", 4)
    ]
    assert _clip(reordered, "s1").origin.order == "user"
    assert _clip(reordered, "s2").origin.order == "user"
    assert _clip(reordered, "s3").origin.order == "default"
    assert _clip(reordered, "s4").origin.order == "default"


def test_an_incomplete_ordering_is_refused() -> None:
    with pytest.raises(EditError):
        set_clip_order(build_example(), ["s2", "s1"])


# --- §4.3 · bin and restore -----------------------------------------------

def test_binning_stashes_the_effective_value_and_trims_to_nothing() -> None:
    project = build_example()            # trim_assist_on=True, so s1 derives its proposal
    binned = bin_clip(project, "s1")
    clip = _clip(binned, "s1")

    assert clip.stashed_segment == Segment(in_s=2.4, out_s=9.1)   # what was on screen
    assert clip.segment == Segment(in_s=0.0, out_s=0.0)
    assert clip.origin.segments == "user"
    assert not in_reel(binned, clip)


def test_bin_then_restore_returns_a_proposed_clip_to_the_assist() -> None:
    # The gate. s1's trim came from the assist, so after restore the assist must
    # still own it — value AND ownership back exactly where they were.
    project = build_example()
    before = _clip(project, "s1").model_copy(deep=True)

    restored = restore_clip(bin_clip(project, "s1"), "s1")
    clip = _clip(restored, "s1")

    assert clip == before
    assert clip.segment is None
    assert clip.stashed_segment is None
    assert clip.origin.segments == "proposed"
    assert effective_trim(restored, clip) == Segment(in_s=2.4, out_s=9.1)


def test_bin_then_restore_returns_a_hand_trimmed_clip_to_the_user() -> None:
    project = build_example()
    before = _clip(project, "s2").model_copy(deep=True)

    restored = restore_clip(bin_clip(project, "s2"), "s2")
    clip = _clip(restored, "s2")

    assert clip == before
    assert clip.segment == Segment(in_s=1.5, out_s=16.0)
    assert clip.origin.segments == "user"


def test_restore_returns_a_clip_that_had_no_trim_at_all_to_default() -> None:
    project = build_example()
    project.trim_assist_on = False
    before = _clip(project, "s4").model_copy(deep=True)

    restored = restore_clip(bin_clip(project, "s4"), "s4")
    assert _clip(restored, "s4") == before
    assert _clip(restored, "s4").origin.segments == "default"


def test_toggling_the_assist_between_bin_and_restore_does_not_change_ownership() -> None:
    # The stash was taken while the assist was on. Turning it off before
    # restoring must not convert the assist's trim into the user's.
    project = build_example()
    binned = bin_clip(project, "s1")
    binned.trim_assist_on = False

    restored = restore_clip(binned, "s1")
    clip = _clip(restored, "s1")
    assert clip.origin.segments == "proposed"
    assert effective_trim(restored, clip) == Segment(in_s=0.0, out_s=12.4)   # assist off

    restored.trim_assist_on = True
    assert effective_trim(restored, clip) == Segment(in_s=2.4, out_s=9.1)    # and back


def test_the_bin_key_is_one_control_in_two_directions() -> None:
    project = build_example()
    once = toggle_bin(project, "s1")
    assert not in_reel(once, _clip(once, "s1"))
    twice = toggle_bin(once, "s1")
    assert _clip(twice, "s1") == _clip(project, "s1")


def test_binning_twice_or_restoring_nothing_is_refused() -> None:
    project = build_example()
    with pytest.raises(EditError):
        bin_clip(project, "s3")          # already binned in the fixture
    with pytest.raises(EditError):
        restore_clip(project, "s1")      # nothing stashed
    with pytest.raises(EditError):
        bin_clip(project, "ghost")


def test_a_bin_and_a_restore_both_survive_a_save(tmp_path) -> None:
    # Every intermediate state has to satisfy the store's invariants, including
    # the §4.4 guard that sees restore hand `origin.segments` back to "proposed".
    store = FileProjectStore(tmp_path)
    saved = store.save(build_example())

    binned = store.save(bin_clip(saved, "s1"))
    assert not in_reel(binned, _clip(binned, "s1"))

    restored = store.save(restore_clip(binned, "s1"))
    reloaded = store.load(restored.project_id)
    assert _clip(reloaded, "s1").origin.segments == "proposed"
    assert _clip(reloaded, "s1").segment is None
    assert _clip(reloaded, "s1").stashed_segment is None


# --- §4.5 · the export writer ---------------------------------------------

def test_export_accepts_every_proposal_the_user_did_not_overrule() -> None:
    # The fixture: s1's trim is pending, s2's trim and speed were both adjusted.
    project = build_example()
    exported, summary = mark_proposals_accepted(project)

    assert _clip(exported, "s1").proposals.segments.disposition == "accepted"
    assert _clip(exported, "s2").proposals.segments.disposition == "adjusted"
    assert _clip(exported, "s2").proposals.speed.disposition == "adjusted"

    assert (summary.trims_total, summary.trims_kept) == (2, 1)
    assert (summary.speeds_total, summary.speeds_kept) == (1, 0)
    assert summary.trim_line() == "Kept 1 of 2 AI trims."
    assert summary.speed_line() == "Kept 0 of 1 AI speed ramps."


def test_export_is_idempotent_and_does_not_relitigate_a_disposition() -> None:
    project = build_example()
    once, first = mark_proposals_accepted(project)
    twice, second = mark_proposals_accepted(once)
    assert twice == once
    assert second == first


def test_a_clip_with_no_proposal_counts_for_nothing() -> None:
    # s3 and s4 carry none, so the denominator is proposals, not clips.
    project = build_example()
    _, summary = mark_proposals_accepted(project)
    assert summary.trims_total == 2 and len(project.clips) == 4
