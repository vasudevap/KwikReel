"""C-4/6 · Renderer & exporter (WO-104). Draft render and per-audio-mode export.

`FFmpegRenderer` satisfies the `Renderer` interface (WO-101). Implements ES-001
§8.1 (trim → setpts → scale/centre-crop to 1080×1920 → concat) and §8.2 audio
modes (music | clip | silent), one loudness pass per mode. No speed ramps beyond
rate 1.0 (M3), no ducking (M2+), no network. Originals are read-only.
"""

from backend.render.ffmpeg_render import FFmpegRenderer, RenderError

__all__ = ["FFmpegRenderer", "RenderError"]
