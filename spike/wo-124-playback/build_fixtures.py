"""WO-124 · Build the spike's fixtures. THROWAWAY — deleted at ADP-002 closeout.

The spike has to answer `SPEC.md` §6 with numbers, and every number depends on
being able to say *exactly which frame the browser is showing*. Timecode burned
in as text would need OCR; a colour gradient does not survive yuv420p chroma
subsampling and H.264 quantisation.

So each frame carries a **9-bit binary code in nine large black/white blocks**.
Big flat blocks are the one thing H.264 preserves faithfully at any sane
bitrate, and reading them back is a threshold on nine pixels. 9 bits wraps at
512 frames, which at 30 fps is 17 s — longer than any spike clip.

Proxies are built by calling the REAL `FFmpegIngest.make_proxy`. Building them
with a hand-rolled ffmpeg line would measure a GOP the application never
produces, and the proxy's keyframe interval is precisely what §6 asks about.

    python spike/wo-124-playback/build_fixtures.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "media"

FPS = 30
DURATION_S = 12
SIZE = (1080, 1920)          # w, h — portrait, the app's native orientation
LANDSCAPE = (1920, 1080)

# Nine code blocks across the top of the frame, each 1/3 of the width.
CODE_COLS, CODE_ROWS = 3, 3


def _frame(idx: int, w: int, h: int, tint: tuple[int, int, int]) -> np.ndarray:
    """One frame: a clip-identifying tint, plus `idx` in nine binary blocks."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :] = tint

    bw, bh = w // CODE_COLS, h // (CODE_ROWS * 3)   # code band is the top third
    for bit in range(CODE_COLS * CODE_ROWS):
        r, c = divmod(bit, CODE_COLS)
        on = (idx >> bit) & 1
        y0, x0 = r * bh, c * bw
        img[y0:y0 + bh, x0:x0 + bw] = (255, 255, 255) if on else (0, 0, 0)

    # Human-readable, for eyeballing a screenshot. Not what the harness reads.
    cv2.putText(img, str(idx), (w // 8, int(h * 0.7)),
                cv2.FONT_HERSHEY_SIMPLEX, w / 200, (255, 255, 255), max(2, w // 120))
    return img


def _write_source(path: Path, *, w: int, h: int, tint: tuple[int, int, int],
                  with_audio: bool, freq: int) -> None:
    """Encode a source clip frame-by-frame through ffmpeg's rawvideo stdin."""
    n = FPS * DURATION_S
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
    ]
    if with_audio:
        # A steady tone: a pitch shift in preview-vs-export is then measurable
        # as a frequency, not a matter of opinion.
        cmd += ["-f", "lavfi", "-i", f"sine=frequency={freq}:duration={DURATION_S}"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    if with_audio:
        cmd += ["-c:a", "aac", "-shortest"]
    cmd += [str(path)]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    assert proc.stdin is not None
    for i in range(n):
        proc.stdin.write(_frame(i, w, h, tint).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f"encode failed for {path.name}:\n{proc.stderr.read().decode()[:400]}")


def _gop(path: Path) -> dict:
    """Keyframe positions — the thing seek latency actually depends on."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "frame=pts_time,key_frame", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    frames = json.loads(out.stdout).get("frames", [])
    keys = [float(f["pts_time"]) for f in frames if f.get("key_frame") == 1]
    gaps = [round(b - a, 3) for a, b in zip(keys, keys[1:])]
    return {
        "frames": len(frames),
        "keyframes": len(keys),
        "keyframe_times_s": [round(k, 3) for k in keys],
        "max_gap_s": max(gaps) if gaps else None,
        "mean_gap_s": round(sum(gaps) / len(gaps), 3) if gaps else None,
    }


def _has_audio(path: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return bool(out.stdout.strip())


def main() -> None:
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        raise SystemExit("ffmpeg/ffprobe required")
    sys.path.insert(0, str(ROOT.parents[1]))
    from backend.contracts.models import SourceIndex          # noqa: E402
    from backend.ingest.ffmpeg_ingest import FFmpegIngest      # noqa: E402

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "src").mkdir(parents=True)

    specs = [
        ("c1", SIZE,      (40, 20, 90),  440),
        ("c2", LANDSCAPE, (20, 80, 40),  660),   # landscape: gets letterboxed
        ("c3", SIZE,      (90, 40, 20),  880),
    ]
    report: dict = {"fps": FPS, "duration_s": DURATION_S, "clips": {}}

    for name, (w, h), tint, freq in specs:
        src = OUT / "src" / f"{name}.mp4"
        print(f"  encoding {name} ({w}x{h}) …")
        _write_source(src, w=w, h=h, tint=tint, with_audio=True, freq=freq)

        # The real path, so the GOP is the application's GOP.
        ingest = FFmpegIngest(proxy_root=OUT / "proxies")
        source = ingest.probe_clip(str(src))
        proxy = Path(ingest.make_proxy(source))

        report["clips"][name] = {
            "source": {
                "path": str(src.relative_to(OUT)), "w": w, "h": h,
                "tone_hz": freq, "has_audio": _has_audio(src), "gop": _gop(src),
            },
            "proxy": {
                "path": str(proxy.relative_to(OUT)),
                "has_audio": _has_audio(proxy),
                "gop": _gop(proxy),
            },
        }
        print(f"    proxy {proxy.name}: {report['clips'][name]['proxy']['gop']['keyframes']} keyframes, "
              f"audio={report['clips'][name]['proxy']['has_audio']}")

    # Reference exports: what the RENDERER produces for a speed ramp, so the
    # browser's playbackRate can be compared against it rather than guessed at.
    print("  rendering setpts/atempo references …")
    refs = {}
    for rate in (1.5, 1.75, 2.0, 2.5):
        ref = OUT / f"ref_rate_{str(rate).replace('.', '_')}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(OUT / "src" / "c1.mp4"),
             "-filter_complex",
             f"[0:v]setpts=PTS/{rate}[v];[0:a]atempo={min(rate, 2.0)}"
             + (f",atempo={rate / 2.0}" if rate > 2.0 else "") + "[a]",
             "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18",
             "-pix_fmt", "yuv420p", "-c:a", "aac", str(ref)],
            capture_output=True, text=True, check=True,
        )
        dur = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(ref)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        refs[str(rate)] = {
            "path": ref.name,
            "duration_s": round(float(dur), 4),
            "expected_s": round(DURATION_S / rate, 4),
            "atempo_chained": rate > 2.0,
        }
        print(f"    {rate}x -> {refs[str(rate)]['duration_s']}s "
              f"(expected {refs[str(rate)]['expected_s']}s)")
    report["setpts_reference"] = refs

    # A music bed, for the sync measurements.
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=60",
         "-c:a", "aac", str(OUT / "music.m4a")],
        capture_output=True, check=True,
    )

    (OUT / "fixtures.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nwrote {OUT / 'fixtures.json'}")


if __name__ == "__main__":
    main()
