"""WO-106 gates · the ES-001 §6 endpoints work end to end through the job
runner, and a failing job surfaces its error rather than hanging."""

from __future__ import annotations

import pytest

from tests.support import AUTH, build_app, wait_job
from tests.synthetic import ffmpeg_available, make_corpus, make_music


def test_failing_job_surfaces_its_error(tmp_path) -> None:
    # No ffmpeg needed: scanning a nonexistent media_root fails in the job thread.
    _, client, _ = build_app(tmp_path)
    created = client.post(
        "/api/project",
        json={"media_root": "/no/such/secret_dir", "track_ref": "/no/such/track.m4a"},
        headers=AUTH,
    )
    assert created.status_code == 200
    pid = created.json()["project_id"]

    job_id = client.post(f"/api/import/{pid}/scan", headers=AUTH).json()["job_id"]
    status = wait_job(client, job_id)
    assert status["state"] == "error"
    assert status["error"]  # surfaced, not hung


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed (ES-001 §3)")
def test_create_scan_export_finalize_end_to_end(tmp_path) -> None:
    media = tmp_path / "media"
    make_corpus(media)
    music = make_music(tmp_path / "bed.m4a")
    _, client, _ = build_app(tmp_path)

    # create
    pid = client.post(
        "/api/project", json={"media_root": str(media), "track_ref": str(music)}, headers=AUTH
    ).json()["project_id"]

    # scan -> sources + default timeline (unreadable surfaced)
    job = client.post(f"/api/import/{pid}/scan", headers=AUTH).json()["job_id"]
    assert wait_job(client, job)["state"] == "done"
    project = client.get(f"/api/project/{pid}").json()
    assert len(project["sources"]) == 4
    assert any(not s["readable"] for s in project["sources"])
    assert len(project["clips"]) == 4

    # proxy serving with range support
    readable = next(s for s in project["sources"] if s["readable"])
    proxy = client.get(f"/api/media/proxy/{readable['source_id']}")
    assert proxy.status_code == 200
    assert proxy.headers.get("accept-ranges") == "bytes"

    # export music -> QA passes -> last_render persisted -> downloadable
    job = client.post(f"/api/export/{pid}", json={"audio_mode": "music"}, headers=AUTH).json()["job_id"]
    assert wait_job(client, job)["state"] == "done"
    project = client.get(f"/api/project/{pid}").json()
    assert "music" in project["export"]["last_render"]
    assert project["export"]["last_render"]["music"]["qa"]["passed"] is True
    assert client.get(f"/api/export/{pid}/download/music").status_code == 200

    # finalize draft -> servable
    job = client.post(f"/api/render/{pid}/finalize", headers=AUTH).json()["job_id"]
    assert wait_job(client, job)["state"] == "done"
    assert client.get(f"/api/render/{pid}/draft").status_code == 200


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed (ES-001 §3)")
def test_analyze_then_propose_writes_explained_proposals(tmp_path) -> None:
    media = tmp_path / "media"
    make_corpus(media)
    music = make_music(tmp_path / "bed.m4a")
    _, client, _ = build_app(tmp_path, with_ai=True)

    pid = client.post(
        "/api/project", json={"media_root": str(media), "track_ref": str(music)}, headers=AUTH
    ).json()["project_id"]
    for path in (f"/api/import/{pid}/scan", f"/api/analyze/{pid}"):
        assert wait_job(client, client.post(path, headers=AUTH).json()["job_id"])["state"] == "done"

    job = client.post(f"/api/propose/trim/{pid}", json={}, headers=AUTH).json()["job_id"]
    assert wait_job(client, job)["state"] == "done"

    project = client.get(f"/api/project/{pid}").json()
    proposed = [c for c in project["clips"] if c["included"] and c["proposals"]["segments"]]
    assert proposed, "expected trim proposals on the included clips"
    for clip in proposed:
        assert clip["origin"]["segments"] == "proposed"
        seg = clip["proposals"]["segments"]
        assert seg["disposition"] == "pending"
        assert seg["reasons"] and all(r["human_text"] and r["evidence_refs"] for r in seg["reasons"])


def test_job_not_found_is_404(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    assert client.get("/api/jobs/nope").status_code == 404


def test_analyze_and_propose_are_501_until_their_lanes_exist(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    pid = client.post(
        "/api/project", json={"media_root": "/m", "track_ref": "/t"}, headers=AUTH
    ).json()["project_id"]
    assert client.post(f"/api/analyze/{pid}", headers=AUTH).status_code == 501
    assert client.post(f"/api/propose/trim/{pid}", headers=AUTH).status_code == 501
