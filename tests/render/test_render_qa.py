"""WO-104 + WO-105 gates (synthetic) · render the three audio modes at
1080×1920 and prove the QA gate catches bad renders while passing good ones.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from backend.contracts.models import (
    Clip,
    Export,
    Music,
    Origin,
    Project,
    Proposals,
    Segment,
    SourceIndex,
    StageApprovals,
)
from backend.ingest import FFmpegIngest
from backend.qa import FFmpegOutputQA
from backend.render import FFmpegRenderer
from tests.synthetic import ffmpeg_available, make_black_clip, make_corpus, make_music

pytestmark = pytest.mark.skipif(
    not ffmpeg_available(), reason="ffmpeg/ffprobe not installed (ES-001 §3 dependency)"
)

_ING = FFmpegIngest(proxy_root="/unused")


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> dict[str, Path]:
    return make_corpus(tmp_path_factory.mktemp("media"))


@pytest.fixture(scope="module")
def music(tmp_path_factory) -> Path:
    return make_music(tmp_path_factory.mktemp("music") / "bed.m4a", duration=12)


def _project(sources: list[SourceIndex], music_path: Path, clip_len: float = 1.0) -> Project:
    clips = [
        Clip(
            source_id=s.source_id, included=True, order=i, deleted=False,
            segments=[Segment(in_s=0.0, out_s=clip_len, speed=[])],
            origin=Origin(), proposals=Proposals(),
        )
        for i, s in enumerate(sources, start=1)
    ]
    return Project(
        schema_version=1, project_id="render-test",
        created_at="2026-07-24T20:00:00Z", updated_at="2026-07-24T20:00:00Z",
        app_version="0.1.0", name="Render Test", media_root="/tmp/media", target_duration_s=75.0,
        music=Music(track_ref=str(music_path), content_hash="sha256:music", duration_s=12.0),
        sources=sources, clips=clips, stage_approvals=StageApprovals(),
        export=Export(audio_modes=["music", "clip", "silent"], last_render={}),
    )


def test_all_three_modes_render_1080x1920_and_pass_qa(corpus, music, tmp_path) -> None:
    # One clip with audio, one without — exercises the clip-mode silent pad.
    sources = [_ING.probe_clip(str(corpus["portrait_audio"])), _ING.probe_clip(str(corpus["landscape_silent"]))]
    project = _project(sources, music)
    renderer = FFmpegRenderer(output_root=tmp_path / "out")
    qa = FFmpegOutputQA()

    for mode in ("music", "clip", "silent"):
        record = renderer.export(project, mode)
        assert Path(record.path).exists()
        report = qa.validate_render(record.path, project, mode)
        assert report.passed, f"{mode}: {report.reasons}"
        assert (report.width, report.height) == (1080, 1920)
        assert abs(report.duration_s - 2.0) <= 0.5  # timeline sum = 2 × 1.0 s


def test_qa_catches_black_render(corpus, music, tmp_path) -> None:
    black = make_black_clip(tmp_path / "black.mp4")
    src = _ING.probe_clip(str(black))
    project = _project([src], music)
    record = FFmpegRenderer(output_root=tmp_path / "out").export(project, "silent")
    report = FFmpegOutputQA().validate_render(record.path, project, "silent")
    assert report.not_black is False
    assert report.passed is False
    assert any("black" in r for r in report.reasons)


def test_qa_catches_silent_music_render(corpus, music, tmp_path) -> None:
    # A silent render validated AS music must fail (music must not be silent).
    sources = [_ING.probe_clip(str(corpus["portrait_audio"]))]
    project = _project(sources, music)
    silent = FFmpegRenderer(output_root=tmp_path / "out").export(project, "silent")
    report = FFmpegOutputQA().validate_render(silent.path, project, "music")
    assert report.audio_ok is False and report.passed is False


def test_qa_catches_truncated_render(corpus, music, tmp_path) -> None:
    sources = [_ING.probe_clip(str(corpus["portrait_audio"])), _ING.probe_clip(str(corpus["landscape_silent"]))]
    project = _project(sources, music)  # timeline 2.0 s
    full = FFmpegRenderer(output_root=tmp_path / "out").export(project, "silent")

    trunc = tmp_path / "trunc.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-i", full.path, "-t", "0.5", "-c:v", "libx264", "-c:a", "aac", str(trunc)],
        check=True, capture_output=True,
    )
    report = FFmpegOutputQA().validate_render(str(trunc), project, "silent")
    assert report.duration_ok is False and report.passed is False


def test_qa_passes_legit_silent_render(corpus, music, tmp_path) -> None:
    sources = [_ING.probe_clip(str(corpus["portrait_audio"]))]
    project = _project(sources, music)
    record = FFmpegRenderer(output_root=tmp_path / "out").export(project, "silent")
    report = FFmpegOutputQA().validate_render(record.path, project, "silent")
    assert report.passed is True  # silent is EXPECTED here — must not fail for being silent


def test_qa_passes_clip_mode_when_all_sources_are_audioless(corpus, music, tmp_path) -> None:
    # Every included source is audio-less → a correctly-silent clip render must pass.
    src = _ING.probe_clip(str(corpus["landscape_silent"]))
    assert src.has_audio is False
    project = _project([src], music)
    record = FFmpegRenderer(output_root=tmp_path / "out").export(project, "clip")
    report = FFmpegOutputQA().validate_render(record.path, project, "clip")
    assert report.audio_ok is True and report.passed is True
