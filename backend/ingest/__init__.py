"""C-1 · Ingest & proxy (WO-102). Probe sources, build preview proxies.

`FFmpegIngest` satisfies the `IngestService` interface (WO-101). Originals under
`media_root` are opened read-only — no code path here writes, moves, or deletes
beneath it (ES-001 §9). Proxies land in a separate derived directory. Unreadable
sources are retained with `readable=False`, never silently dropped.
"""

from backend.ingest.ffmpeg_ingest import FFmpegIngest, ProbeError

__all__ = ["FFmpegIngest", "ProbeError"]
