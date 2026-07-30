"""WO-122 · QA-v2 gates on generated synthetic exports only."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.contracts.models import (
    AudioMix,
    AudioSettings,
    Clip,
    Export,
    Music,
    Origin,
    Project,
    Segment,
    SourceIndex,
    SpeedRange,
)
from backend.ingest import FFmpegIngest
from backend.qa import FFmpegOutputQA
from backend.render import FFmpegRenderer
from tests.synthetic import ffmpeg_available, make_black_clip, make_clip, make_music

pytestmark = pytest.mark.skipif(
    not ffmpeg_available(), reason="ffmpeg/ffprobe not installed"
)

_INGEST = FFmpegIngest(proxy_root="/unused")


@pytest.fixture(scope="module")
def portrait(tmp_path_factory) -> Path:
    return make_clip(
        tmp_path_factory.mktemp("qa-media") / "portrait.mp4",
        size="1080x1920",
        codec="h264",
        duration=3.0,
        with_audio=True,
    )


@pytest.fixture(scope="module")
def source(portrait: Path) -> SourceIndex:
    return _INGEST.probe_clip(str(portrait))


def _clip(
    source_id: str,
    *,
    order: int = 1,
    speeds: list[SpeedRange] | None = None,
) -> Clip:
    return Clip(
        source_id=source_id,
        order=order,
        segment=Segment(in_s=0.0, out_s=3.0),
        speed_ranges=speeds or [],
        audio=AudioSettings(retain=True, gain_db=0.0),
        origin=Origin(segments="user", speed="user" if speeds is not None else "default"),
    )


def _project(
    sources: list[SourceIndex],
    clips: list[Clip] | None = None,
    *,
    resolution: str = "1080p",
    music: Music | None = None,
    music_level: float = 0.0,
    clip_level: float = 1.0,
) -> Project:
    return Project(
        schema_version=2,
        project_id="qa-v2-test",
        created_at="2026-07-30T13:00:00Z",
        updated_at="2026-07-30T13:00:00Z",
        app_version="0.2.0",
        name="QA v2 Test",
        media_root=str(Path(sources[0].path).parent),
        target_duration_s=75.0,
        output_resolution=resolution,
        audio=AudioMix(music_level=music_level, clip_level=clip_level),
        music=music,
        sources=sources,
        clips=clips or [_clip(item.source_id, order=index) for index, item in enumerate(sources, 1)],
        export=Export(),
    )


def test_uses_the_project_resolution_not_a_hardcoded_target(source, tmp_path) -> None:
    project = _project([source], resolution="720p")
    record = FFmpegRenderer(tmp_path / "out").export(project)

    report = FFmpegOutputQA().validate_render(record.path, project)
    assert report.passed
    assert report.resolution_ok
    assert (report.width, report.height) == (720, 1280)


def test_music_level_requires_audible_audio_and_zero_mix_passes_silent_aac(
    source, tmp_path
) -> None:
    track = make_music(tmp_path / "music.m4a", duration=3.0)
    music = Music(
        track_ref=str(track),
        content_hash="sha256:synthetic-track",
        duration_s=3.0,
        in_s=0.0,
    )
    audible_project = _project(
        [source], music=music, music_level=0.6, clip_level=0.0
    )
    silent_project = _project(
        [source], music=music, music_level=0.0, clip_level=0.0
    )
    qa = FFmpegOutputQA()
    audible = FFmpegRenderer(tmp_path / "audible").export(audible_project)
    assert qa.validate_render(audible.path, audible_project).passed
    silent = FFmpegRenderer(tmp_path / "silent").export(silent_project)
    silent_report = qa.validate_render(silent.path, silent_project)
    assert silent_report.passed and silent_report.audio_ok

    rejected = qa.validate_render(silent.path, audible_project)
    assert not rejected.passed
    assert not rejected.audio_ok
    assert "audio levels require an audible AAC track" in rejected.reasons


def test_bad_render_is_blocked_with_stated_reasons(tmp_path) -> None:
    black_path = make_black_clip(tmp_path / "black.mp4", duration=1.0)
    black_source = _INGEST.probe_clip(str(black_path))
    project = _project([black_source])

    report = FFmpegOutputQA().validate_render(str(black_path), project)
    assert not report.passed
    assert not report.not_black
    assert "render is black" in report.reasons
    assert report.reasons


def test_resolution_mismatch_is_stated(source, tmp_path) -> None:
    rendered_for_720 = _project([source], resolution="720p")
    record = FFmpegRenderer(tmp_path / "out").export(rendered_for_720)
    expected_1080 = _project([source], resolution="1080p")

    report = FFmpegOutputQA().validate_render(record.path, expected_1080)
    assert not report.passed
    assert not report.resolution_ok
    assert "resolution 720x1280 != 1080x1920" in report.reasons


def test_multi_clip_ramped_reel_stays_inside_duration_tolerance(source, tmp_path) -> None:
    sources = [
        source.model_copy(update={"source_id": f"synthetic-{index}"})
        for index in range(3)
    ]
    clips = [
        _clip(
            item.source_id,
            order=index,
            speeds=[SpeedRange(from_s=0.0, to_s=3.0, rate=2.0)],
        )
        for index, item in enumerate(sources, 1)
    ]
    project = _project(sources, clips)
    record = FFmpegRenderer(tmp_path / "out").export(project)

    report = FFmpegOutputQA().validate_render(record.path, project)
    assert report.duration_ok
    assert report.passed
    assert report.duration_s == pytest.approx(4.5, abs=0.5)
