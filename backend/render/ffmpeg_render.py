"""FFmpeg render/export for M1: 1080×1920 centre-crop concat, three audio modes.

Video (§8.1): per included, non-deleted clip in order — trim to the segment,
rebase PTS, scale-to-cover then centre-crop to 1080×1920, normalise to 30 fps,
then concat. Audio (§8.2):
  * music  — the supplied track as the bed, no clip audio; -shortest to video len
  * clip   — natural clip audio concatenated, a silent pad for any has_audio=False
             clip so streams stay aligned
  * silent — a valid silent AAC track
One loudness-normalisation pass per mode. All segments are rate 1.0 in M1.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from backend.contracts.models import AudioMode, Project, RenderRecord

TARGET_W, TARGET_H, TARGET_FPS = 1080, 1920, 30
_SR, _LAYOUT = 48000, "stereo"


class RenderError(Exception):
    """The render pipeline failed or the timeline is empty."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _timeline_clips(project: Project):
    clips = [c for c in project.clips if c.included and not c.deleted]
    clips.sort(key=lambda c: c.order)
    if not clips:
        raise RenderError("timeline is empty: no included, non-deleted clips")
    by_id = {s.source_id: s for s in project.sources}
    out = []
    for c in clips:
        src = by_id.get(c.source_id)
        if src is None:
            raise RenderError(f"clip references unknown source {c.source_id!r}")
        if not c.segments:
            raise RenderError(f"clip {c.source_id!r} has no segment")
        seg = c.segments[0]  # v1 UI enforces exactly one segment (§11)
        out.append((src, seg))
    return out


def timeline_duration_s(project: Project) -> float:
    return sum(seg.out_s - seg.in_s for _, seg in _timeline_clips(project))


def output_filename(project: Project, label: str) -> str:
    """Deterministic output basename, shared by the renderer and the API layer."""
    stem = (project.name or "reel").strip().replace(" ", "-").lower() or "reel"
    return f"{stem}-{label}.mp4"


class FFmpegRenderer:
    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)

    # --- Renderer interface ----------------------------------------------

    def render_draft(self, project: Project) -> str:
        return str(self._render(project, "silent", self._out_path(project, "draft")))

    def export(self, project: Project, audio_mode: AudioMode) -> RenderRecord:
        path = self._render(project, audio_mode, self._out_path(project, audio_mode))
        return RenderRecord(path=str(path), rendered_at=_now_iso(), qa=None)

    # --- internal ---------------------------------------------------------

    def _out_path(self, project: Project, label: str) -> Path:
        return self.output_root / project.project_id / output_filename(project, label)

    def _render(self, project: Project, audio_mode: AudioMode, out: Path) -> Path:
        clips = _timeline_clips(project)
        n = len(clips)
        inputs: list[str] = []
        for src, _ in clips:
            inputs += ["-i", src.path]

        parts: list[str] = []
        for k, (_, seg) in enumerate(clips):
            parts.append(
                f"[{k}:v]trim=start={seg.in_s}:end={seg.out_s},setpts=PTS-STARTPTS,"
                f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,"
                f"crop={TARGET_W}:{TARGET_H},setsar=1,fps={TARGET_FPS}[v{k}]"
            )
        parts.append("".join(f"[v{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[vout]")

        extra_args: list[str] = []
        if audio_mode == "music":
            music_idx = n
            inputs += ["-i", project.music.track_ref]
            parts.append(f"[{music_idx}:a]aformat=sample_rates={_SR}:channel_layouts={_LAYOUT},loudnorm[aout]")
            extra_args = ["-shortest"]
        elif audio_mode == "clip":
            all_silent = all(not src.has_audio for src, _ in clips)
            for k, (src, seg) in enumerate(clips):
                dur = round(seg.out_s - seg.in_s, 3)
                if src.has_audio:
                    parts.append(
                        f"[{k}:a]atrim=start={seg.in_s}:end={seg.out_s},asetpts=PTS-STARTPTS,"
                        f"aformat=sample_rates={_SR}:channel_layouts={_LAYOUT}[a{k}]"
                    )
                else:  # silent pad keeps the concatenation aligned (§8.2)
                    parts.append(f"anullsrc=channel_layout={_LAYOUT}:sample_rate={_SR}:d={dur}[a{k}]")
            parts.append("".join(f"[a{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1[acat]")
            # loudnorm on pure digital silence yields NaN samples the AAC encoder
            # rejects; an all-audio-less reel is correctly silent and needs none.
            parts.append(f"[acat]{'anull' if all_silent else 'loudnorm'}[aout]")
        elif audio_mode == "silent":
            total = round(timeline_duration_s(project), 3)
            parts.append(f"anullsrc=channel_layout={_LAYOUT}:sample_rate={_SR}:d={total}[aout]")
        else:  # pragma: no cover - AudioMode is a closed Literal
            raise RenderError(f"unknown audio_mode {audio_mode!r}")

        filter_complex = ";".join(parts)
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = (
            ["ffmpeg", "-y", *inputs, "-filter_complex", filter_complex,
             "-map", "[vout]", "-map", "[aout]",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
             "-movflags", "+faststart", *extra_args, str(out)]
        )
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RenderError(f"ffmpeg render failed ({audio_mode}): {proc.stderr.strip()[-400:]}")
        return out
