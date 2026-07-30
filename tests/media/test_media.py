from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path

import pytest

from backend.contracts.models import SourceIndex
from backend.media import FFmpegMediaService
from tests.synthetic import ffmpeg_available, make_clip, make_music


def _source(path: Path, *, proxy_path: str | None = None) -> SourceIndex:
    return SourceIndex(
        source_id="source-1", content_hash="source-hash", path=str(path), duration_s=3.0,
        captured_at=None, orientation="portrait", codec="h264", fps=30.0, width=1080,
        height=1920, has_audio=True, has_gps=False, readable=True, proxy_path=proxy_path,
    )


def test_music_peaks_cache_by_content_hash_before_a_project_exists(tmp_path, monkeypatch) -> None:
    service = FFmpegMediaService(tmp_path / "cache")
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=struct.pack("<3f", -0.25, 0.5, 2.0), stderr=b"")

    monkeypatch.setattr("backend.media.ffmpeg_media.subprocess.run", fake_run)
    first = service.music_peaks("/private/first.m4a", "same-bytes")
    second = service.music_peaks("/private/moved.m4a", "same-bytes")

    assert first == second == [0.25, 0.5, 1.0]
    assert len(calls) == 1


def test_thumbnail_is_cached_and_never_writes_beside_the_source(tmp_path, monkeypatch) -> None:
    source_path = tmp_path / "original.mov"
    source_path.write_bytes(b"original")
    service = FFmpegMediaService(tmp_path / "cache")
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        Path(command[-1]).write_bytes(b"jpeg")
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr("backend.media.ffmpeg_media.subprocess.run", fake_run)
    first = service.thumbnail(_source(source_path), 1.25)
    second = service.thumbnail(_source(source_path), 1.25)

    assert first == second == b"jpeg"
    assert len(calls) == 1
    assert list(tmp_path.glob("original.mov*")) == [source_path]


def test_picker_returns_path_or_clean_cancel(monkeypatch, tmp_path) -> None:
    service = FFmpegMediaService(tmp_path / "cache")
    monkeypatch.setattr(
        "backend.media.ffmpeg_media.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout="/tmp/track.m4a\n", stderr=""),
    )
    assert service.pick_file() == "/tmp/track.m4a"

    monkeypatch.setattr(
        "backend.media.ffmpeg_media.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, stdout="", stderr="User canceled"),
    )
    assert service.pick_folder() is None


def test_music_probe_uses_ffprobe_duration(monkeypatch, tmp_path) -> None:
    service = FFmpegMediaService(tmp_path / "cache")
    monkeypatch.setattr(
        "backend.media.ffmpeg_media.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 0, stdout=json.dumps({"format": {"duration": "12.5"}}).encode(), stderr=b""
        ),
    )
    music = service.probe_music("/tmp/song.m4a", "song-hash")
    assert music.duration_s == 12.5 and music.content_hash == "song-hash"


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_real_synthetic_music_yields_cached_peaks(tmp_path) -> None:
    track = make_music(tmp_path / "track.m4a", duration=1)
    service = FFmpegMediaService(tmp_path / "cache")
    first = service.music_peaks(str(track), "synthetic-track")
    second = service.music_peaks(str(track), "synthetic-track")
    assert first == second
    assert first and all(0.0 <= peak <= 1.0 for peak in first)


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_real_synthetic_video_yields_a_cached_jpeg_thumbnail(tmp_path) -> None:
    clip = make_clip(
        tmp_path / "clip.mp4", size="1080x1920", codec="h264", duration=1, with_audio=False
    )
    service = FFmpegMediaService(tmp_path / "cache")
    first = service.thumbnail(_source(clip), 0.5)
    second = service.thumbnail(_source(clip), 0.5)
    assert first == second
    assert first.startswith(b"\xff\xd8")
