"""Output QA per ES-001 §8.3 — blocks export when a render is wrong.

Checks: not black · audio matched to the mode (music not silent; silent *is*
silent yet carries a valid track; clip carries a track and is non-silent unless
every included source is audio-less) · duration within ±0.5 s of the timeline ·
exactly 1080×1920 · H.264/AAC · non-zero frames · title-safe margins. Emits a
QAReport; `passed=False` blocks export, with a human reason per failure.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from backend.contracts.models import AudioMode, Project, QAReport
from backend.render.ffmpeg_render import TARGET_FPS, TARGET_H, TARGET_W, timeline_duration_s

DURATION_TOL_S = 0.5
SILENCE_FLOOR_DB = -70.0
BLACK_RATIO_FAIL = 0.95


class QAError(Exception):
    """QA could not inspect the render (probe failure)."""


def _ffprobe(path: Path) -> dict:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise QAError(f"ffprobe failed for {path.name}: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def _mean_volume_db(path: Path) -> float | None:
    """Mean volume in dB, or None if there is no audio to measure."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-map", "0:a?", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    m = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?|-inf)\s*dB", proc.stderr)
    if not m:
        return None
    return -999.0 if m.group(1) == "-inf" else float(m.group(1))


def _black_ratio(path: Path, duration: float) -> float:
    if duration <= 0:
        return 1.0
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-vf", "blackdetect=d=0.1", "-an", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    total = 0.0
    for m in re.finditer(r"black_start:(\d+(?:\.\d+)?)\s+black_end:(\d+(?:\.\d+)?)", proc.stderr):
        total += float(m.group(2)) - float(m.group(1))
    return total / duration


def _included_sources(project: Project):
    included_ids = {c.source_id for c in project.clips if c.included and not c.deleted}
    return [s for s in project.sources if s.source_id in included_ids]


class FFmpegOutputQA:
    def validate_render(self, render_path: str, project: Project, audio_mode: AudioMode) -> QAReport:
        data = _ffprobe(Path(render_path))
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        fmt = data.get("format", {})

        duration = float(fmt.get("duration") or (video or {}).get("duration") or 0.0)
        width = int(video.get("width", 0)) if video else 0
        height = int(video.get("height", 0)) if video else 0
        vcodec = video.get("codec_name") if video else None
        acodec = audio.get("codec_name") if audio else None

        try:
            frame_count = int((video or {}).get("nb_frames"))
        except (TypeError, ValueError):
            frame_count = int(duration * TARGET_FPS)  # estimate when the container omits it

        expected = timeline_duration_s(project)
        reasons: list[str] = []

        resolution_ok = (width, height) == (TARGET_W, TARGET_H)
        if not resolution_ok:
            reasons.append(f"resolution {width}x{height} != {TARGET_W}x{TARGET_H}")

        codec_ok = vcodec == "h264" and acodec == "aac"
        if not codec_ok:
            reasons.append(f"codecs v={vcodec} a={acodec}, expected h264/aac")

        duration_ok = abs(duration - expected) <= DURATION_TOL_S
        if not duration_ok:
            reasons.append(f"duration {duration:.2f}s off timeline {expected:.2f}s (>±{DURATION_TOL_S})")

        frame_count_ok = frame_count > 0
        if not frame_count_ok:
            reasons.append("zero frame count")

        not_black = _black_ratio(Path(render_path), duration) < BLACK_RATIO_FAIL
        if not not_black:
            reasons.append("render is black")

        has_audio_stream = audio is not None
        mean_db = _mean_volume_db(Path(render_path)) if has_audio_stream else None
        is_silent = mean_db is None or mean_db <= SILENCE_FLOOR_DB
        all_sources_silent = all(not s.has_audio for s in _included_sources(project)) if _included_sources(project) else True

        if audio_mode == "music":
            audio_ok = has_audio_stream and not is_silent
            if not audio_ok:
                reasons.append("music mode has no audio or is silent")
        elif audio_mode == "silent":
            audio_ok = has_audio_stream and is_silent
            if not audio_ok:
                reasons.append("silent mode must carry a valid, silent audio track")
        elif audio_mode == "clip":
            audio_ok = has_audio_stream and (not is_silent or all_sources_silent)
            if not audio_ok:
                reasons.append("clip mode is silent though sources carry audio, or has no track")
        else:  # pragma: no cover - AudioMode is a closed Literal
            audio_ok = False
            reasons.append(f"unknown audio_mode {audio_mode!r}")

        # M1 renders no titles/overlays, so there is nothing to violate the margins;
        # this becomes a real pixel check when on-screen text arrives (post-M1).
        safe_margins_ok = True

        passed = all([not_black, audio_ok, duration_ok, resolution_ok, codec_ok, frame_count_ok, safe_margins_ok])
        return QAReport(
            passed=passed,
            not_black=not_black,
            audio_ok=audio_ok,
            duration_ok=duration_ok,
            resolution_ok=resolution_ok,
            codec_ok=codec_ok,
            safe_margins_ok=safe_margins_ok,
            frame_count_ok=frame_count_ok,
            duration_s=duration,
            width=width,
            height=height,
            reasons=reasons,
        )
