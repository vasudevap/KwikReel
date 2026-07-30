"""WO-123a synthetic v2 flow through every frontend-operability seam."""

from __future__ import annotations

import pytest

from tests.support import AUTH, build_app, wait_job
from tests.synthetic import ffmpeg_available, make_clip, make_music

pytestmark = pytest.mark.skipif(
    not ffmpeg_available(),
    reason="ffmpeg/ffprobe not installed",
)


def _job(client, path: str, body: dict | None = None) -> None:
    response = client.post(path, json=body, headers=AUTH)
    assert response.status_code == 200, response.text
    result = wait_job(client, response.json()["job_id"])
    assert result["state"] == "done", result


def test_v2_create_scan_analyse_propose_control_export_and_log(tmp_path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    make_clip(
        media / "synthetic.mp4",
        size="720x1280",
        codec="h264",
        duration=3,
        with_audio=True,
    )
    music_path = make_music(tmp_path / "bed.m4a", duration=4)
    _, client, _ = build_app(tmp_path, with_ai=True)

    probed = client.post(
        "/api/music/probe",
        json={"track_ref": str(music_path)},
        headers=AUTH,
    )
    assert probed.status_code == 200
    assert client.get(
        "/api/music/peaks",
        params={
            "track_ref": probed.json()["track_ref"],
            "content_hash": probed.json()["content_hash"],
        },
    ).json()["peaks"]

    created = client.post(
        "/api/project",
        json={
            "media_root": str(media),
            "output_resolution": "720p",
            "music_level": 0.3,
            "clip_level": 0.7,
            "target_duration_s": 15,
            "track_ref": str(music_path),
        },
        headers=AUTH,
    )
    assert created.status_code == 200, created.text
    pid = created.json()["project_id"]

    _job(client, f"/api/import/{pid}/scan")
    _job(client, f"/api/analyze/{pid}")
    _job(client, f"/api/propose/trim/{pid}", {})
    _job(client, f"/api/propose/speed/{pid}", {})

    project = client.get(f"/api/project/{pid}").json()
    source_id = project["clips"][0]["source_id"]
    proposal = project["clips"][0]["proposals"]["segments"]
    assert proposal is not None
    assert proposal["reasons"]

    rejected = client.post(
        f"/api/project/{pid}/clip/{source_id}/reject-trim",
        json={"updated_at": project["updated_at"]},
        headers=AUTH,
    )
    assert rejected.status_code == 200
    assert rejected.json()["clips"][0]["proposals"]["segments"]["disposition"] == "dismissed"
    assert client.post(
        f"/api/project/{pid}/clip/{source_id}/reject-trim",
        json={"updated_at": project["updated_at"]},
        headers=AUTH,
    ).status_code == 409

    _job(client, f"/api/propose/trim/{pid}", {"source_ids": [source_id]})
    project = client.get(f"/api/project/{pid}").json()
    enabled = client.patch(
        f"/api/project/{pid}",
        json={"updated_at": project["updated_at"], "trim_assist_on": True},
        headers=AUTH,
    )
    assert enabled.status_code == 200

    binned = client.post(
        f"/api/project/{pid}/clip/{source_id}/bin",
        json={"updated_at": enabled.json()["updated_at"]},
        headers=AUTH,
    )
    assert binned.status_code == 200
    assert binned.json()["clips"][0]["stashed_segment"] is not None
    restored = client.post(
        f"/api/project/{pid}/clip/{source_id}/bin",
        json={"updated_at": binned.json()["updated_at"]},
        headers=AUTH,
    )
    assert restored.status_code == 200
    assert restored.json()["clips"][0]["stashed_segment"] is None

    _job(client, f"/api/export/{pid}")
    final_project = client.get(f"/api/project/{pid}").json()
    assert final_project["export"]["last_render"]["qa"]["passed"] is True
    assert client.get(f"/api/export/{pid}/download").status_code == 200

    log = client.get(f"/api/project/{pid}/log").json()
    codes = [item["code"] for item in log]
    for expected in (
        "ORIGINALS_READ_ONLY",
        "LOCAL_ONLY",
        "MUSIC_SELECTED",
        "PROJECT_CREATED",
        "INGEST_SUMMARY",
        "ANALYSIS_SUMMARY",
        "TRIM_PROPOSAL_SUMMARY",
        "SPEED_PROPOSAL_SUMMARY",
        "TRIM_DISMISSED",
        "TRIM_ASSIST_ON",
        "CLIP_BINNED",
        "CLIP_RESTORED",
        "EXPORT_TRIM_SUMMARY",
        "EXPORT_SPEED_SUMMARY",
    ):
        assert expected in codes
    reason_texts = {
        reason["human_text"]
        for reason in final_project["clips"][0]["proposals"]["segments"]["reasons"]
    }
    assert reason_texts.issubset({item["text"] for item in log})

    _, reopened, _ = build_app(tmp_path, with_ai=True)
    assert reopened.get(f"/api/project/{pid}/log").json() == log
