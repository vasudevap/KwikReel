"""WO-123a focused API gates for the corrected frontend seam."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support import AUTH, build_app, wait_job
from tests.synthetic import ffmpeg_available, make_clip, make_music


def _create(client, media_root: Path, **overrides) -> dict:
    response = client.post(
        "/api/project",
        json={
            "media_root": str(media_root),
            "output_resolution": "1080p",
            "music_level": 0.0,
            "clip_level": 0.0,
            **overrides,
        },
        headers=AUTH,
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_music_probe_and_peaks_work_before_project_exists(tmp_path) -> None:
    track = make_music(tmp_path / "bed.m4a", duration=2)
    _, client, _ = build_app(tmp_path)

    response = client.post(
        "/api/music/probe",
        json={"track_ref": str(track)},
        headers=AUTH,
    )
    assert response.status_code == 200, response.text
    music = response.json()
    assert music["track_ref"] == str(track)
    assert len(music["content_hash"]) == 64
    assert music["duration_s"] == pytest.approx(2.0, abs=0.1)
    assert music["in_s"] == 0.0

    peaks = client.get(
        "/api/music/peaks",
        params={"track_ref": music["track_ref"], "content_hash": music["content_hash"]},
    )
    assert peaks.status_code == 200
    assert peaks.json()["peaks"]

    project = _create(client, tmp_path / "media", track_ref=str(track))
    log = client.get(f"/api/project/{project['project_id']}/log").json()
    assert any(item["code"] == "MUSIC_SELECTED" for item in log)


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_bin_restore_and_hash_repair_preserve_edit_state_and_root_boundary(tmp_path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    original = make_clip(
        media / "original.mp4",
        size="320x568",
        codec="h264",
        duration=2,
        with_audio=True,
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    _, client, _ = build_app(tmp_path)
    project = _create(client, media)
    pid = project["project_id"]

    scan = client.post(f"/api/import/{pid}/scan", headers=AUTH).json()["job_id"]
    assert wait_job(client, scan)["state"] == "done"
    project = client.get(f"/api/project/{pid}").json()
    source_id = project["sources"][0]["source_id"]

    edited = client.patch(
        f"/api/project/{pid}/clip/{source_id}",
        json={
            "updated_at": project["updated_at"],
            "segment": {"in_s": 0.25, "out_s": 1.5},
            "audio": {"retain": False, "gain_db": -2.0},
        },
        headers=AUTH,
    ).json()
    prior_clip = edited["clips"][0]

    binned = client.post(
        f"/api/project/{pid}/clip/{source_id}/bin",
        json={"updated_at": edited["updated_at"]},
        headers=AUTH,
    )
    assert binned.status_code == 200
    assert binned.json()["clips"][0]["segment"] == {"in_s": 0.0, "out_s": 0.0}
    assert binned.json()["clips"][0]["stashed_segment"] == prior_clip["segment"]
    stale = client.post(
        f"/api/project/{pid}/clip/{source_id}/bin",
        json={"updated_at": edited["updated_at"]},
        headers=AUTH,
    )
    assert stale.status_code == 409

    restored = client.post(
        f"/api/project/{pid}/clip/{source_id}/bin",
        json={"updated_at": binned.json()["updated_at"]},
        headers=AUTH,
    ).json()
    assert restored["clips"][0]["segment"] == prior_clip["segment"]
    assert restored["clips"][0]["audio"] == prior_clip["audio"]
    assert restored["clips"][0]["origin"] == prior_clip["origin"]

    nested = media / "moved"
    nested.mkdir()
    moved = nested / "renamed.mp4"
    original.rename(moved)
    repaired = client.post(
        f"/api/project/{pid}/repair-links",
        json={"updated_at": restored["updated_at"]},
        headers=AUTH,
    )
    assert repaired.status_code == 200, repaired.text
    repaired_project = repaired.json()
    assert repaired_project["sources"][0]["source_id"] == source_id
    assert repaired_project["sources"][0]["path"] == str(moved.resolve())
    assert repaired_project["clips"][0] == restored["clips"][0]

    outside_match = outside / "same-bytes.mp4"
    moved.rename(outside_match)
    missed = client.post(
        f"/api/project/{pid}/repair-links",
        json={"updated_at": repaired_project["updated_at"]},
        headers=AUTH,
    )
    assert missed.status_code == 200
    assert missed.json()["sources"][0]["path"] == str(moved.resolve())
    assert str(outside_match) not in missed.text

    codes = [item["code"] for item in client.get(f"/api/project/{pid}/log").json()]
    assert "CLIP_BINNED" in codes
    assert "CLIP_RESTORED" in codes
    assert "SOURCE_REPAIRED" in codes
    assert "SOURCE_UNLINKED" in codes
