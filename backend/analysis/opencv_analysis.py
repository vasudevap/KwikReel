"""OpenCV + ffmpeg per-second signal extraction (ES-001 §5.1, normalised 0..1).

Video signals come from the proxy (fast); audio RMS from the original (the proxy
is silent), read-only. All signals are normalised to 0..1 so the proposer's fixed
floors apply (the reference constants are config and tunable). Facts only — no
editorial decisions here.

The proxy is **letterboxed** into 540×960, so its black bars are cropped off
before anything is measured — see `_content_rect`. Measuring the padded frame
made every landscape clip read as catastrophically clipped.
"""

from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from backend.contracts.models import Analysis, Signals, SourceIndex


@dataclass(frozen=True)
class AnalysisConfig:
    samples_per_sec: int = 4
    sharp_ref: float = 200.0     # Laplacian variance mapped to ~1.0
    shake_ref: float = 20.0      # global shift (px) mapped to ~1.0
    motion_ref: float = 15.0     # mean abs inter-frame diff mapped to ~1.0
    cut_threshold: float = 0.5   # normalised motion above this = a scene cut
    proc_size: int = 128         # downscale for motion/shake


class AnalysisError(Exception):
    """The clip could not be opened for analysis."""


def _clamp01(values: list[float], n: int) -> list[float]:
    out = list(values[:n]) + [0.0] * max(0, n - len(values))
    return [float(min(max(v, 0.0), 1.0)) for v in out]


def _content_rect(frame_h: int, frame_w: int, source: SourceIndex) -> tuple[int, int, int, int] | None:
    """Where the real picture sits inside a letterboxed proxy, or None.

    `make_proxy` scales the source into 540×960 preserving aspect ratio and
    centre-pads the rest with black. Those bars are pixel value 0, and exposure
    counts pixels at `<= 8` as clipped — so measured over the padded frame a
    16:9 clip reads ~0.68 exposed before any content is considered, clearing the
    0.50 ceiling on every second and coming back OVEREXPOSED.

    The rect is derived from the source's own aspect ratio rather than detected
    from pixels, because bar detection cannot tell a black bar from a genuinely
    dark frame — and a dark frame is exactly the case the exposure signal exists
    to catch. `SourceIndex.width/height` are rotation-corrected, matching what
    ffmpeg's scaler saw.
    """
    sw, sh = source.width, source.height
    if sw <= 0 or sh <= 0:
        return None
    scale = min(frame_w / sw, frame_h / sh)
    # One pixel of inset each side: ffmpeg rounds the scaled size to even
    # dimensions and the scaler softens the content/bar boundary, so the
    # outermost row or column can be part bar.
    x0 = int(round((frame_w - sw * scale) / 2)) + 1
    y0 = int(round((frame_h - sh * scale) / 2)) + 1
    x1, y1 = frame_w - x0, frame_h - y0
    if x1 - x0 < 16 or y1 - y0 < 16:
        return None    # implausible geometry — measure the whole frame instead
    return y0, y1, x0, x1


class OpenCVAnalysis:
    def __init__(self, config: AnalysisConfig | None = None) -> None:
        self.config = config or AnalysisConfig()

    def analyze(self, source: SourceIndex) -> Analysis:
        n = max(1, round(source.duration_s)) if source.duration_s > 0 else 1
        # Only the proxy is letterboxed; the original is measured as-is.
        video_path = source.proxy_path or source.path
        letterboxed = source if source.proxy_path else None
        blur, exposure, shake, motion, cuts = self._video_signals(video_path, n, letterboxed)
        audio = self._audio_rms(source.path, n) if source.has_audio else [0.0] * n
        return Analysis(
            source_id=source.source_id,
            signals=Signals(
                blur=_clamp01(blur, n),
                exposure=_clamp01(exposure, n),
                shake=_clamp01(shake, n),
                motion_energy=_clamp01(motion, n),
                audio_rms=_clamp01(audio, n),
                people_count=None,   # M2
                saliency_ref=None,   # deferred
            ),
            scene_cuts_s=cuts,
            dup_group=None,          # cross-clip dedup not wired for M1 trim
            run_id=f"an-{source.content_hash[:12]}",
        )

    # --- internals --------------------------------------------------------

    def _video_signals(self, path: str, n: int, letterboxed: SourceIndex | None = None):
        c = self.config
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise AnalysisError(f"cannot open video for analysis: {Path(path).name}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0 or math.isnan(fps):
            fps = 30.0
        step = max(1, int(round(fps / c.samples_per_sec)))

        sharp = [[] for _ in range(n)]
        expo = [[] for _ in range(n)]
        motion = [[] for _ in range(n)]
        shake = [[] for _ in range(n)]
        cuts: list[float] = []

        han = cv2.createHanningWindow((c.proc_size, c.proc_size), cv2.CV_32F)
        prev_small: np.ndarray | None = None
        crop: tuple[int, int, int, int] | None = None
        cropped = False
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step != 0:
                idx += 1
                continue
            t = idx / fps
            sec = min(int(t), n - 1)
            if letterboxed is not None and not cropped:
                crop = _content_rect(frame.shape[0], frame.shape[1], letterboxed)
                cropped = True    # geometry is fixed for the file; compute once
            if crop is not None:
                y0, y1, x0, x1 = crop
                frame = frame[y0:y1, x0:x1]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            sharp[sec].append(min(cv2.Laplacian(gray, cv2.CV_64F).var() / c.sharp_ref, 1.0))
            clipped = int(np.count_nonzero(gray <= 8) + np.count_nonzero(gray >= 247))
            expo[sec].append(clipped / gray.size)

            small = cv2.resize(gray, (c.proc_size, c.proc_size)).astype(np.float32)
            if prev_small is not None:
                mad = float(np.mean(np.abs(small - prev_small)))
                m_norm = min(mad / c.motion_ref, 1.0)
                motion[sec].append(m_norm)
                try:
                    (dx, dy), _ = cv2.phaseCorrelate(prev_small * han, small * han)
                except cv2.error:
                    dx = dy = 0.0
                if math.isnan(dx) or math.isnan(dy):
                    dx = dy = 0.0
                shake[sec].append(min(math.hypot(dx, dy) / c.shake_ref, 1.0))
                if m_norm >= c.cut_threshold:
                    cuts.append(round(t, 2))
            prev_small = small
            idx += 1
        cap.release()

        def per_second(buckets: list[list[float]]) -> list[float]:
            return [(sum(b) / len(b)) if b else 0.0 for b in buckets]

        return per_second(sharp), per_second(expo), per_second(shake), per_second(motion), _dedup_cuts(cuts)

    def _audio_rms(self, path: str, n: int) -> list[float]:
        proc = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a?", "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
            capture_output=True,
        )
        if proc.returncode != 0 or not proc.stdout:
            return [0.0] * n
        data = np.frombuffer(proc.stdout, dtype=np.float32)
        sr = 8000
        rms = []
        for s in range(n):
            chunk = data[s * sr:(s + 1) * sr]
            rms.append(float(np.sqrt(np.mean(np.square(chunk)))) if chunk.size else 0.0)
        return rms


def _dedup_cuts(cuts: list[float]) -> list[float]:
    out: list[float] = []
    for t in sorted(cuts):
        if t < 0.5:
            continue
        if out and t - out[-1] < 1.0:
            continue
        out.append(t)
    return out
