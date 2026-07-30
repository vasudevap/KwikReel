"""WO-121 renderer-v2 gates on generated, synthetic media only.

Output verdicts belong to WO-122. This reduced file proves the renderer itself
uses the derived v2 timeline, clamps speed pieces to arithmetic duration,
refuses upscaling, skips out-of-reel clips, and strips source metadata.
"""

from __future__ import annotations

import json
import subprocess
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
    Proposals,
    ReasonRecord,
    Segment,
    SegmentsProposal,
    SourceIndex,
    SpeedRange,
)
from backend.ingest import FFmpegIngest
from backend.render import FFmpegRenderer, RenderError
from backend.store.derive import reel_length_s, unlinked_source_ids
from tests.synthetic import ffmpeg_available, make_clip, make_music

pytestmark = pytest.mark.skipif(
    not ffmpeg_available(), reason="ffmpeg/ffprobe not installed"
)

_INGEST = FFmpegIngest(proxy_root="/unused")


@pytest.fixture(scope="module")
def portrait(tmp_path_factory) -> Path:
    return make_clip(
        tmp_path_factory.mktemp("renderer-media") / "portrait.mp4",
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
    segment: Segment | None = None,
    speeds: list[SpeedRange] | None = None,
    retain_audio: bool = True,
) -> Clip:
    segment_is_user = segment is not None
    speed_is_user = speeds is not None
    return Clip(
        source_id=source_id,
        order=order,
        segment=segment,
        speed_ranges=speeds or [],
        audio=AudioSettings(retain=retain_audio, gain_db=0.0),
        origin=Origin(
            segments="user" if segment_is_user else "default",
            speed="user" if speed_is_user else "default",
        ),
        proposals=Proposals(),
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
        project_id="renderer-v2-test",
        created_at="2026-07-30T12:00:00Z",
        updated_at="2026-07-30T12:00:00Z",
        app_version="0.2.0",
        name="Renderer v2 Test",
        media_root=str(Path(sources[0].path).parent),
        target_duration_s=75.0,
        output_resolution=resolution,
        trim_assist_on=False,
        speed_assist_on=False,
        audio=AudioMix(music_level=music_level, clip_level=clip_level),
        music=music,
        sources=sources,
        clips=clips or [_clip(item.source_id, order=index) for index, item in enumerate(sources, 1)],
        export=Export(),
    )


def _probe(path: str | Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


def _duration(path: str | Path) -> float:
    return float(_probe(path)["format"]["duration"])


def test_renders_one_file_at_project_resolution(source, tmp_path) -> None:
    project = _project([source], resolution="720p")
    record = FFmpegRenderer(tmp_path / "out").export(project)
    probe = _probe(record.path)
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")

    assert Path(record.path).name == "renderer-v2-test.mp4"
    assert (video["width"], video["height"]) == (720, 1280)
    assert video["codec_name"] == "h264"
    assert audio["codec_name"] == "aac"
    assert abs(_duration(record.path) - 3.0) <= 0.05


def test_effective_assist_trim_is_rendered(source, tmp_path) -> None:
    clip = _clip(source.source_id)
    clip.origin.segments = "proposed"
    clip.proposals.segments = SegmentsProposal(
        value=Segment(in_s=0.5, out_s=2.0),
        at="2026-07-30T12:01:00Z",
        reasons=[
            ReasonRecord(
                code="SYNTHETIC_TRIM",
                human_text="Synthetic trim fixture.",
                evidence_refs=["signals.blur[0:1]"],
                score=0.5,
                confidence="med",
            )
        ],
        disposition="pending",
    )
    project = _project([source], [clip])
    project.trim_assist_on = True

    record = FFmpegRenderer(tmp_path / "out").export(project)
    assert abs(_duration(record.path) - 1.5) <= 0.05


@pytest.mark.parametrize("rate", [0.25, 4.0])
def test_chained_atempo_speed_matches_arithmetic_exactly(source, tmp_path, rate) -> None:
    clip = _clip(
        source.source_id,
        segment=Segment(in_s=0.0, out_s=3.0),
        speeds=[SpeedRange(from_s=0.0, to_s=3.0, rate=rate)],
    )
    project = _project([source], [clip])
    expected = 3.0 / rate

    record = FFmpegRenderer(tmp_path / f"out-{rate}").export(project)
    assert reel_length_s(project, unlinked_source_ids(project)) == pytest.approx(expected)
    assert abs(_duration(record.path) - expected) <= 0.05


def test_short_music_does_not_truncate_the_reel(source, tmp_path) -> None:
    track = make_music(tmp_path / "short.m4a", duration=0.75)
    music = Music(
        track_ref=str(track),
        content_hash="sha256:synthetic-music",
        duration_s=0.75,
        in_s=0.0,
    )
    project = _project(
        [source],
        music=music,
        music_level=0.6,
        clip_level=0.8,
    )

    record = FFmpegRenderer(tmp_path / "out").export(project)
    assert abs(_duration(record.path) - 3.0) <= 0.05


def test_out_of_reel_sources_are_skipped_and_every_clip_out_is_stated(
    source, tmp_path
) -> None:
    missing = source.model_copy(
        update={"source_id": "missing", "path": str(tmp_path / "missing.mp4")}
    )
    damaged = source.model_copy(update={"source_id": "damaged", "readable": False})
    kept = _clip(source.source_id, order=1, segment=Segment(in_s=0.0, out_s=1.0))
    project = _project(
        [source, missing, damaged],
        [
            kept,
            _clip("missing", order=2),
            _clip("damaged", order=3),
        ],
    )

    record = FFmpegRenderer(tmp_path / "out").export(project)
    assert abs(_duration(record.path) - 1.0) <= 0.05

    kept.segment = Segment(in_s=0.0, out_s=0.0)
    with pytest.raises(RenderError, match="every clip is trimmed out, unlinked, or damaged"):
        FFmpegRenderer(tmp_path / "empty").export(project)


def test_upscaling_is_refused_with_a_stated_reason(source, tmp_path) -> None:
    project = _project([source], resolution="4k")
    with pytest.raises(RenderError, match=r"upscaling refused.*1080x1920.*2160x3840"):
        FFmpegRenderer(tmp_path / "out").export(project)


def test_source_metadata_is_stripped_and_zero_mix_keeps_aac(
    portrait, tmp_path
) -> None:
    tagged = tmp_path / "tagged.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(portrait),
            "-c",
            "copy",
            "-metadata",
            "title=synthetic-fixture",
            "-metadata",
            "location=+00.0000+000.0000/",
            str(tagged),
        ],
        check=True,
        capture_output=True,
    )
    tagged_source = _INGEST.probe_clip(str(tagged))
    project = _project([tagged_source], music_level=0.0, clip_level=0.0)

    record = FFmpegRenderer(tmp_path / "out").export(project)
    probe = _probe(record.path)
    tags = {key.lower() for key in probe["format"].get("tags", {})}
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")

    assert "title" not in tags
    assert "location" not in tags
    assert "creation_time" not in tags
    assert audio["codec_name"] == "aac"
