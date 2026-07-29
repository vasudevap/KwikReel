"""WO-111 gates (synthetic) · signals are normalised and plausible, and the
analyze→propose pair produces an explained result end to end."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.analysis import FileAnalysisStore, OpenCVAnalysis
from backend.ingest import FFmpegIngest
from backend.propose import TrimRuleProposer
from tests.synthetic import ffmpeg_available, make_black_clip, make_corpus

pytestmark = pytest.mark.skipif(
    not ffmpeg_available(), reason="ffmpeg/ffprobe not installed (ES-001 §3)"
)

_ING = FFmpegIngest(proxy_root="/unused")


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> dict[str, Path]:
    return make_corpus(tmp_path_factory.mktemp("media"))


def _signals_are_normalised(sig) -> None:
    for arr in (sig.blur, sig.exposure, sig.shake, sig.motion_energy, sig.audio_rms):
        assert all(0.0 <= v <= 1.0 for v in arr)


def test_analyze_produces_normalised_per_second_signals(corpus) -> None:
    src = _ING.probe_clip(str(corpus["portrait_audio"]))
    analysis = OpenCVAnalysis().analyze(src)
    n = round(src.duration_s)
    assert len(analysis.signals.blur) == n
    _signals_are_normalised(analysis.signals)
    assert sum(analysis.signals.audio_rms) > 0  # this clip has audio


def test_silent_source_has_zero_audio_rms(corpus) -> None:
    src = _ING.probe_clip(str(corpus["landscape_silent"]))
    analysis = OpenCVAnalysis().analyze(src)
    assert all(v == 0.0 for v in analysis.signals.audio_rms)


def test_black_clip_reads_as_dark_and_unsharp(tmp_path) -> None:
    black = make_black_clip(tmp_path / "black.mp4", duration=2)
    src = _ING.probe_clip(str(black))
    sig = OpenCVAnalysis().analyze(src).signals
    assert sum(sig.exposure) / len(sig.exposure) > 0.5   # heavily clipped (dark)
    assert sum(sig.blur) / len(sig.blur) < 0.35          # below the sharpness floor


def test_landscape_through_a_real_proxy_is_not_reported_overexposed(corpus, tmp_path) -> None:
    """WO-116 regression.

    `make_proxy` letterboxes every orientation into 540×960, so a 16:9 clip is
    ~0.68 black bar by area. Exposure is the fraction of clipped pixels and bars
    are 0, so measured naively the clip clears the 0.50 ceiling on *every*
    second and comes back OVEREXPOSED before any content is considered.

    No other test in the suite builds a proxy — they all call `probe_clip`,
    which leaves `proxy_path` None, so analysis reads the original and the
    padded path is never exercised. The one exposure assertion that exists uses
    a black *portrait* clip, which letterboxes to nothing.
    """
    ing = FFmpegIngest(proxy_root=tmp_path / "proxies")
    src = ing.probe_clip(str(corpus["landscape_silent"]))
    src.proxy_path = ing.make_proxy(src)

    analysis = OpenCVAnalysis().analyze(src)
    assert max(analysis.signals.exposure) < 0.5, "letterbox bars counted as clipped content"

    proposal = TrimRuleProposer().propose_trim(src, analysis)
    assert not any(r.code == "OVEREXPOSED" for r in proposal.reasons)


def test_proxy_and_original_agree_on_exposure(corpus, tmp_path) -> None:
    """The proxy is a speed optimisation, not a different measurement — the same
    landscape clip must read the same either way."""
    ing = FFmpegIngest(proxy_root=tmp_path / "proxies")
    src = ing.probe_clip(str(corpus["landscape_silent"]))
    from_original = OpenCVAnalysis().analyze(src).signals.exposure

    src.proxy_path = ing.make_proxy(src)
    from_proxy = OpenCVAnalysis().analyze(src).signals.exposure

    for a, b in zip(from_original, from_proxy):
        assert abs(a - b) < 0.10, f"proxy {b:.3f} vs original {a:.3f}"


def test_analysis_store_round_trip(corpus, tmp_path) -> None:
    src = _ING.probe_clip(str(corpus["portrait_audio"]))
    analysis = OpenCVAnalysis().analyze(src)
    store = FileAnalysisStore(tmp_path / "analysis")
    store.save("proj", analysis)
    assert store.exists("proj", src.source_id)
    assert store.load("proj", src.source_id) == analysis


def test_analyze_then_propose_black_clip_keeps_whole_and_says_why(tmp_path) -> None:
    black = make_black_clip(tmp_path / "black.mp4", duration=2)
    src = _ING.probe_clip(str(black))
    analysis = OpenCVAnalysis().analyze(src)
    proposal = TrimRuleProposer().propose_trim(src, analysis)
    assert proposal.disposition == "pending"
    assert proposal.reasons[0].code == "NO_CLEAR_WINDOW"  # nothing cleared the floors
    assert proposal.value[0].in_s == 0.0  # whole clip kept


def test_analyze_then_propose_good_clip_is_explained(corpus) -> None:
    src = _ING.probe_clip(str(corpus["portrait_audio"]))
    analysis = OpenCVAnalysis().analyze(src)
    proposal = TrimRuleProposer().propose_trim(src, analysis)
    assert proposal.disposition == "pending"
    assert proposal.value[0].out_s > proposal.value[0].in_s
    assert proposal.reasons and all(r.human_text and r.evidence_refs for r in proposal.reasons)
