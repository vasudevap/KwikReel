"""On-demand local media derivatives for previews (SPEC.md §8).

Thumbnails and waveform peaks are cached beneath ``cache_root`` — never beside
the original, so this service preserves the read-only ``media_root`` rule. The
music cache key is its content hash rather than a project id because a track can
be selected before any project exists.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path
from typing import Optional

from backend.contracts.models import Music, SourceIndex

_PEAK_SAMPLE_RATE = 100


class MediaError(Exception):
    """A local media derivative or picker could not be produced."""


def _safe_key(value: str) -> str:
    """A filesystem-safe opaque cache key; never use paths as cache names."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class FFmpegMediaService:
    """FFmpeg-backed `MediaService` implementation, with a separate cache root."""

    def __init__(self, cache_root: str | Path) -> None:
        self.cache_root = Path(cache_root)

    # --- Preview media ---------------------------------------------------

    def proxy_path(self, source: SourceIndex) -> str:
        if source.proxy_path and Path(source.proxy_path).is_file():
            return source.proxy_path
        raise MediaError(f"no preview proxy for {Path(source.path).name}")

    def thumbnail(self, source: SourceIndex, at_s: float) -> bytes:
        """Return one JPEG preview frame, creating it on the first request."""
        timestamp = max(0.0, min(at_s, max(0.0, source.duration_s)))
        path = self._thumbnail_path(source.content_hash, timestamp)
        if path.is_file():
            return path.read_bytes()

        path.parent.mkdir(parents=True, exist_ok=True)
        media = self._read_path(source)
        command = [
            "ffmpeg", "-y", "-ss", f"{timestamp:.3f}", "-i", str(media),
            "-frames:v", "1", "-q:v", "3", str(path),
        ]
        self._run(command, source.path, "thumbnail")
        try:
            return path.read_bytes()
        except OSError as exc:  # pragma: no cover - ffmpeg success normally guarantees it
            raise MediaError(f"thumbnail was not produced for {Path(source.path).name}") from exc

    def peaks(self, source: SourceIndex) -> list[float]:
        """Return clip-audio peaks, caching the JSON result by source content."""
        cache_path = self._peaks_path("clips", source.content_hash)
        if cache_path.is_file():
            return self._read_peaks(cache_path)
        peaks = self._compute_peaks(self._read_path(source), source.path)
        self._write_peaks(cache_path, peaks)
        return peaks

    def music_peaks(self, track_ref: str, content_hash: str) -> list[float]:
        """Return track peaks keyed solely by the supplied content hash (§8)."""
        cache_path = self._peaks_path("music", content_hash)
        if cache_path.is_file():
            return self._read_peaks(cache_path)
        peaks = self._compute_peaks(Path(track_ref), track_ref)
        self._write_peaks(cache_path, peaks)
        return peaks

    def probe_music(self, track_ref: str, content_hash: str) -> Music:
        """Read a selected track's duration without requiring a project."""
        path = Path(track_ref)
        proc = self._run(
            ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", str(path)],
            track_ref,
            "music probe",
        )
        try:
            duration_s = float(json.loads(proc.stdout).get("format", {}).get("duration") or 0.0)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MediaError(f"music probe returned invalid data for {path.name}") from exc
        return Music(track_ref=track_ref, content_hash=content_hash, duration_s=duration_s)

    # --- Native pickers --------------------------------------------------

    def pick_folder(self) -> Optional[str]:
        return self._pick('POSIX path of (choose folder with prompt "Select a folder of clips")')

    def pick_file(self) -> Optional[str]:
        return self._pick('POSIX path of (choose file with prompt "Select a music track or replacement clip")')

    # --- Internal --------------------------------------------------------

    def _read_path(self, source: SourceIndex) -> Path:
        # A proxy is preferred for interactive preview derivatives, but an
        # ungenerated proxy must not prevent source thumbnails or peaks.
        if source.proxy_path and Path(source.proxy_path).is_file():
            return Path(source.proxy_path)
        return Path(source.path)

    def _thumbnail_path(self, content_hash: str, at_s: float) -> Path:
        millis = int(round(at_s * 1000))
        return self.cache_root / "thumbnails" / _safe_key(content_hash) / f"{millis}.jpg"

    def _peaks_path(self, kind: str, content_hash: str) -> Path:
        return self.cache_root / "peaks" / kind / f"{_safe_key(content_hash)}.json"

    def _compute_peaks(self, media: Path, display_path: str) -> list[float]:
        proc = self._run(
            [
                "ffmpeg", "-v", "error", "-i", str(media), "-vn", "-ac", "1",
                "-ar", str(_PEAK_SAMPLE_RATE), "-f", "f32le", "-",
            ],
            display_path,
            "waveform peaks",
        )
        count = len(proc.stdout) // 4
        if not count:
            return []
        samples = struct.unpack(f"<{count}f", proc.stdout[: count * 4])
        return [round(min(1.0, abs(sample)), 6) for sample in samples]

    def _read_peaks(self, path: Path) -> list[float]:
        try:
            raw = json.loads(path.read_text())
            return [float(item) for item in raw]
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MediaError(f"cached waveform data is invalid ({path.name})") from exc

    def _write_peaks(self, path: Path, peaks: list[float]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(peaks))
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _pick(self, script: str) -> Optional[str]:
        try:
            proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=600)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        return proc.stdout.strip() or None if proc.returncode == 0 else None

    def _run(self, command: list[str], display_path: str, purpose: str) -> subprocess.CompletedProcess:
        try:
            proc = subprocess.run(command, capture_output=True, check=False)
        except FileNotFoundError as exc:
            raise MediaError(f"{purpose} is unavailable for {Path(display_path).name}") from exc
        if proc.returncode != 0:
            raise MediaError(f"{purpose} failed for {Path(display_path).name}")
        return proc
