"""WO-112 gates · the §5.2 trim rules and ADR-006 legibility, pinned with
hand-crafted analysis signals (deterministic, no media)."""

from __future__ import annotations

from backend.contracts.models import Analysis, Signals, SourceIndex
from backend.propose import TrimRuleProposer


def _analysis(n: int, *, blur=None, exposure=None, shake=None, motion=None, audio=None, cuts=None) -> Analysis:
    def fill(v, default):
        return list(v) if v is not None else [default] * n
    return Analysis(
        source_id="s",
        signals=Signals(
            blur=fill(blur, 1.0),            # sharp
            exposure=fill(exposure, 0.0),    # not clipped
            shake=fill(shake, 0.0),          # steady
            motion_energy=fill(motion, 0.5), # moving (not static)
            audio_rms=fill(audio, 0.5),      # has sound (not static)
        ),
        scene_cuts_s=list(cuts or []),
        dup_group=None,
        run_id="run",
    )


def _source(dur: float) -> SourceIndex:
    return SourceIndex(
        source_id="s", content_hash="h", path="/x.mov", duration_s=dur, captured_at=None,
        orientation="portrait", codec="h264", fps=30.0, width=1080, height=1920,
        has_audio=True, has_gps=False, readable=True, proxy_path=None,
    )


def _propose(dur, analysis):
    return TrimRuleProposer().propose_trim(_source(dur), analysis)


def test_trims_leading_blur_with_a_citing_reason() -> None:
    p = _propose(6.0, _analysis(6, blur=[0.1, 0.1, 1.0, 1.0, 1.0, 1.0]))
    seg = p.value[0]
    assert (seg.in_s, seg.out_s) == (2.0, 6.0)
    reason = next(r for r in p.reasons if r.code == "LEADING_BLUR")
    assert reason.evidence_refs == ["signals.blur[0:2]"]
    assert "blurry" in reason.human_text and "0.35 floor" in reason.human_text
    assert p.disposition == "pending"


def test_trims_trailing_shake() -> None:
    p = _propose(6.0, _analysis(6, shake=[0.0, 0.0, 0.0, 0.0, 0.9, 0.9]))
    seg = p.value[0]
    assert (seg.in_s, seg.out_s) == (0.0, 4.0)
    assert "TRAILING_SHAKE" in {r.code for r in p.reasons}


def test_full_clip_fallback_when_nothing_clears_floors() -> None:
    p = _propose(6.0, _analysis(6, blur=[0.1] * 6))
    seg = p.value[0]
    assert (seg.in_s, seg.out_s) == (0.0, 6.0)
    assert [r.code for r in p.reasons] == ["NO_CLEAR_WINDOW"]  # rule 5: kept and said so


def test_respects_the_one_second_floor() -> None:
    p = _propose(6.0, _analysis(6, blur=[0.1, 0.1, 0.1, 1.0, 0.1, 0.1]))  # one good second
    seg = p.value[0]
    assert seg.out_s - seg.in_s >= 1.0
    assert (seg.in_s, seg.out_s) == (3.0, 4.0)


def test_window_does_not_cross_a_scene_cut() -> None:
    # All seconds are good, but a cut at 3.0 s splits two shots; the best single
    # shot is proposed (rule 4), not a window spanning the cut.
    p = _propose(6.0, _analysis(6, cuts=[3.0]))
    seg = p.value[0]
    assert (seg.in_s, seg.out_s) == (0.0, 3.0)


def test_trims_leading_static_dead_air() -> None:
    p = _propose(6.0, _analysis(6, motion=[0.0, 0.0, 0.5, 0.5, 0.5, 0.5], audio=[0.0, 0.0, 0.5, 0.5, 0.5, 0.5]))
    seg = p.value[0]
    assert (seg.in_s, seg.out_s) == (2.0, 6.0)
    reason = next(r for r in p.reasons if r.code == "LEADING_STATIC")
    assert "signals.motion_energy[0:2]" in reason.evidence_refs
    assert "signals.audio_rms[0:2]" in reason.evidence_refs


def test_whole_clip_good_is_stated() -> None:
    p = _propose(6.0, _analysis(6))
    seg = p.value[0]
    assert (seg.in_s, seg.out_s) == (0.0, 6.0)
    assert [r.code for r in p.reasons] == ["WHOLE_CLIP_GOOD"]


def test_every_reason_is_legible() -> None:  # ADR-006
    # Multiple factors at once — every ReasonRecord must be human-readable and cite evidence.
    p = _propose(6.0, _analysis(6, blur=[0.1, 0.1, 1.0, 1.0, 1.0, 1.0], shake=[0.0, 0.0, 0.0, 0.0, 0.9, 0.9]))
    assert {"LEADING_BLUR", "TRAILING_SHAKE"} <= {r.code for r in p.reasons}
    for r in p.reasons:
        assert r.human_text.strip()
        assert r.evidence_refs and all(ev.startswith("signals.") for ev in r.evidence_refs)
        assert r.confidence in ("high", "med", "low")
