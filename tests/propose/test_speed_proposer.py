from backend.propose import SpeedRuleProposer
from tests.propose.test_proposer import _analysis, _source


def test_speed_proposes_long_dull_source_time_ranges_only() -> None:
    p = SpeedRuleProposer().propose_speed(_source(6.0), _analysis(6, motion=[.1, .1, .1, .6, .1, .1], audio=[.1, .1, .1, .6, .1, .1]))
    assert [(r.from_s, r.to_s) for r in p.value] == [(0.0, 3.0), (4.0, 6.0)]
    assert 1.5 <= p.value[0].rate <= 2.0


def test_speed_drops_short_dull_candidates() -> None:
    p = SpeedRuleProposer().propose_speed(_source(3.0), _analysis(3, motion=[.1, .6, .6], audio=[.1, .6, .6]))
    assert p.value == []
