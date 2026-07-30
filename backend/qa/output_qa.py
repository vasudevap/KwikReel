"""WO-122 · Output QA against the v2 project's derived render contract."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from backend.contracts.models import Project, QAReport
from backend.render.ffmpeg_render import TARGET_FPS, timeline_duration_s
from backend.store.derive import in_reel, unlinked_source_ids

DURATION_TOL_S = 0.5
SILENCE_FLOOR_DB = -70.0
BLACK_RATIO_FAIL = 0.95
_RESOLUTIONS = {
    "720p": (720, 1280),
    "1080p": (1080, 1920),
    "4k": (2160, 3840),
}


class QAError(Exception):
    """QA could not inspect the render."""


def _ffprobe(path: Path) -> dict:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise QAError(f"ffprobe failed for {path.name}: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def _mean_volume_db(path: Path) -> float | None:
    """Mean volume in dB, or None when ffmpeg finds no measurable track."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-map", "0:a?", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?|-inf)\s*dB", proc.stderr)
    if not match:
        return None
    return -999.0 if match.group(1) == "-inf" else float(match.group(1))


def _black_ratio(path: Path, duration: float) -> float:
    if duration <= 0:
        return 1.0
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-vf", "blackdetect=d=0.1", "-an", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    total = sum(
        float(match.group(2)) - float(match.group(1))
        for match in re.finditer(
            r"black_start:(\d+(?:\.\d+)?)\s+black_end:(\d+(?:\.\d+)?)",
            proc.stderr,
        )
    )
    return total / duration


def _clip_audio_can_be_audible(project: Project) -> bool:
    """Whether the derived reel includes an unmuted source with an audio track."""
    unlinked = unlinked_source_ids(project)
    sources = {source.source_id: source for source in project.sources}
    return any(
        in_reel(project, clip, unlinked)
        and clip.audio.retain
        and sources[clip.source_id].has_audio
        for clip in project.clips
    )


class FFmpegOutputQA:
    """Inspect one v2 export; never render or mutate project state."""

    def validate_render(self, render_path: str, project: Project) -> QAReport:
        data = _ffprobe(Path(render_path))
        streams = data.get("streams", [])
        video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
        fmt = data.get("format", {})

        duration = float(fmt.get("duration") or (video or {}).get("duration") or 0.0)
        width = int(video.get("width", 0)) if video else 0
        height = int(video.get("height", 0)) if video else 0
        vcodec = video.get("codec_name") if video else None
        acodec = audio.get("codec_name") if audio else None
        try:
            frame_count = int((video or {}).get("nb_frames"))
        except (TypeError, ValueError):
            frame_count = int(duration * TARGET_FPS)

        expected_duration = timeline_duration_s(project)
        expected_resolution = _RESOLUTIONS[project.output_resolution]
        reasons: list[str] = []

        resolution_ok = (width, height) == expected_resolution
        if not resolution_ok:
            reasons.append(
                f"resolution {width}x{height} != {expected_resolution[0]}x{expected_resolution[1]}"
            )

        codec_ok = vcodec == "h264" and acodec == "aac"
        if not codec_ok:
            reasons.append(f"codecs v={vcodec} a={acodec}, expected h264/aac")

        duration_ok = abs(duration - expected_duration) <= DURATION_TOL_S
        if not duration_ok:
            reasons.append(
                f"duration {duration:.2f}s off timeline {expected_duration:.2f}s (>±{DURATION_TOL_S})"
            )

        frame_count_ok = frame_count > 0
        if not frame_count_ok:
            reasons.append("zero frame count")

        not_black = _black_ratio(Path(render_path), duration) < BLACK_RATIO_FAIL
        if not not_black:
            reasons.append("render is black")

        has_audio_stream = audio is not None
        mean_db = _mean_volume_db(Path(render_path)) if has_audio_stream else None
        is_silent = mean_db is None or mean_db <= SILENCE_FLOOR_DB
        both_levels_zero = project.audio.music_level == 0 and project.audio.clip_level == 0
        sound_expected = project.audio.music_level > 0 or (
            project.audio.clip_level > 0 and _clip_audio_can_be_audible(project)
        )

        if both_levels_zero:
            audio_ok = has_audio_stream and acodec == "aac" and is_silent
            if not audio_ok:
                reasons.append("zero audio levels require a valid, silent AAC track")
        elif sound_expected:
            audio_ok = has_audio_stream and not is_silent
            if not audio_ok:
                reasons.append("audio levels require an audible AAC track")
        else:
            # A clip-only mix may correctly be silent when all retained sources
            # lack audio or are muted; it still needs the export's AAC track.
            audio_ok = has_audio_stream and acodec == "aac"
            if not audio_ok:
                reasons.append("export must carry a valid AAC track")

        # No titles or overlays are in the frozen v2 renderer. This stays an
        # explicit report field until a later authorized WO adds one to inspect.
        safe_margins_ok = True
        passed = all(
            [
                not_black,
                audio_ok,
                duration_ok,
                resolution_ok,
                codec_ok,
                frame_count_ok,
                safe_margins_ok,
            ]
        )
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
