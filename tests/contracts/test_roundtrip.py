"""WO-117 gate · the SPEC.md §3.2 example validates and round-trips byte-equivalently.

`SPEC.md` §12 gate 10 ("save→reopen is byte-equivalent") proven here at the model
layer; WO-118 proves it again through the on-disk store.

The tests that matter most are the two structural ones at the bottom. §3.1 says
the assists do not mutate clips — proposals are retained and effective values are
derived — and §4.4 makes "an assist never touches a hand-edited field" a
correctness requirement rather than a behaviour. A contract that lost either
across a round trip would look fine and be broken.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from backend.contracts.models import Project, Segment
from tests.contracts.canonical_example import FIXTURE_PATH, build_example, canonical_json


def test_example_validates_and_carries_the_v2_shape() -> None:
    p = build_example()
    assert p.schema_version == 2
    assert p.name == "Beach Day"
    assert p.output_resolution == "1080p"

    # DECISIONS A-4: two levels, one file. Not three modes and a map.
    assert (p.audio.music_level, p.audio.clip_level) == (0.62, 0.78)
    assert p.export.last_render is not None
    assert p.export.last_render.path.endswith("beach-day.mp4")

    # A-1: the toggles are the control surface. There are no stage approvals to
    # read, and nothing here says which stage the project is "at".
    assert not hasattr(p, "stage_approvals")
    assert p.trim_assist_on is True and p.speed_assist_on is False

    # §3.4: membership is derived. No booleans exist to disagree with it.
    c1 = next(c for c in p.clips if c.source_id == "s1")
    assert not hasattr(c1, "included")
    assert not hasattr(c1, "deleted")


def test_the_four_ways_a_clip_relates_to_the_reel() -> None:
    """s1 proposed · s2 hand-edited · s3 binned · s4 damaged (SPEC.md §3.4)."""
    p = build_example()
    by_id = {c.source_id: c for c in p.clips}

    # s1 · a proposal the user has not acted on. The clip itself is untouched:
    # `segment` stays null and what renders is derived through the proposal.
    assert by_id["s1"].segment is None
    assert by_id["s1"].origin.segments == "proposed"
    assert by_id["s1"].proposals.segments is not None
    assert by_id["s1"].proposals.segments.disposition == "pending"

    # s3 · binned: zero-length effective trim, with the stash holding the return.
    s3 = by_id["s3"]
    assert s3.segment is not None and s3.segment.out_s <= s3.segment.in_s
    assert s3.stashed_segment == Segment(in_s=0.0, out_s=8.0)

    # s4 · damaged: out of the reel for a reason that lives on the SOURCE, not
    # the clip. The clip records nothing about it.
    s4_source = next(s for s in p.sources if s.source_id == "s4")
    assert s4_source.readable is False
    assert by_id["s4"].segment is None
    assert by_id["s4"].origin.segments == "default"


def test_a_hand_edit_is_recorded_where_the_assists_can_see_it() -> None:
    """§4.4 · stickiness is structural: `origin == "user"` is the whole mechanism."""
    c2 = next(c for c in build_example().clips if c.source_id == "s2")

    # The user's own values are present and their origins say so...
    assert c2.origin.segments == "user" and c2.segment is not None
    assert c2.origin.speed == "user" and c2.speed_ranges

    # ...and the proposals they overrode are RETAINED, which is what makes
    # switching a toggle off lossless (§3.1 consequence 1).
    assert c2.proposals.segments is not None
    assert c2.proposals.speed is not None
    assert c2.proposals.segments.disposition == "adjusted"

    # The retained proposal is genuinely different from the user's value — a
    # test that passed because they happened to be equal would prove nothing.
    assert c2.proposals.segments.value != c2.segment


def test_speed_ranges_are_stored_in_source_time() -> None:
    """§3.2 · a ramp describes content, so it must not be relative to the trim."""
    c2 = next(c for c in build_example().clips if c.source_id == "s2")
    ramp = c2.speed_ranges[0]
    assert c2.segment is not None
    # The ramp sits inside the kept region but is expressed from the CLIP's
    # start, not the segment's: 6.0 is absolute, not 6.0 past in_s (1.5).
    assert ramp.from_s >= c2.segment.in_s
    assert ramp.to_s <= c2.segment.out_s
    assert ramp.rate == 1.75  # hand-set and above nothing — N-6 removes the cap


def test_committed_fixture_is_byte_equivalent_to_the_model() -> None:
    # The fixture must be exactly what the model serialises; regenerate on drift:
    #   python -m tests.contracts.canonical_example
    assert FIXTURE_PATH.read_text(encoding="utf-8") == canonical_json()


def test_load_reopen_is_byte_equivalent() -> None:
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    loaded = Project.model_validate_json(text)
    redumped = loaded.model_dump_json(indent=2) + "\n"
    assert redumped == text
    # second round trip is a fixed point
    assert Project.model_validate_json(redumped).model_dump_json(indent=2) + "\n" == text


def test_origin_and_proposals_survive_a_round_trip() -> None:
    """The ADP-002 §4 gate, stated as its own test.

    Everything the human did, and everything the machine proposed, has to come
    back off disk exactly. If a proposal were dropped in serialisation the app
    would look correct until someone switched a toggle off and lost their edit.
    """
    original = build_example()
    reloaded = Project.model_validate_json(canonical_json())

    for a, b in zip(original.clips, reloaded.clips):
        assert a.origin == b.origin
        assert a.proposals == b.proposals
        assert a.segment == b.segment
        assert a.speed_ranges == b.speed_ranges
        assert a.stashed_segment == b.stashed_segment


def test_unknown_fields_are_rejected() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    data["surprise"] = 1
    with pytest.raises(ValidationError):
        Project.model_validate(data)


def test_a_v1_document_does_not_load_as_v2() -> None:
    """The version boundary is real, not decorative.

    v1 and v2 describe different products. A v1 document loading with its
    unknown fields quietly dropped would silently discard approvals and audio
    modes and present the result as a valid project.
    """
    v1 = {
        "schema_version": 1,
        "project_id": "6f9619ff-8b86-d011-b42d-00cf4fc964ff",
        "created_at": "2026-07-24T18:55:02Z",
        "updated_at": "2026-07-24T19:10:44Z",
        "app_version": "0.1.0",
        "media_root": "/Users/example/Movies/BeachDay",
        "target_duration_s": 75.0,
        "music": {"track_ref": "/t.m4a", "content_hash": "h", "duration_s": 1.0},
        "sources": [],
        "clips": [],
        "stage_approvals": {"ingest": "2026-07-24T19:02:11Z"},
        "export": {"audio_modes": ["music"], "last_render": {}},
    }
    with pytest.raises(ValidationError):
        Project.model_validate(v1)
