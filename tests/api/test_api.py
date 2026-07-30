"""WO-123 API-v2 routes on synthetic fixtures."""

from __future__ import annotations

import pytest

from tests.support import AUTH, build_app, wait_job
from tests.synthetic import ffmpeg_available, make_clip, make_music

_CREATE = {"media_root": "/no/such/secret_dir", "output_resolution": "1080p", "music_level": 0.0, "clip_level": 0.0}


def _create(client, **overrides):
    body = {**_CREATE, **overrides}
    response = client.post("/api/project", json=body, headers=AUTH)
    assert response.status_code == 200, response.text
    return response.json()


def test_create_patch_and_optimistic_conflict(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    project = _create(client)
    patch = {"updated_at": project["updated_at"], "name": "Synthetic Day", "audio": {"music_level": 0.2, "clip_level": 0.8}}
    saved = client.patch(f"/api/project/{project['project_id']}", json=patch, headers=AUTH)
    assert saved.status_code == 200
    assert saved.json()["name"] == "Synthetic Day"
    stale = client.patch(f"/api/project/{project['project_id']}", json=patch, headers=AUTH)
    assert stale.status_code == 409


def test_failing_scan_job_scrubs_private_path(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    project = _create(client)
    job = client.post(f"/api/import/{project['project_id']}/scan", headers=AUTH).json()["job_id"]
    status = wait_job(client, job)
    assert status["state"] == "error"
    assert "/no/such/secret_dir" not in (status["error"] or "")


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg/ffprobe not installed")
def test_scan_patch_export_download_and_media(tmp_path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    make_clip(media / "portrait.mp4", size="1080x1920", codec="h264", duration=3, with_audio=True)
    track = make_music(tmp_path / "bed.m4a", duration=3)
    _, client, _ = build_app(tmp_path)
    project = _create(client, media_root=str(media), track_ref=str(track), music_level=0.5, clip_level=0.5)
    pid = project["project_id"]
    assert wait_job(client, client.post(f"/api/import/{pid}/scan", headers=AUTH).json()["job_id"])["state"] == "done"
    project = client.get(f"/api/project/{pid}").json()
    clip = project["clips"][0]
    changed = client.patch(f"/api/project/{pid}/clip/{clip['source_id']}", json={"updated_at": project["updated_at"], "segment": {"in_s": 0.0, "out_s": 2.0}, "audio": {"retain": False, "gain_db": 0.0}}, headers=AUTH)
    assert changed.status_code == 200
    assert changed.json()["clips"][0]["origin"]["segments"] == "user"
    exported = wait_job(client, client.post(f"/api/export/{pid}", headers=AUTH).json()["job_id"])
    assert exported["state"] == "done", exported
    project = client.get(f"/api/project/{pid}").json()
    assert project["export"]["last_render"]["qa"]["passed"]
    assert client.get(f"/api/export/{pid}/download").status_code == 200
    assert client.get(f"/api/media/proxy/{clip['source_id']}").status_code == 200
    assert client.get(f"/api/media/peaks/{pid}/{clip['source_id']}").status_code == 200


def test_removed_v1_routes_are_not_present_and_new_mutations_require_token(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    project = _create(client)
    pid = project["project_id"]
    assert client.post(f"/api/project/{pid}/approve/ingest", headers=AUTH).status_code == 404
    assert client.post(f"/api/render/{pid}/finalize", headers=AUTH).status_code == 404
    assert client.post(f"/api/export/{pid}").status_code == 401
    assert client.post("/api/pick-file").status_code == 401


def test_proposal_routes_are_clear_when_services_are_absent(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    project = _create(client)
    pid = project["project_id"]
    assert client.post(f"/api/analyze/{pid}", headers=AUTH).status_code == 501
    assert client.post(f"/api/propose/trim/{pid}", headers=AUTH).status_code == 501
    assert client.post(f"/api/propose/speed/{pid}", headers=AUTH).status_code == 501
