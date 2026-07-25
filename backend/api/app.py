"""FastAPI app for M1 (WO-106). Every ES-001 §6 route, ADR-011 security posture.

Security (ES-001 §9 / ADR-011), enforced by `SecurityMiddleware`:
  * Host allow-list  — Host must resolve to 127.0.0.1/localhost (anti DNS-rebinding)
  * Origin allow-list — a cross-origin request (Origin host not local) is rejected
  * Capability token — every state-changing method needs a valid per-launch token
  * No permissive CORS — no CORS middleware, so no wildcard ACAO is ever emitted
  * Path-scrubbed errors — via backend.api.errors

The app codes against the WO-101 service interfaces; long operations run through
the JobRunner. Bind to 127.0.0.1 only (see run.py); binding beyond is a stop-and-ask.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.staticfiles import StaticFiles

from backend.analysis import FileAnalysisStore
from backend.api.errors import envelope, install_error_handlers, scrub
from backend.api.jobs import JobRunner, ProgressFn
from backend.api.services import Services
from backend.contracts.models import (
    AudioMode,
    Clip,
    Export,
    Music,
    Origin,
    Project,
    Proposals,
    Segment,
    StageApprovals,
)
from backend.render.ffmpeg_render import output_filename

APP_VERSION = "0.1.0"
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost"})
STAGES = frozenset({"ingest", "trim", "selection", "speed", "finalize"})
MUTATING = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@dataclass
class ApiConfig:
    proxy_root: Path
    output_root: Path
    analysis_root: Path | None = None
    frontend_dist: Path | None = None
    allowed_hosts: frozenset[str] = LOCAL_HOSTS
    allowed_origin_hosts: frozenset[str] = LOCAL_HOSTS
    capability_token: str | None = None  # generated per launch if not supplied


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, token: str, allowed_hosts, allowed_origin_hosts) -> None:
        super().__init__(app)
        self._token = token
        self._hosts = allowed_hosts
        self._origins = allowed_origin_hosts

    async def dispatch(self, request: Request, call_next):
        host = (request.headers.get("host", "") or "").rsplit(":", 1)[0].strip("[]")
        if host and host not in self._hosts:
            return envelope("forbidden_host", "Request host is not allowed.", "Reach the app at http://127.0.0.1.", 403)

        origin = request.headers.get("origin")
        if origin is not None:
            if (urlparse(origin).hostname or "") not in self._origins:
                return envelope("forbidden_origin", "Cross-origin request rejected.", "Use the local app UI.", 403)

        if request.method in MUTATING:
            token = request.headers.get("x-capability-token", "")
            if not token or not hmac.compare_digest(token, self._token):
                return envelope("missing_capability", "Missing or invalid capability token.", "Reload the local app to obtain a fresh session.", 401)

        return await call_next(request)


class CreateProjectBody(BaseModel):
    media_root: str
    track_ref: str
    target_duration_s: float = 75.0


class ExportBody(BaseModel):
    audio_mode: AudioMode


class ProposeBody(BaseModel):
    source_ids: list[str] | None = None  # omit for all included clips


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _music_for(track_ref: str) -> Music:
    p = Path(track_ref)
    content_hash = ""
    if p.exists() and p.is_file():
        h = hashlib.sha256()
        with p.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        content_hash = h.hexdigest()
    return Music(track_ref=track_ref, content_hash=content_hash, duration_s=0.0)


def create_app(services: Services, config: ApiConfig) -> FastAPI:
    token = config.capability_token or secrets.token_urlsafe(32)
    runner = JobRunner(scrub=scrub)
    analysis_store = FileAnalysisStore(config.analysis_root) if config.analysis_root else None

    app = FastAPI(title="AI Vacation Reel Agent", version=APP_VERSION)
    app.state.capability_token = token
    app.add_middleware(
        SecurityMiddleware,
        token=token,
        allowed_hosts=config.allowed_hosts,
        allowed_origin_hosts=config.allowed_origin_hosts,
    )
    install_error_handlers(app)

    def _serve(path: Path) -> Response:
        if not path.exists():
            return envelope("not_found", "No such file.", "Produce it first.", 404)
        return FileResponse(str(path), media_type="video/mp4")  # Starlette handles Range

    # --- projects ---------------------------------------------------------

    @app.post("/api/project")
    def create_project(body: CreateProjectBody):
        pid = str(uuid4())
        now = _now_iso()
        project = Project(
            schema_version=1, project_id=pid, created_at=now, updated_at=now,
            app_version=APP_VERSION, name=None, media_root=body.media_root,
            target_duration_s=body.target_duration_s, music=_music_for(body.track_ref),
            sources=[], clips=[], stage_approvals=StageApprovals(),
            export=Export(audio_modes=["music", "clip", "silent"], last_render={}),
        )
        return services.store.save(project).model_dump()

    @app.get("/api/project/{project_id}")
    def get_project(project_id: str):
        return services.store.load(project_id).model_dump()

    @app.put("/api/project/{project_id}")
    def save_project(project_id: str, project: Project):
        from backend.store import InvariantError
        if project.project_id != project_id:
            raise InvariantError("project_id in body does not match the URL")
        return services.store.save(project).model_dump()

    @app.post("/api/project/{project_id}/approve/{stage}")
    def approve(project_id: str, stage: str):
        from backend.store import InvariantError
        if stage not in STAGES:
            raise InvariantError(f"unknown stage {stage!r}")
        project = services.store.load(project_id)
        setattr(project.stage_approvals, stage, _now_iso())
        return services.store.save(project).model_dump()

    # --- import / analyze / propose --------------------------------------

    @app.post("/api/import/{project_id}/scan")
    def scan(project_id: str):
        services.store.load(project_id)  # 404 if missing

        def work(progress: ProgressFn) -> None:
            project = services.store.load(project_id)
            sources = services.ingest.build_source_index(project.media_root)
            for i, s in enumerate(sources):
                if s.readable:
                    s.proxy_path = services.ingest.make_proxy(s)
                progress((i + 1) / max(len(sources), 1) * 0.9)
            # Default timeline for curation: capture-time order (§5.4), include readable.
            ordered = sorted(sources, key=lambda s: (s.captured_at or "", s.path))
            project.clips = [
                Clip(
                    source_id=s.source_id, included=s.readable, order=i + 1, deleted=False,
                    segments=[Segment(in_s=0.0, out_s=max(s.duration_s, 0.0), speed=[])],
                    origin=Origin(), proposals=Proposals(),
                )
                for i, s in enumerate(ordered)
            ]
            project.sources = sources
            project.stage_approvals.ingest = _now_iso()
            services.store.save(project)

        return {"job_id": runner.submit(work)}

    @app.post("/api/analyze/{project_id}")
    def analyze(project_id: str):
        services.store.load(project_id)
        if services.analysis is None:
            return envelope("not_implemented", "Per-clip analysis arrives in WO-111.", "Not available in this build.", 501)

        def work(progress: ProgressFn) -> None:
            project = services.store.load(project_id)
            readable = [s for s in project.sources if s.readable]
            for i, s in enumerate(readable):
                analysis = services.analysis.analyze(s)
                if analysis_store is not None:
                    analysis_store.save(project_id, analysis)
                progress((i + 1) / max(len(readable), 1))

        return {"job_id": runner.submit(work)}

    @app.post("/api/propose/trim/{project_id}")
    def propose_trim(project_id: str, body: ProposeBody | None = None):
        services.store.load(project_id)
        if services.proposer is None or services.analysis is None:
            return envelope("not_implemented", "The trim proposer arrives in WO-112.", "Not available in this build.", 501)
        wanted = set(body.source_ids) if body and body.source_ids else None

        def work(progress: ProgressFn) -> None:
            project = services.store.load(project_id)
            by_id = {s.source_id: s for s in project.sources}
            targets = [
                c for c in project.clips
                if c.included and not c.deleted and by_id.get(c.source_id) and by_id[c.source_id].readable
                and (wanted is None or c.source_id in wanted)
            ]
            for i, clip in enumerate(targets):
                src = by_id[clip.source_id]
                if analysis_store is not None and analysis_store.exists(project_id, src.source_id):
                    analysis = analysis_store.load(project_id, src.source_id)
                else:
                    analysis = services.analysis.analyze(src)
                    if analysis_store is not None:
                        analysis_store.save(project_id, analysis)
                proposal = services.proposer.propose_trim(src, analysis)
                # Apply the proposal as the effective trim, pending the user's review
                # (§5.3): segments become the proposal, origin -> "proposed", the
                # proposal is retained with disposition "pending".
                clip.segments = list(proposal.value)
                clip.origin.segments = "proposed"
                clip.proposals.segments = proposal
                progress((i + 1) / max(len(targets), 1))
            services.store.save(project)

        return {"job_id": runner.submit(work)}

    # --- jobs -------------------------------------------------------------

    @app.get("/api/jobs/{job_id}")
    def job_status(job_id: str):
        from backend.store import ProjectNotFoundError
        job = runner.get(job_id)
        if job is None:
            raise ProjectNotFoundError(job_id)
        return {"state": job.state, "progress": job.progress, "error": job.error}

    # --- media serving ----------------------------------------------------

    @app.get("/api/media/proxy/{source_id}")
    def serve_proxy(source_id: str):
        return _serve(config.proxy_root / f"{source_id}.mp4")

    @app.get("/api/render/{project_id}/draft")
    def serve_draft(project_id: str):
        project = services.store.load(project_id)
        return _serve(config.output_root / project_id / output_filename(project, "draft"))

    @app.get("/api/export/{project_id}/download/{audio_mode}")
    def download_export(project_id: str, audio_mode: str):
        project = services.store.load(project_id)
        record = project.export.last_render.get(audio_mode)
        if record is None:
            return envelope("not_found", "That audio mode has not been exported.", "Export it first.", 404)
        return _serve(Path(record.path))

    # --- render / export --------------------------------------------------

    @app.post("/api/render/{project_id}/finalize")
    def finalize(project_id: str):
        services.store.load(project_id)

        def work(progress: ProgressFn) -> None:
            project = services.store.load(project_id)
            progress(0.1)
            services.renderer.render_draft(project)

        return {"job_id": runner.submit(work)}

    @app.post("/api/export/{project_id}")
    def export(project_id: str, body: ExportBody):
        services.store.load(project_id)
        mode = body.audio_mode

        def work(progress: ProgressFn) -> None:
            from backend.render import RenderError
            project = services.store.load(project_id)
            progress(0.1)
            record = services.renderer.export(project, mode)
            progress(0.7)
            report = services.qa.validate_render(record.path, project, mode)
            if not report.passed:  # QA blocks export with a stated reason (§8.3)
                raise RenderError("output QA failed: " + "; ".join(report.reasons))
            fresh = services.store.load(project_id)
            fresh.export.last_render[mode] = record.model_copy(update={"qa": report})
            services.store.save(fresh)

        return {"job_id": runner.submit(work)}

    # Serve the built frontend as one local web app (ADR-005). The per-launch
    # capability token is injected into index.html here, at serve time — the
    # frontend never fetches it from an unauthenticated endpoint.
    if config.frontend_dist:
        dist = Path(config.frontend_dist)
        assets = dist / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/")
        def index() -> Response:
            html = (dist / "index.html").read_text(encoding="utf-8")
            inject = f"<script>window.__REEL_TOKEN__={json.dumps(token)}</script>"
            return HTMLResponse(html.replace("</head>", inject + "</head>"))

    return app
