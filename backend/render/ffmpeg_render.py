"""WO-121 · FFmpeg renderer v2.

The renderer consumes the derived v2 timeline: effective trims and speed
ranges, derived reel membership, the selected output resolution, and the two
independent audio levels. It renders one H.264/AAC file from originals.
"""

from __future__ import annotations

import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from backend.contracts.models import Clip, Project, RenderRecord, SourceIndex
from backend.store.derive import (
    effective_speed,
    effective_trim,
    in_reel,
    reel_length_s,
    source_for,
    unlinked_source_ids,
)

TARGET_FPS = 30
_SR, _LAYOUT = 48000, "stereo"
_RESOLUTIONS = {
    "720p": (720, 1280),
    "1080p": (1080, 1920),
    "4k": (2160, 3840),
}


class RenderError(Exception):
    """The render pipeline failed or the derived timeline cannot be rendered."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _number(value: float) -> str:
    """Stable ffmpeg numeric literal without scientific notation."""
    return f"{value:.9f}".rstrip("0").rstrip(".") or "0"


def _timeline_clips(project: Project) -> list[tuple[Clip, SourceIndex]]:
    unlinked = unlinked_source_ids(project)
    clips = [
        (clip, source_for(project, clip))
        for clip in sorted(project.clips, key=lambda item: item.order)
        if in_reel(project, clip, unlinked)
    ]
    if not clips:
        raise RenderError(
            "reel has no renderable clips: every clip is trimmed out, unlinked, or damaged"
        )
    return clips


def timeline_duration_s(project: Project) -> float:
    """The exact derived duration shared with the reel clock and WO-122 QA."""
    return reel_length_s(project, unlinked_source_ids(project))


def output_filename(project: Project) -> str:
    """Deterministic basename for the single v2 export."""
    raw = (project.name or "reel").strip().lower()
    stem = re.sub(r"[^a-z0-9._-]+", "-", raw).strip("-._") or "reel"
    return f"{stem}.mp4"


def _atempo_chain(rate: float) -> list[float]:
    """Split an uncapped positive rate into ffmpeg's supported 0.5–2.0 factors."""
    if not math.isfinite(rate) or rate <= 0:
        raise RenderError("speed range rate must be a finite value greater than zero")

    factors: list[float] = []
    remainder = rate
    while remainder > 2.0:
        factors.append(2.0)
        remainder /= 2.0
    while remainder < 0.5:
        factors.append(0.5)
        remainder /= 0.5
    factors.append(remainder)
    return factors


def _pieces(project: Project, clip: Clip) -> list[tuple[float, float, float]]:
    """Return contiguous source-time pieces as (in, out, playback rate)."""
    trim = effective_trim(project, clip)
    cursor = trim.in_s
    pieces: list[tuple[float, float, float]] = []

    ranges = sorted(effective_speed(project, clip), key=lambda item: item.from_s)
    for speed in ranges:
        start = max(trim.in_s, speed.from_s)
        end = min(trim.out_s, speed.to_s)
        if end <= start:
            continue
        if start < cursor - 1e-9:
            raise RenderError(f"clip {clip.source_id!r} has overlapping speed ranges")
        if start > cursor:
            pieces.append((cursor, start, 1.0))
        _atempo_chain(speed.rate)  # validate even when the source has no audio
        pieces.append((start, end, speed.rate))
        cursor = end

    if cursor < trim.out_s:
        pieces.append((cursor, trim.out_s, 1.0))
    return pieces


def _refuses_upscale(source: SourceIndex, width: int, height: int) -> bool:
    """Scale-to-cover would enlarge at least one source dimension."""
    return max(width / source.width, height / source.height) > 1.0 + 1e-9


def _safe_ffmpeg_detail(
    stderr: str,
    project: Project,
    out: Path,
) -> str:
    """Keep a useful tail without leaking private absolute paths into the error."""
    detail = stderr.strip()[-400:]
    private_paths = [source.path for source in project.sources]
    if project.music is not None:
        private_paths.append(project.music.track_ref)
    private_paths.append(str(out))
    for private_path in private_paths:
        detail = detail.replace(private_path, Path(private_path).name)
    return detail


class FFmpegRenderer:
    """Render the v2 derived timeline to one local H.264/AAC file."""

    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)

    def export(self, project: Project) -> RenderRecord:
        out = self._render(project, self._out_path(project))
        return RenderRecord(path=str(out), rendered_at=_now_iso(), qa=None)

    def _out_path(self, project: Project) -> Path:
        return self.output_root / project.project_id / output_filename(project)

    def _render(self, project: Project, out: Path) -> Path:
        clips = _timeline_clips(project)
        width, height = _RESOLUTIONS[project.output_resolution]
        total = timeline_duration_s(project)
        if total <= 0:
            raise RenderError("reel has no positive renderable duration")

        for _, source in clips:
            if source.width <= 0 or source.height <= 0:
                raise RenderError(f"source {Path(source.path).name!r} has invalid dimensions")
            if _refuses_upscale(source, width, height):
                raise RenderError(
                    f"upscaling refused for {Path(source.path).name!r}: "
                    f"{source.width}x{source.height} cannot cover {width}x{height}"
                )

        inputs: list[str] = []
        for _, source in clips:
            inputs += ["-i", source.path]

        parts: list[str] = []
        concat_labels: list[str] = []
        piece_number = 0
        for input_number, (clip, source) in enumerate(clips):
            for start, end, rate in _pieces(project, clip):
                duration = (end - start) / rate
                if duration <= 0:
                    continue

                v_label = f"v{piece_number}"
                a_label = f"a{piece_number}"
                # The post-fps trim is the WO-124 clamp: without it setpts/fps
                # adds one or two CFR frames to every ramped piece.
                parts.append(
                    f"[{input_number}:v]"
                    f"trim=start={_number(start)}:end={_number(end)},"
                    f"setpts=(PTS-STARTPTS)/{_number(rate)},"
                    f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                    f"crop={width}:{height},setsar=1,fps={TARGET_FPS},"
                    f"trim=duration={_number(duration)},setpts=PTS-STARTPTS"
                    f"[{v_label}]"
                )

                if source.has_audio and clip.audio.retain:
                    tempo = ",".join(
                        f"atempo={_number(factor)}" for factor in _atempo_chain(rate)
                    )
                    gain = 10 ** (clip.audio.gain_db / 20.0)
                    parts.append(
                        f"[{input_number}:a]"
                        f"atrim=start={_number(start)}:end={_number(end)},"
                        f"asetpts=PTS-STARTPTS,"
                        f"aformat=sample_rates={_SR}:channel_layouts={_LAYOUT},"
                        f"volume={_number(gain)},{tempo},"
                        f"atrim=duration={_number(duration)},asetpts=PTS-STARTPTS"
                        f"[{a_label}]"
                    )
                else:
                    parts.append(
                        f"anullsrc=channel_layout={_LAYOUT}:sample_rate={_SR}:"
                        f"d={_number(duration)}[{a_label}]"
                    )

                concat_labels.append(f"[{v_label}][{a_label}]")
                piece_number += 1

        if not concat_labels:
            raise RenderError("reel has no positive renderable duration")

        parts.append(
            "".join(concat_labels)
            + f"concat=n={len(concat_labels)}:v=1:a=1[vcat][acat]"
        )
        parts.append(
            f"[acat]volume={_number(project.audio.clip_level)}[clipmix]"
        )

        if project.music is not None and project.audio.music_level > 0:
            music_input = len(clips)
            inputs += ["-i", project.music.track_ref]
            parts.append(
                f"[{music_input}:a]"
                f"atrim=start={_number(project.music.in_s)},"
                f"asetpts=PTS-STARTPTS,"
                f"aformat=sample_rates={_SR}:channel_layouts={_LAYOUT},"
                f"volume={_number(project.audio.music_level)}[musicmix]"
            )
            parts.append(
                f"[clipmix][musicmix]"
                f"amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,"
                f"atrim=duration={_number(total)},asetpts=PTS-STARTPTS[aout]"
            )
        else:
            parts.append(
                f"[clipmix]atrim=duration={_number(total)},"
                f"asetpts=PTS-STARTPTS[aout]"
            )

        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            ";".join(parts),
            "-map",
            "[vcat]",
            "-map",
            "[aout]",
            "-t",
            _number(total),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-map_metadata",
            "-1",
            "-map_chapters",
            "-1",
            "-movflags",
            "+faststart",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            detail = _safe_ffmpeg_detail(proc.stderr, project, out)
            raise RenderError(f"ffmpeg render failed: {detail}")
        return out
