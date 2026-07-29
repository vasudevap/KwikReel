"""WO-118 gates · the §3.1 derivation and §3.4's derived state.

This file carries the **structural** half of the §4.4 stickiness gate: an assist
cannot reach a user-owned field, not because a check refuses it but because the
derivation stops looking. It also carries the "toggle off restores exactly, hand
edits untouched" gate, which is the same property read from the other end.

The fixture is `tests/contracts/canonical_example.py`, whose four clips were
built to exercise exactly these cases — a proposal nobody has acted on (s1), a
hand edit over a retained proposal (s2), a binned clip (s3), and a damaged
source (s4).
"""

from __future__ import annotations

import pytest

from backend.contracts.models import Project, Segment, SpeedRange
from backend.store import (
    effective_speed,
    effective_trim,
    in_reel,
    out_reason,
    played_duration_s,
    reel_length_s,
    unlinked_source_ids,
    whole_clip,
)
from tests.contracts.canonical_example import build_example


def _clip(project: Project, source_id: str):
    return next(c for c in project.clips if c.source_id == source_id)


# --- §3.1 · effective_trim ------------------------------------------------

def test_the_proposal_renders_while_the_trim_assist_is_on() -> None:
    project = build_example()            # trim_assist_on=True
    s1 = _clip(project, "s1")
    assert s1.segment is None            # nothing was copied into the clip
    assert effective_trim(project, s1) == Segment(in_s=2.4, out_s=9.1)


def test_the_whole_clip_renders_with_the_assist_off() -> None:
    project = build_example()
    project.trim_assist_on = False
    assert effective_trim(project, _clip(project, "s1")) == Segment(in_s=0.0, out_s=12.4)


def test_a_clip_with_no_proposal_renders_whole() -> None:
    project = build_example()
    s4 = _clip(project, "s4")
    assert effective_trim(project, s4) == whole_clip(project, s4)


# --- §4.4 · stickiness, structurally --------------------------------------

def test_an_assist_cannot_reach_a_user_owned_trim() -> None:
    # s2 carries BOTH a hand trim and a retained proposal. The proposal is right
    # there and is never consulted — with the assist on or off.
    project = build_example()
    s2 = _clip(project, "s2")
    assert s2.proposals.segments is not None

    for toggle in (True, False):
        project.trim_assist_on = toggle
        assert effective_trim(project, s2) == Segment(in_s=1.5, out_s=16.0)


def test_an_assist_cannot_reach_user_owned_speed() -> None:
    project = build_example()
    s2 = _clip(project, "s2")
    assert s2.proposals.speed is not None

    for toggle in (True, False):
        project.speed_assist_on = toggle
        assert effective_speed(project, s2) == [SpeedRange(from_s=6.0, to_s=11.0, rate=1.75)]


def test_a_user_may_own_the_speed_field_with_no_ramps() -> None:
    # "I removed the assist's ramps by hand." The proposal stays retained and
    # stays unreachable, so turning the toggle on does not put them back.
    project = build_example()
    project.speed_assist_on = True
    s2 = _clip(project, "s2")
    s2.speed_ranges = []
    assert effective_speed(project, s2) == []


def test_turning_a_toggle_off_reverts_it_and_leaves_hand_edits_alone() -> None:
    # The ADP-002 §4 gate, stated as the spec states it: reverting an assist is
    # free and lossless because nothing was ever overwritten.
    project = build_example()
    project.trim_assist_on = True
    before = {c.source_id: c.model_copy(deep=True) for c in project.clips}

    proposed_on = effective_trim(project, _clip(project, "s1"))
    user_on = effective_trim(project, _clip(project, "s2"))

    project.trim_assist_on = False
    proposed_off = effective_trim(project, _clip(project, "s1"))
    user_off = effective_trim(project, _clip(project, "s2"))

    assert proposed_on == Segment(in_s=2.4, out_s=9.1)          # the assist's
    assert proposed_off == Segment(in_s=0.0, out_s=12.4)        # reverted to whole
    assert user_on == user_off == Segment(in_s=1.5, out_s=16.0)  # untouched

    # And no clip changed on the way through: the toggle is a derivation, not
    # an edit, so there is nothing to restore afterwards.
    assert {c.source_id: c for c in project.clips} == before


# --- §3.1 · effective_speed ----------------------------------------------

def test_speed_ranges_come_from_the_proposal_only_while_the_toggle_is_on() -> None:
    project = build_example()
    s2 = _clip(project, "s2")
    s2.speed_ranges = []
    s2.origin.speed = "proposed"            # the machine owns the field again

    project.speed_assist_on = False
    assert effective_speed(project, s2) == []

    project.speed_assist_on = True
    assert effective_speed(project, s2) == [SpeedRange(from_s=5.5, to_s=12.0, rate=1.6)]


def test_no_proposal_and_no_user_ramps_is_1x_throughout() -> None:
    project = build_example()
    project.speed_assist_on = True
    assert effective_speed(project, _clip(project, "s1")) == []


# --- §3.4 · membership, and why a clip is out -----------------------------

def test_out_of_reel_is_derived_from_the_trim_alone() -> None:
    project = build_example()
    assert out_reason(project, _clip(project, "s3")) == "trimmed"
    assert not in_reel(project, _clip(project, "s3"))
    assert in_reel(project, _clip(project, "s1"))


def test_a_damaged_source_is_out_for_a_different_reason() -> None:
    project = build_example()
    assert out_reason(project, _clip(project, "s4")) == "damaged"


def test_the_three_reasons_keep_their_precedence() -> None:
    # §3.4 lists them in order: trimmed out, then unlinked, then damaged. A clip
    # can be more than one at once and the row reports the first.
    project = build_example()
    assert out_reason(project, _clip(project, "s1"), frozenset({"s1"})) == "unlinked"
    assert out_reason(project, _clip(project, "s3"), frozenset({"s3"})) == "trimmed"
    assert out_reason(project, _clip(project, "s4"), frozenset({"s4"})) == "unlinked"


def test_dragging_the_handle_back_revives_a_trimmed_out_clip() -> None:
    # Removal needs no state of its own, which is why this costs nothing.
    project = build_example()
    s3 = _clip(project, "s3")
    s3.segment = Segment(in_s=0.0, out_s=8.0)
    assert in_reel(project, s3)
    assert out_reason(project, s3) is None


def test_unlinked_is_read_from_the_filesystem(tmp_path) -> None:
    project = build_example()
    present = tmp_path / "IMG_0001.mov"
    present.write_bytes(b"")
    project.sources[0].path = str(present)

    unlinked = unlinked_source_ids(project)
    assert "s1" not in unlinked                  # the file is where the index says
    assert {"s2", "s3", "s4"} <= unlinked        # the fixture's paths are fictional


# --- §3.4 · played duration and reel length -------------------------------

def test_played_duration_of_an_unramped_clip_is_its_kept_time() -> None:
    project = build_example()
    assert played_duration_s(project, _clip(project, "s1")) == pytest.approx(6.7)


def test_played_duration_divides_the_ramped_overlap_by_its_rate() -> None:
    # s2 keeps 1.5..16.0 (14.5 s) with a 5.0 s ramp at 1.75x inside it.
    project = build_example()
    assert played_duration_s(project, _clip(project, "s2")) == pytest.approx(5.0 / 1.75 + 9.5)


def test_a_ramp_is_clipped_to_the_kept_region() -> None:
    # Ranges are stored in SOURCE time (§3.2), so a trim handle can leave part
    # of a ramp outside the kept region. Only the overlap counts.
    project = build_example()
    s2 = _clip(project, "s2")
    s2.segment = Segment(in_s=5.0, out_s=10.0)
    s2.speed_ranges = [SpeedRange(from_s=8.0, to_s=14.0, rate=2.0)]
    assert played_duration_s(project, s2) == pytest.approx(2.0 / 2.0 + 3.0)

    s2.speed_ranges = [SpeedRange(from_s=12.0, to_s=14.0, rate=2.0)]   # wholly outside
    assert played_duration_s(project, s2) == pytest.approx(5.0)


def test_a_clip_trimmed_to_nothing_plays_for_no_time() -> None:
    project = build_example()
    assert played_duration_s(project, _clip(project, "s3")) == 0.0


def test_reel_length_sums_the_in_reel_clips_only() -> None:
    # s3 is trimmed out and s4 is damaged, so the reel is s1 + s2.
    project = build_example()
    expected = 6.7 + (5.0 / 1.75 + 9.5)
    assert reel_length_s(project) == pytest.approx(expected)


def test_reel_length_drops_a_clip_whose_file_has_gone() -> None:
    project = build_example()
    assert reel_length_s(project, frozenset({"s2"})) == pytest.approx(6.7)
