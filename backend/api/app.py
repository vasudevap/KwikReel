"""WO-123 · Local HTTP API for the frozen v2 contract."""

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
from backend.contracts.models import AudioMix, AudioSettings, Clip, Export, Music, Project, Segment, SpeedRange
from backend.render.ffmpeg_render import output_filename
from backend.store import (
    InvariantError, mark_proposals_accepted, set_clip_order, set_user_audio,
    set_user_segment, set_user_speed_ranges,
)

APP_VERSION = "0.2.0"
LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost"})
MUTATING = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@dataclass
class ApiConfig:
    proxy_root: Path
    output_root: Path
    analysis_root: Path | None = None
    frontend_dist: Path | None = None
    allowed_hosts: frozenset[str] = LOCAL_HOSTS
    allowed_origin_hosts: frozenset[str] = LOCAL_HOSTS
    capability_token: str | None = None


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, token: str, allowed_hosts, allowed_origin_hosts) -> None:
        super().__init__(app)
        self._token, self._hosts, self._origins = token, allowed_hosts, allowed_origin_hosts

    async def dispatch(self, request: Request, call_next):
        host = (request.headers.get("host", "") or "").rsplit(":", 1)[0].strip("[]")
        if host and host not in self._hosts:
            return envelope("forbidden_host", "Request host is not allowed.", "Reach the app at http://127.0.0.1.", 403)
        origin = request.headers.get("origin")
        if origin is not None and (urlparse(origin).hostname or "") not in self._origins:
            return envelope("forbidden_origin", "Cross-origin request rejected.", "Use the local app UI.", 403)
        if request.method in MUTATING:
            supplied = request.headers.get("x-capability-token", "")
            if not supplied or not hmac.compare_digest(supplied, self._token):
                return envelope("missing_capability", "Missing or invalid capability token.", "Reload the local app to obtain a fresh session.", 401)
        return await call_next(request)


class CreateProjectBody(BaseModel):
    media_root: str
    output_resolution: str
    music_level: float
    clip_level: float
    target_duration_s: float = 75.0
    track_ref: str | None = None


class ProjectPatch(BaseModel):
    updated_at: str
    name: str | None = None
    target_duration_s: float | None = None
    output_resolution: str | None = None
    audio: AudioMix | None = None
    trim_assist_on: bool | None = None
    speed_assist_on: bool | None = None
    music: Music | None = None


class ClipPatch(BaseModel):
    updated_at: str
    order: int | None = None
    segment: Segment | None = None
    speed_ranges: list[SpeedRange] | None = None
    audio: AudioSettings | None = None


class RelinkBody(BaseModel):
    updated_at: str
    path: str


class ProposeBody(BaseModel):
    source_ids: list[str] | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash(path: str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_app(services: Services, config: ApiConfig) -> FastAPI:
    token = config.capability_token or secrets.token_urlsafe(32)
    runner = JobRunner(scrub=scrub)
    analysis_store = FileAnalysisStore(config.analysis_root) if config.analysis_root else None
    app = FastAPI(title="KwikReel", version=APP_VERSION)
    app.state.capability_token = token
    app.add_middleware(SecurityMiddleware, token=token, allowed_hosts=config.allowed_hosts, allowed_origin_hosts=config.allowed_origin_hosts)
    install_error_handlers(app)

    def source(project: Project, source_id: str):
        found = next((item for item in project.sources if item.source_id == source_id), None)
        if found is None:
            raise InvariantError(f"unknown source_id {source_id!r}")
        return found

    def serve(path: Path, media_type: str = "video/mp4") -> Response:
        if not path.exists():
            return envelope("not_found", "No such file.", "Produce it first.", 404)
        return FileResponse(str(path), media_type=media_type)

    @app.post("/api/pick-folder")
    def pick_folder():
        return {"path": services.media.pick_folder() if services.media else None}

    @app.post("/api/pick-file")
    def pick_file():
        return {"path": services.media.pick_file() if services.media else None}

    @app.post("/api/project")
    def create_project(body: CreateProjectBody):
        now = _now_iso()
        music = Music(track_ref=body.track_ref, content_hash=_hash(body.track_ref), duration_s=0.0) if body.track_ref else None
        project = Project(schema_version=2, project_id=str(uuid4()), created_at=now, updated_at=now,
            app_version=APP_VERSION, media_root=body.media_root, target_duration_s=body.target_duration_s,
            output_resolution=body.output_resolution, audio=AudioMix(music_level=body.music_level, clip_level=body.clip_level),
            music=music, sources=[], clips=[], export=Export())
        return services.store.save(project).model_dump()

    @app.get("/api/project/{project_id}")
    def get_project(project_id: str):
        return services.store.load(project_id).model_dump()

    @app.patch("/api/project/{project_id}")
    def patch_project(project_id: str, body: ProjectPatch):
        project = services.store.load(project_id)
        if project.updated_at != body.updated_at:
            from backend.store import ConflictError
            raise ConflictError("stale updated_at")
        changed = body.model_fields_set - {"updated_at"}
        if not changed:
            raise InvariantError("patch contains no changes")
        for field in changed:
            setattr(project, field, getattr(body, field))
        return services.store.save(project).model_dump()

    @app.patch("/api/project/{project_id}/clip/{source_id}")
    def patch_clip(project_id: str, source_id: str, body: ClipPatch):
        project = services.store.load(project_id)
        if project.updated_at != body.updated_at:
            from backend.store import ConflictError
            raise ConflictError("stale updated_at")
        if "segment" in body.model_fields_set:
            if body.segment is None:
                raise InvariantError("segment may not be null")
            project = set_user_segment(project, source_id, body.segment)
        if "speed_ranges" in body.model_fields_set:
            project = set_user_speed_ranges(project, source_id, body.speed_ranges or [])
        if "audio" in body.model_fields_set:
            if body.audio is None:
                raise InvariantError("audio may not be null")
            project = set_user_audio(project, source_id, retain=body.audio.retain, gain_db=body.audio.gain_db)
        if "order" in body.model_fields_set:
            if body.order is None or not 1 <= body.order <= len(project.clips):
                raise InvariantError("order must be within the project clip range")
            ordering = [clip.source_id for clip in sorted(project.clips, key=lambda item: item.order) if clip.source_id != source_id]
            ordering.insert(body.order - 1, source_id)
            project = set_clip_order(project, ordering)
        return services.store.save(project).model_dump()

    @app.post("/api/project/{project_id}/relink/{source_id}")
    def relink(project_id: str, source_id: str, body: RelinkBody):
        project = services.store.load(project_id)
        if project.updated_at != body.updated_at:
            from backend.store import ConflictError
            raise ConflictError("stale updated_at")
        replacement = services.ingest.probe_clip(body.path)
        replacement.source_id = source_id
        replacement.proxy_path = services.ingest.make_proxy(replacement) if replacement.readable else None
        for index, item in enumerate(project.sources):
            if item.source_id == source_id:
                project.sources[index] = replacement
                break
        else:
            raise InvariantError(f"unknown source_id {source_id!r}")
        return services.store.save(project).model_dump()

    @app.post("/api/import/{project_id}/scan")
    def scan(project_id: str):
        services.store.load(project_id)
        def work(progress: ProgressFn) -> None:
            project = services.store.load(project_id)
            sources = services.ingest.build_source_index(project.media_root)
            for index, item in enumerate(sources):
                if item.readable:
                    item.proxy_path = services.ingest.make_proxy(item)
                progress((index + 1) / max(len(sources), 1) * 0.9)
            project.sources = sources
            project.clips = [Clip(source_id=item.source_id, order=index) for index, item in enumerate(sorted(sources, key=lambda item: (item.captured_at or "", item.path)), 1)]
            services.store.save(project)
        return {"job_id": runner.submit(work)}

    @app.post("/api/analyze/{project_id}")
    def analyze(project_id: str):
        services.store.load(project_id)
        if services.analysis is None:
            return envelope("not_implemented", "Analysis is not available.", "Enable the local analysis service.", 501)
        def work(progress: ProgressFn) -> None:
            project = services.store.load(project_id)
            readable = [item for item in project.sources if item.readable]
            for index, item in enumerate(readable):
                analysis = services.analysis.analyze(item)
                if analysis_store: analysis_store.save(project_id, analysis)
                progress((index + 1) / max(len(readable), 1))
        return {"job_id": runner.submit(work)}

    def propose(project_id: str, body: ProposeBody | None, kind: str):
        services.store.load(project_id)
        proposer = services.proposer if kind == "trim" else services.speed_proposer
        if proposer is None or services.analysis is None:
            return envelope("not_implemented", f"{kind.title()} proposals are not available.", "Enable the local proposal service.", 501)
        wanted = set(body.source_ids) if body and body.source_ids else None
        def work(progress: ProgressFn) -> None:
            project = services.store.load(project_id)
            targets = [clip for clip in project.clips if source(project, clip.source_id).readable and (wanted is None or clip.source_id in wanted)]
            for index, clip in enumerate(targets):
                item = source(project, clip.source_id)
                analysis = analysis_store.load(project_id, item.source_id) if analysis_store and analysis_store.exists(project_id, item.source_id) else services.analysis.analyze(item)
                if analysis_store: analysis_store.save(project_id, analysis)
                proposal = proposer.propose_trim(item, analysis) if kind == "trim" else proposer.propose_speed(item, analysis)
                if kind == "trim":
                    clip.proposals.segments, clip.origin.segments = proposal, "proposed"
                else:
                    clip.proposals.speed, clip.origin.speed = proposal, "proposed"
                progress((index + 1) / max(len(targets), 1))
            services.store.save(project)
        return {"job_id": runner.submit(work)}

    @app.post("/api/propose/trim/{project_id}")
    def propose_trim(project_id: str, body: ProposeBody | None = None): return propose(project_id, body, "trim")
    @app.post("/api/propose/speed/{project_id}")
    def propose_speed(project_id: str, body: ProposeBody | None = None): return propose(project_id, body, "speed")

    @app.get("/api/jobs/{job_id}")
    def job_status(job_id: str):
        from backend.store import ProjectNotFoundError
        job = runner.get(job_id)
        if job is None: raise ProjectNotFoundError(job_id)
        return {"state": job.state, "progress": job.progress, "error": job.error}

    @app.get("/api/media/proxy/{source_id}")
    def serve_proxy(source_id: str): return serve(config.proxy_root / f"{source_id}.mp4")
    @app.get("/api/media/thumb/{project_id}/{source_id}")
    def thumbnail(project_id: str, source_id: str, at_s: float = 0.0):
        if services.media is None: return envelope("not_implemented", "Preview media is not available.", "Enable the local media service.", 501)
        return Response(content=services.media.thumbnail(source(services.store.load(project_id), source_id), at_s), media_type="image/jpeg")
    @app.get("/api/media/peaks/{project_id}/{source_id}")
    def peaks(project_id: str, source_id: str):
        if services.media is None: return envelope("not_implemented", "Preview media is not available.", "Enable the local media service.", 501)
        return {"peaks": services.media.peaks(source(services.store.load(project_id), source_id))}
    @app.get("/api/music/peaks")
    def music_peaks(track_ref: str, content_hash: str):
        if services.media is None: return envelope("not_implemented", "Preview media is not available.", "Enable the local media service.", 501)
        return {"peaks": services.media.music_peaks(track_ref, content_hash)}

    @app.post("/api/export/{project_id}")
    def export(project_id: str):
        services.store.load(project_id)
        def work(progress: ProgressFn) -> None:
            from backend.render import RenderError
            project = services.store.load(project_id)
            progress(0.1); record = services.renderer.export(project); progress(0.7)
            report = services.qa.validate_render(record.path, project)
            if not report.passed: raise RenderError("output QA failed: " + "; ".join(report.reasons))
            fresh, _ = mark_proposals_accepted(services.store.load(project_id))
            fresh.export.last_render = record.model_copy(update={"qa": report})
            services.store.save(fresh)
        return {"job_id": runner.submit(work)}

    @app.get("/api/export/{project_id}/download")
    def download_export(project_id: str):
        record = services.store.load(project_id).export.last_render
        if record is None: return envelope("not_found", "No export is available.", "Export the reel first.", 404)
        return serve(Path(record.path))

    if config.frontend_dist:
        dist, assets = Path(config.frontend_dist), Path(config.frontend_dist) / "assets"
        if assets.is_dir(): app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")
        @app.get("/")
        def index() -> Response:
            html = (dist / "index.html").read_text(encoding="utf-8")
            return HTMLResponse(html.replace("</head>", f"<script>window.__REEL_TOKEN__={json.dumps(token)}</script></head>"))
    return app
