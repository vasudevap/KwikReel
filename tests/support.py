"""Shared helpers for the API and guard tests."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import ApiConfig, Services, create_app
from backend.ingest import FFmpegIngest
from backend.media import FFmpegMediaService
from backend.propose import SpeedRuleProposer
from backend.qa import FFmpegOutputQA
from backend.render import FFmpegRenderer
from backend.store import FileProjectStore

TEST_TOKEN = "test-capability-token"
AUTH = {"X-Capability-Token": TEST_TOKEN}


def build_app(tmp_path: Path, with_ai: bool = False):
    proxy_root = tmp_path / "proxies"
    output_root = tmp_path / "renders"
    analysis_root = tmp_path / "analysis"
    kwargs = dict(
        store=FileProjectStore(tmp_path / "projects"),
        ingest=FFmpegIngest(proxy_root=proxy_root),
        renderer=FFmpegRenderer(output_root=output_root),
        qa=FFmpegOutputQA(),
        media=FFmpegMediaService(tmp_path / "media-cache"),
        speed_proposer=SpeedRuleProposer(),
    )
    if with_ai:  # WO-111/112 — injected only when a test needs the trim assist
        from backend.analysis import OpenCVAnalysis
        from backend.propose import TrimRuleProposer

        kwargs["analysis"] = OpenCVAnalysis()
        kwargs["proposer"] = TrimRuleProposer()
    services = Services(**kwargs)
    config = ApiConfig(
        proxy_root=proxy_root, output_root=output_root,
        analysis_root=analysis_root if with_ai else None, capability_token=TEST_TOKEN,
    )
    app = create_app(services, config)
    # base_url on 127.0.0.1 so the Host allow-list passes by default.
    client = TestClient(app, base_url="http://127.0.0.1")
    return app, client, config


def wait_job(client: TestClient, job_id: str, timeout: float = 120.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get(f"/api/jobs/{job_id}").json()
        if status["state"] in ("done", "error"):
            return status
        time.sleep(0.1)
    raise AssertionError(f"job {job_id} did not finish within {timeout}s")
