"""ES-001 §10 internal checkpoint (ADR-007) · Import → curate → store → render →
export, end to end through the real services against a synthetic media_root.

This is the milestone that must pass BEFORE the trim proposer is built — the
renderer and the proposer are never debugged simultaneously. It also stands in
for the WO-114 integration lane's happy path on synthetic fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.contracts.models import (
    Clip,
    Export,
    Music,
    Origin,
    Project,
    Proposals,
    Segment,
    StageApprovals,
)
from backend.ingest import FFmpegIngest
from backend.qa import FFmpegOutputQA
from backend.render import FFmpegRenderer
from backend.store import FileProjectStore
from tests.synthetic import ffmpeg_available, make_corpus, make_music

pytestmark = pytest.mark.skipif(
    not ffmpeg_available(), reason="ffmpeg/ffprobe not installed (ES-001 §3 dependency)"
)


def test_import_curate_store_render_export_end_to_end(tmp_path) -> None:
    media_root = tmp_path / "media"
    make_corpus(media_root)
    music = make_music(tmp_path / "bed.m4a")

    ingest = FFmpegIngest(proxy_root=tmp_path / "proxies")
    store = FileProjectStore(tmp_path / "store")
    renderer = FFmpegRenderer(output_root=tmp_path / "out")
    qa = FFmpegOutputQA()

    # 1) Import: probe the folder. Unreadable sources are surfaced, not dropped.
    sources = ingest.build_source_index(str(media_root))
    assert any(s.readable for s in sources) and any(not s.readable for s in sources)

    # Proxies for the readable sources land outside media_root (read-only originals).
    for s in sources:
        if s.readable:
            proxy = Path(ingest.make_proxy(s))
            assert proxy.exists() and media_root not in proxy.parents

    # 2) Curate by hand: include readable, exclude the unreadable one (G-4).
    #    order is dense across ALL non-deleted clips (included or not).
    clips = [
        Clip(
            source_id=s.source_id,
            included=s.readable,
            order=i,
            deleted=False,
            segments=[Segment(in_s=0.0, out_s=1.0, speed=[])],
            origin=Origin(included="user" if not s.readable else "default"),
            proposals=Proposals(),
        )
        for i, s in enumerate(sources, start=1)
    ]
    project = Project(
        schema_version=1,
        project_id="checkpoint",
        created_at="2026-07-24T20:00:00Z",
        updated_at="2026-07-24T20:00:00Z",
        app_version="0.1.0",
        name="Checkpoint Day",
        media_root=str(media_root),
        target_duration_s=75.0,
        music=Music(track_ref=str(music), content_hash="sha256:music", duration_s=12.0),
        sources=sources,
        clips=clips,
        stage_approvals=StageApprovals(ingest="2026-07-24T20:01:00Z"),
        export=Export(audio_modes=["music", "clip", "silent"], last_render={}),
    )

    # 3) Store: save, reload, byte-equivalent.
    saved = store.save(project)
    reloaded = store.load("checkpoint")
    assert reloaded == saved

    # 4) Render + export every audio mode; QA must pass each. last_render becomes a
    #    per-mode map (G-5); a machine could then persist it via the store.
    for mode in ("music", "clip", "silent"):
        record = renderer.export(saved, mode)
        report = qa.validate_render(record.path, saved, mode)
        assert report.passed, f"{mode}: {report.reasons}"
        assert (report.width, report.height) == (1080, 1920)
        saved.export.last_render[mode] = record.model_copy(update={"qa": report})

    # The pipe works end to end: three included clips (~3 s), all three modes pass QA.
    assert set(saved.export.last_render) == {"music", "clip", "silent"}
    persisted = store.save(saved)
    assert set(persisted.export.last_render) == {"music", "clip", "silent"}
