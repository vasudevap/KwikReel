"""WO-113 security guards (ADR-011 / ES-001 §9). Each test asserts a protection
is active, so removing that protection makes the test fail.

Covered: Origin allow-list · Host allow-list · capability token on mutations ·
no wildcard CORS · absolute paths scrubbed from surfaced errors. No ffmpeg needed.
"""

from __future__ import annotations

from backend.api.errors import scrub
from tests.support import AUTH, build_app, wait_job

_BODY = {"media_root": "/m", "track_ref": "/t"}


def test_scrub_removes_absolute_paths() -> None:
    assert scrub("failed at /Users/x/secret/movie.mov here") == "failed at <path> here"
    assert scrub(None) == ""


def test_cross_origin_post_is_rejected(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    r = client.post("/api/project", json=_BODY, headers={**AUTH, "Origin": "http://evil.example"})
    assert r.status_code == 403
    assert r.json()["error_code"] == "forbidden_origin"


def test_local_cross_port_origin_is_allowed(tmp_path) -> None:
    # The Vite dev origin (different port, same host) must work; only foreign hosts are blocked.
    _, client, _ = build_app(tmp_path)
    r = client.post("/api/project", json=_BODY, headers={**AUTH, "Origin": "http://localhost:5173"})
    assert r.status_code == 200


def test_foreign_host_is_rejected(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    r = client.get("/api/project/whatever", headers={"Host": "evil.example"})
    assert r.status_code == 403
    assert r.json()["error_code"] == "forbidden_host"


def test_mutation_without_token_is_rejected(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    r = client.post("/api/project", json=_BODY)  # no token
    assert r.status_code == 401
    assert r.json()["error_code"] == "missing_capability"


def test_mutation_with_wrong_token_is_rejected(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    r = client.post("/api/project", json=_BODY, headers={"X-Capability-Token": "wrong"})
    assert r.status_code == 401


def test_reads_need_no_token(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    r = client.get("/api/project/does-not-exist")  # GET is not a mutation
    assert r.status_code == 404  # reached the route (not 401)


def test_no_wildcard_cors_header_is_ever_sent(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    r = client.post("/api/project", json=_BODY, headers={**AUTH, "Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") != "*"


def test_error_envelope_carries_no_absolute_media_path(tmp_path) -> None:
    _, client, _ = build_app(tmp_path)
    pid = client.post(
        "/api/project",
        json={"media_root": "/private/secret_dir", "track_ref": "/private/track.m4a"},
        headers=AUTH,
    ).json()["project_id"]
    job_id = client.post(f"/api/import/{pid}/scan", headers=AUTH).json()["job_id"]
    status = wait_job(client, job_id)
    assert status["state"] == "error"
    assert "/private" not in (status["error"] or "")
    assert "secret_dir" not in (status["error"] or "")
