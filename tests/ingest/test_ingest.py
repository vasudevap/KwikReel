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


# --- WO-116a · the proxy is the thing the Monitor plays -------------------
#
# None of this existed, which is how `-an` survived. The one proxy assertion in
# the suite used `landscape_silent` — a source with NO audio — so an audio check
# would have found nothing missing and passed. That is the same shape of blind
# spot as the letterbox fault WO-116 fixed, where the only exposure assertion
# used a black *portrait* clip that letterboxed to nothing.

def _streams(path: str, kind: str) -> list[dict]:
    import json
    import subprocess
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", kind[0],
         "-show_streams", "-print_format", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout).get("streams", [])


def test_proxy_of_a_source_with_audio_carries_audio(corpus, tmp_path) -> None:
    """The assertion whose absence let every proxy ship silent.

    The Monitor plays proxies. A silent proxy means `clip_level` (SPEC.md §5)
    has nothing to act on and preview loudness cannot match export loudness
    (§6) — so this is a contract requirement, not a nicety.
    """
    ing = FFmpegIngest(proxy_root=tmp_path / "proxies")
    src = ing.probe_clip(str(corpus["portrait_audio"]))
    assert src.has_audio, "fixture precondition: this source must have audio"

    audio = _streams(ing.make_proxy(src), "audio")
    assert audio, "proxy has no audio track — the Monitor would preview silence"
    assert audio[0]["codec_name"] == "aac"
    assert int(audio[0]["channels"]) == 2   # downmixed, per make_proxy


def test_proxy_of_a_silent_source_still_builds(corpus, tmp_path) -> None:
    """No fabricated silence: a source that never had sound gets no track.

    Inventing one would make it indistinguishable from a clip the user muted.
    """
    ing = FFmpegIngest(proxy_root=tmp_path / "proxies")
    src = ing.probe_clip(str(corpus["landscape_silent"]))
    assert not src.has_audio

    proxy_path = ing.make_proxy(src)
    assert Path(proxy_path).exists()
    assert not _streams(proxy_path, "audio")
    assert ing.probe_clip(proxy_path).width == 540  # still a valid proxy


def test_proxy_keyframes_are_about_a_second_apart(corpus, tmp_path) -> None:
    """WO-124 measured seek latency rising with distance past a keyframe.

    x264's default 250-frame GOP put keyframes 8.3 s apart and cost up to 45 ms
    on a seek. Seeking was already frame-accurate; this guards the latency the
    trim handles and the scrub pay on every drag.
    """
    import json
    import subprocess
    ing = FFmpegIngest(proxy_root=tmp_path / "proxies")
    src = ing.probe_clip(str(corpus["portrait_audio"]))
    proxy_path = ing.make_proxy(src)

    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "frame=pts_time,key_frame", "-print_format", "json", proxy_path],
        capture_output=True, text=True, check=True,
    )
    keys = [float(f["pts_time"]) for f in json.loads(out.stdout)["frames"] if f.get("key_frame") == 1]
    assert len(keys) >= 2, f"only {len(keys)} keyframe(s) — the GOP is still the x264 default"
    gaps = [b - a for a, b in zip(keys, keys[1:])]
    assert max(gaps) <= 1.05, f"keyframes up to {max(gaps):.2f}s apart, want ~1s"


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
