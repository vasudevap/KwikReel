"""WO-102 gates (synthetic fixtures) · probing facts, corrupt-file handling,
proxies, and read-only enforcement over media_root. The real 50-clip-day gate is
deferred until the ADR-002 consent record exists.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from backend.ingest import FFmpegIngest, ProbeError
from tests.synthetic import ffmpeg_available, make_corpus

pytestmark = pytest.mark.skipif(
    not ffmpeg_available(), reason="ffmpeg/ffprobe not installed (ES-001 §3 dependency)"
)


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> dict[str, Path]:
    return make_corpus(tmp_path_factory.mktemp("media"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_probe_portrait_with_audio(corpus) -> None:
    s = FFmpegIngest(proxy_root="/unused").probe_clip(str(corpus["portrait_audio"]))
    assert s.readable is True
    assert s.orientation == "portrait"
    assert (s.width, s.height) == (1080, 1920)
    assert s.codec == "h264"
    assert s.fps == 30.0
    assert s.has_audio is True
    assert 2.5 < s.duration_s < 3.6
    assert s.captured_at is None and s.has_gps is False
    assert len(s.content_hash) == 64 and int(s.content_hash, 16) >= 0
    assert s.source_id.startswith("src-")


def test_probe_landscape_silent(corpus) -> None:
    s = FFmpegIngest(proxy_root="/unused").probe_clip(str(corpus["landscape_silent"]))
    assert s.orientation == "landscape"
    assert (s.width, s.height) == (1920, 1080)
    assert s.has_audio is False


def test_probe_reads_hevc_codec(corpus) -> None:
    s = FFmpegIngest(proxy_root="/unused").probe_clip(str(corpus["hevc_audio"]))
    assert s.codec == "hevc"
    assert s.has_audio is True


def test_corrupt_file_is_reported_not_crashed(corpus) -> None:
    ing = FFmpegIngest(proxy_root="/unused")
    assert ing.validate_readable(str(corpus["broken"])) is False
    with pytest.raises(ProbeError):
        ing.probe_clip(str(corpus["broken"]))

    # build_source_index keeps it, flagged unreadable — never dropped, never raises.
    media_root = corpus["portrait_audio"].parent
    sources = ing.build_source_index(str(media_root))
    by_readable = {s.readable for s in sources}
    assert by_readable == {True, False}
    broken = next(s for s in sources if not s.readable)
    assert broken.path.endswith("d_broken.mov")
    assert len(sources) == 4  # 3 readable + 1 unreadable


def test_make_proxy_is_540x960_h264(corpus, tmp_path) -> None:
    ing = FFmpegIngest(proxy_root=tmp_path / "proxies")
    src = ing.probe_clip(str(corpus["landscape_silent"]))  # landscape -> letterboxed
    proxy_path = ing.make_proxy(src)
    assert Path(proxy_path).exists()

    probed = ing.probe_clip(proxy_path)  # the proxy is itself a valid, playable clip
    assert probed.codec == "h264"
    assert (probed.width, probed.height) == (540, 960)


def test_originals_are_never_written(corpus, tmp_path) -> None:
    media_root = corpus["portrait_audio"].parent
    before = {p.name: _sha256(p) for p in sorted(media_root.iterdir()) if p.is_file()}

    ing = FFmpegIngest(proxy_root=tmp_path / "proxies")
    for s in ing.build_source_index(str(media_root)):
        if s.readable:
            proxy = Path(ing.make_proxy(s))
            assert tmp_path in proxy.parents  # proxy lands in proxy_root, not media_root
            assert media_root not in proxy.parents

    after = {p.name: _sha256(p) for p in sorted(media_root.iterdir()) if p.is_file()}
    assert before == after  # nothing beneath media_root created, modified, or removed
