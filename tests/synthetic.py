"""Synthetic media corpus for the backend lanes — no real footage, no people.

Generated on demand with ffmpeg's `lavfi` sources (`testsrc`, `sine`), so nothing
binary is committed and the ADR-002 consent gate is never touched. Every lane's
tests build a corpus into a tmp dir via `make_corpus`; if ffmpeg is absent the
tests skip with a recorded reason (never silently pass).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_ENC = {"h264": "libx264", "hevc": "libx265"}


def ffmpeg_available() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True, capture_output=True)


def make_clip(
    path: Path,
    *,
    size: str,          # "WxH", e.g. "1080x1920"
    codec: str,         # "h264" | "hevc"
    duration: float,
    with_audio: bool,
    fps: int = 30,
) -> Path:
    args = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=size={size}:rate={fps}:duration={duration}"]
    if with_audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}"]
    args += ["-c:v", _ENC[codec], "-pix_fmt", "yuv420p"]
    if codec == "hevc":
        args += ["-tag:v", "hvc1"]
    if with_audio:
        args += ["-c:a", "aac", "-shortest"]
    else:
        args += ["-an"]
    args += [str(path)]
    _run(args)
    return path


def make_music(path: Path, duration: float = 12) -> Path:
    _run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=330:duration={duration}", "-c:a", "aac", str(path)])
    return path


def make_black_clip(path: Path, *, size: str = "1080x1920", duration: float = 2) -> Path:
    _run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:size={size}:rate=30:duration={duration}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(path),
    ])
    return path


def make_corpus(root: Path) -> dict[str, Path]:
    """A small corpus spanning the cases the gates need to exercise."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    clips = {
        "portrait_audio": make_clip(root / "a_portrait_h264_audio.mp4", size="1080x1920", codec="h264", duration=3, with_audio=True),
        "landscape_silent": make_clip(root / "b_landscape_h264_silent.mp4", size="1920x1080", codec="h264", duration=2, with_audio=False),
        "hevc_audio": make_clip(root / "c_portrait_hevc_audio.mp4", size="1080x1920", codec="hevc", duration=2, with_audio=True),
    }
    # A deliberately-unreadable file: right extension, garbage bytes.
    broken = root / "d_broken.mov"
    broken.write_bytes(b"\x00\x01\x02 not a real video " * 64)
    clips["broken"] = broken
    return clips
