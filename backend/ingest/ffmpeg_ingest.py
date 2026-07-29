"""FFprobe-based ingest and FFmpeg proxy generation.

Read-only over `media_root`: probing and hashing only read; proxies are written
to a separate `proxy_root`. Nothing beneath `media_root` is ever created,
modified, moved, or deleted (ES-001 §9, verified by test).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from backend.contracts.models import SourceIndex

VIDEO_EXTS = {".mov", ".mp4", ".m4v", ".avi", ".mkv", ".hevc", ".mts"}
_CHUNK = 1 << 20


class ProbeError(Exception):
    """ffprobe failed or the file has no decodable video stream."""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _ffprobe(path: Path) -> dict:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ProbeError(f"ffprobe failed for {path.name}: {proc.stderr.strip()[:200]}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ProbeError(f"ffprobe produced no JSON for {path.name}") from exc


def _parse_fps(rate: str | None) -> float:
    if not rate or rate in ("0/0", "0"):
        return 0.0
    num, _, den = rate.partition("/")
    try:
        d = float(den) if den else 1.0
        return round(float(num) / d, 3) if d else 0.0
    except ValueError:
        return 0.0


def _rotation(video: dict) -> int:
    for sd in video.get("side_data_list", []) or []:
        if "rotation" in sd:
            try:
                return abs(int(sd["rotation"])) % 360
            except (TypeError, ValueError):
                pass
    tags = video.get("tags", {}) or {}
    if "rotate" in tags:
        try:
            return abs(int(tags["rotate"])) % 360
        except (TypeError, ValueError):
            pass
    return 0


def _stable_id(content_hash: str) -> str:
    return f"src-{content_hash[:16]}"


class FFmpegIngest:
    """Probe sources and build proxies. `proxy_root` is separate from media_root."""

    def __init__(self, proxy_root: str | Path) -> None:
        self.proxy_root = Path(proxy_root)

    # --- IngestService ----------------------------------------------------

    def validate_readable(self, path: str) -> bool:
        try:
            data = _ffprobe(Path(path))
        except ProbeError:
            return False
        return any(s.get("codec_type") == "video" for s in data.get("streams", []))

    def probe_clip(self, path: str) -> SourceIndex:
        p = Path(path)
        data = _ffprobe(p)
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        if video is None:
            raise ProbeError(f"no video stream in {p.name}")
        fmt = data.get("format", {})
        tags = {k.lower(): v for k, v in (fmt.get("tags", {}) or {}).items()}

        width = int(video.get("width", 0))
        height = int(video.get("height", 0))
        if _rotation(video) in (90, 270):  # display orientation, rotation-corrected
            width, height = height, width

        has_gps = any("location" in k or "gps" in k for k in tags)
        captured_at = tags.get("creation_time")
        content_hash = _sha256(p)

        return SourceIndex(
            source_id=_stable_id(content_hash),
            content_hash=content_hash,
            path=str(p),
            duration_s=float(fmt.get("duration") or video.get("duration") or 0.0),
            captured_at=captured_at,
            orientation="portrait" if height >= width else "landscape",
            codec=str(video.get("codec_name", "unknown")),
            fps=_parse_fps(video.get("r_frame_rate")),
            width=width,
            height=height,
            has_audio=any(s.get("codec_type") == "audio" for s in streams),
            has_gps=has_gps,
            readable=True,
            proxy_path=None,
        )

    def build_source_index(self, media_root: str) -> list[SourceIndex]:
        root = Path(media_root)
        sources: list[SourceIndex] = []
        for path in sorted(root.iterdir()):
            if not path.is_file() or path.suffix.lower() not in VIDEO_EXTS:
                continue
            try:
                sources.append(self.probe_clip(str(path)))
            except ProbeError:
                # Reported, never dropped: retained readable=False (reason surfaced
                # out-of-band via the API/job log; SourceIndex has no reason field).
                sources.append(self._unreadable(path))
        return sources

    def make_proxy(self, source: SourceIndex) -> str:
        """Write a 540×960 H.264 preview proxy to proxy_root; return its path.

        Never writes beneath media_root. Letterboxes any orientation into 540×960
        so the preview <video> is a consistent size.

        **The proxy carries the source's audio** (WO-116a). It previously did
        not — `-an` made every proxy silent — and the Monitor plays proxies, so
        that left `SPEC.md` §5's `clip_level` acting on nothing, the Sound unit
        drawing traces for audio that could not play, and §6's "preview loudness
        must match export loudness" unsatisfiable with one side silent.

        **Keyframes are ~1 s apart.** x264's default is 250 frames — 8.3 s at
        30 fps — and WO-124 measured seek latency rising to 45 ms the further a
        target lands past a keyframe. Seeking was already frame-*accurate*; this
        only buys back the latency, which the trim handles and the scrub pay on
        every drag.
        """
        self.proxy_root.mkdir(parents=True, exist_ok=True)
        out = self.proxy_root / f"{source.source_id}.mp4"
        vf = (
            "scale=540:960:force_original_aspect_ratio=decrease,"
            "pad=540:960:(ow-iw)/2:(oh-ih)/2,setsar=1"
        )
        # One keyframe per second of source. fps is a float on real footage
        # (29.97), and 0.0 on anything that failed to probe cleanly.
        gop = max(1, round(source.fps)) if source.fps and source.fps > 0 else 30
        cmd = [
            "ffmpeg", "-y", "-i", source.path,
            "-vf", vf, "-c:v", "libx264", "-b:v", "1.5M",
            "-g", str(gop),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        ]
        if source.has_audio:
            # Downmixed to stereo: a 5.1 source would otherwise give the preview
            # a channel layout the mix in §5 was never specified against.
            cmd += ["-c:a", "aac", "-b:a", "128k", "-ac", "2"]
        else:
            # No track rather than a fabricated silent one. `has_audio` already
            # tells the UI, and inventing silence would make a source that never
            # had sound indistinguishable from one the user muted.
            cmd += ["-an"]
        cmd += [str(out)]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise ProbeError(f"proxy generation failed for {source.source_id}: {proc.stderr.strip()[:200]}")
        return str(out)

    # --- internal ---------------------------------------------------------

    def _unreadable(self, path: Path) -> SourceIndex:
        try:
            content_hash = _sha256(path)
        except OSError:
            content_hash = "sha256:unreadable"
        return SourceIndex(
            source_id=_stable_id(content_hash) if not content_hash.startswith("sha256:") else f"src-{path.stem}",
            content_hash=content_hash,
            path=str(path),
            duration_s=0.0,
            captured_at=None,
            orientation="portrait",
            codec="unknown",
            fps=0.0,
            width=0,
            height=0,
            has_audio=False,
            has_gps=False,
            readable=False,
            proxy_path=None,
        )
