import pytest

from backend.propose import SpeedRuleProposer
from backend.propose.speed_proposer import _merge_candidate_spans
from backend.store import effective_speed, set_user_segment
from backend.contracts.models import Segment
from tests.contracts.canonical_example import build_example
from tests.propose.test_proposer import _analysis, _source


def test_speed_proposes_long_dull_source_time_ranges_only() -> None:
    p = SpeedRuleProposer().propose_speed(_source(6.0), _analysis(6, motion=[.1, .1, .1, .6, .1, .1], audio=[.1, .1, .1, .6, .1, .1]))
    assert [(r.from_s, r.to_s) for r in p.value] == [(0.0, 3.0), (4.0, 6.0)]
    assert p.value[0].rate == pytest.approx(1.8)
    assert p.reasons[0].evidence_refs == ["signals.motion_energy[0:3]", "signals.audio_rms[0:3]"]


def test_speed_drops_short_dull_candidates() -> None:
    p = SpeedRuleProposer().propose_speed(_source(3.0), _analysis(3, motion=[.1, .6, .6], audio=[.1, .6, .6]))
    assert p.value == []


def test_speed_accepts_the_exact_threshold_and_one_point_five_second_floor() -> None:
    p = SpeedRuleProposer().propose_speed(
        _source(1.5), _analysis(2, motion=[.25, .25], audio=[.25, .25])
    )
    assert [(item.from_s, item.to_s, item.rate) for item in p.value] == [
        (0.0, 1.5, 1.5)
    ]


def test_speed_proposals_are_deterministic_except_for_the_timestamp() -> None:
    analysis = _analysis(3, motion=[.0, .1, .2], audio=[.0, .1, .2])
    first = SpeedRuleProposer().propose_speed(_source(3.0), analysis)
    second = SpeedRuleProposer().propose_speed(_source(3.0), analysis)
    assert first.value == second.value
    assert first.reasons == second.reasons
    assert first.disposition == second.disposition == "pending"


def test_under_half_second_candidate_gaps_merge() -> None:
    assert _merge_candidate_spans([(0.0, 2.0), (2.4, 4.0)]) == [(0.0, 4.0)]
    assert _merge_candidate_spans([(0.0, 2.0), (2.5, 4.0)]) == [(0.0, 2.0), (2.5, 4.0)]


def test_proposed_ranges_remain_in_source_time_after_a_trim_handle_move() -> None:
    proposal = SpeedRuleProposer().propose_speed(
        _source(6.0), _analysis(6, motion=[.1, .1, .6, .6, .6, .6], audio=[.1, .1, .6, .6, .6, .6])
    )
    project = build_example()
    clip = next(item for item in project.clips if item.source_id == "s1")
    clip.proposals.speed = proposal
    clip.origin.speed = "proposed"
    project.speed_assist_on = True

    before = effective_speed(project, clip)
    edited = set_user_segment(project, "s1", Segment(in_s=1.0, out_s=4.0))
    after = effective_speed(edited, next(item for item in edited.clips if item.source_id == "s1"))
    assert [(item.from_s, item.to_s) for item in before] == [(0.0, 2.0)]
    assert after == before
