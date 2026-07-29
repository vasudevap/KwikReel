"""WO-124 follow-up · Does the setpts duration overshoot accumulate? THROWAWAY.

The spike measured a +0.42%..+1.39% overshoot at one clip length (12 s) and
reported it as a percentage. A percentage implies it scales with duration —
which would mean a long ramped reel drifts badly. The frame counts suggest
something else: quantisation to a fixed output frame rate, bounded at 1–2
frames regardless of how long the clip is.

Those two models give completely different answers for SPEC.md §9's ±0.5 s QA
tolerance, so this measures which one is true instead of arguing about it.

    python spike/wo-124-playback/setpts_duration.py
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

FPS = 30
DURATIONS = [2, 6, 12, 30]
RATES = [1.0, 1.5, 2.0, 2.5]


def _probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-count_frames", "-show_entries", "stream=nb_read_frames,duration,r_frame_rate",
         "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    d = json.loads(out.stdout)
    s = d["streams"][0]
    return {
        "frames": int(s["nb_read_frames"]),
        "stream_duration_s": float(s.get("duration", 0)),
        "format_duration_s": float(d["format"]["duration"]),
        "fps": s["r_frame_rate"],
    }


def _source(path: Path, seconds: int) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"testsrc=size=320x568:rate={FPS}:duration={seconds}",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
         "-c:v", "libx264", "-crf", "28", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", str(path)],
        capture_output=True, check=True,
    )


def _render(src: Path, out: Path, rate: float, *, extra: list[str] | None = None) -> None:
    if rate == 1.0:
        filt = "[0:v]copy[v];[0:a]anull[a]"
    else:
        chain = f"atempo={min(rate, 2.0)}"
        if rate > 2.0:
            chain += f",atempo={rate / 2.0}"
        filt = f"[0:v]setpts=PTS/{rate}[v];[0:a]{chain}[a]"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-filter_complex", filt,
         "-map", "[v]", "-map", "[a]", *(extra or []),
         "-c:v", "libx264", "-crf", "28", "-pix_fmt", "yuv420p",
         "-c:a", "aac", str(out)],
        capture_output=True, check=True,
    )


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="setpts-"))
    print(f"working in {tmp}\n")

    print("Q1 · Does the overshoot grow with clip duration?")
    print(f"{'src_s':>6} {'rate':>5} {'want_frames':>12} {'got':>6} {'d_frames':>9} "
          f"{'want_s':>8} {'got_s':>8} {'over_ms':>8} {'over_%':>7}")
    model = {}
    for secs in DURATIONS:
        src = tmp / f"src_{secs}.mp4"
        _source(src, secs)
        for rate in RATES:
            out = tmp / f"o_{secs}_{rate}.mp4"
            _render(src, out, rate)
            p = _probe(out)
            want_frames = secs * FPS / rate
            want_s = secs / rate
            over_ms = (p["format_duration_s"] - want_s) * 1000
            print(f"{secs:>6} {rate:>5} {want_frames:>12.1f} {p['frames']:>6} "
                  f"{p['frames'] - want_frames:>+9.1f} {want_s:>8.3f} "
                  f"{p['format_duration_s']:>8.3f} {over_ms:>+8.1f} "
                  f"{(over_ms / 10 / want_s):>+7.2f}")
            model.setdefault(rate, []).append((secs, over_ms))

    print("\nQ1 verdict — overshoot in ms by source duration, per rate:")
    for rate, rows in model.items():
        vals = ", ".join(f"{s}s:{ms:+.0f}ms" for s, ms in rows)
        spread = max(ms for _, ms in rows) - min(ms for _, ms in rows)
        verdict = "CONSTANT (quantisation)" if spread < 20 else "GROWS (proportional)"
        print(f"  {rate}x  {vals}   spread={spread:.0f}ms  -> {verdict}")

    print("\nQ2 · Does forcing CFR output or passthrough change it? (12 s source)")
    src = tmp / "src_12.mp4"
    for label, extra in [
        ("default", []),
        ("-r 30", ["-r", "30"]),
        ("-fps_mode passthrough", ["-fps_mode", "passthrough"]),
        ("-fps_mode cfr -r 30", ["-fps_mode", "cfr", "-r", "30"]),
    ]:
        out = tmp / f"m_{abs(hash(label))}.mp4"
        try:
            _render(src, out, 2.0, extra=extra)
            p = _probe(out)
            print(f"  {label:<24} frames={p['frames']:>4} dur={p['format_duration_s']:.4f}s "
                  f"over={(p['format_duration_s'] - 6.0) * 1000:+.1f}ms")
        except subprocess.CalledProcessError as e:
            print(f"  {label:<24} FAILED: {e.stderr.decode()[-120:].strip()}")

    print("\nQ3 · Does it compound across a concat? (6 clips, 6 s each, all at 2x)")
    parts = []
    for i in range(6):
        out = tmp / f"c_{i}.mp4"
        _render(tmp / "src_6.mp4", out, 2.0)
        parts.append(out)
    listing = tmp / "concat.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in parts))
    joined = tmp / "joined.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", str(joined)],
        capture_output=True, check=True,
    )
    p = _probe(joined)
    per = _probe(parts[0])
    want = 6 * 3.0
    print(f"  one part:  {per['format_duration_s']:.4f}s "
          f"(want 3.000, over {(per['format_duration_s'] - 3) * 1000:+.1f}ms)")
    print(f"  6 concat:  {p['format_duration_s']:.4f}s (want {want:.3f}, "
          f"over {(p['format_duration_s'] - want) * 1000:+.1f}ms)")
    print(f"  -> per-clip error {'ACCUMULATES' if abs(p['format_duration_s'] - want) > 0.1 else 'does NOT fully accumulate'}")
    print(f"\n  SPEC.md §9 tolerance is ±0.5 s. This reel is "
          f"{'INSIDE' if abs(p['format_duration_s'] - want) <= 0.5 else 'OUTSIDE'} it.")


if __name__ == "__main__":
    main()
