"""WO-123 · Local HTTP API for the frozen v2 contract."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
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
    ConflictError,
    FileLogStore,
    InvariantError,
    LogEntry,
    SessionLogBuffer,
    effective_speed,
    effective_trim,
    in_reel,
    mark_proposals_accepted,
    reel_length_s,
    reject_trim_proposal,
    set_clip_order,
    set_user_audio,
    set_user_segment,
    set_user_speed_ranges,
    toggle_bin,
    unlinked_source_ids,
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
        if host not in self._hosts:
            return envelope("forbidden_host", "Request host is not allowed.", "Reach the app at http://127.0.0.1.", 403)
        origin = request.headers.get("origin")
        if origin is not None and (urlparse(origin).hostname or "") not in self._origins:
            return envelope("forbidden_origin", "Cross-origin request rejected.", "Use the local app UI.", 403)
        referer = request.headers.get("referer")
        if referer is not None and (urlparse(referer).hostname or "") not in self._origins:
            return envelope("forbidden_referer", "Cross-site request rejected.", "Use the local app UI.", 403)
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


class ProjectActionBody(BaseModel):
    updated_at: str


class MusicProbeBody(BaseModel):
    track_ref: str


class ClientLogBody(BaseModel):
    kind: Literal["warn", "fault"]
    text: str
    code: str | None = None
    source_id: str | None = None


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
    log_store = services.log
    if log_store is None:
        project_root = getattr(services.store, "root", None)
        if project_root is None:
            raise RuntimeError("the API requires a persistent Log store")
        log_store = FileLogStore(project_root)
    session_log = SessionLogBuffer()
    app = FastAPI(title="KwikReel", version=APP_VERSION)
    app.state.capability_token = token
    app.add_middleware(SecurityMiddleware, token=token, allowed_hosts=config.allowed_hosts, allowed_origin_hosts=config.allowed_origin_hosts)
    install_error_handlers(app)

    def source(project: Project, source_id: str):
        found = next((item for item in project.sources if item.source_id == source_id), None)
        if found is None:
            raise InvariantError(f"unknown source_id {source_id!r}")
        return found

    def clip_for(project: Project, source_id: str) -> Clip:
        found = next((item for item in project.clips if item.source_id == source_id), None)
        if found is None:
            raise InvariantError(f"unknown source_id {source_id!r}")
        return found

    def source_name(project: Project, source_id: str) -> str:
        return Path(source(project, source_id).path).name

    def require_current(project: Project, updated_at: str) -> None:
        if project.updated_at != updated_at:
            raise ConflictError("stale updated_at")

    def entry(
        kind: Literal["info", "warn", "fault"],
        text: str,
        *,
        code: str | None = None,
        source_id: str | None = None,
    ) -> LogEntry:
        return LogEntry(
            at=_now_iso(),
            kind=kind,
            text=scrub(text),
            code=code,
            source_id=source_id,
            standing=False,
        )

    def append_log(project_id: str, *entries: LogEntry) -> None:
        if entries:
            log_store.append(project_id, entries)

    def job_failure(project_id: str, operation: str, code: str):
        return lambda message: append_log(
            project_id,
            entry("fault", f"{operation} failed: {message}", code=code),
        )

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

    @app.post("/api/music/probe")
    def probe_music(body: MusicProbeBody):
        if services.media is None:
            return envelope("not_implemented", "Music inspection is not available.", "Enable the local media service.", 501)
        music = services.media.probe_music(body.track_ref, _hash(body.track_ref))
        session_log.add(
            entry(
                "info",
                f"Selected music {Path(body.track_ref).name}.",
                code="MUSIC_SELECTED",
            )
        )
        return music.model_dump()

    @app.post("/api/project")
    def create_project(body: CreateProjectBody):
        now = _now_iso()
        music = None
        if body.track_ref:
            content_hash = _hash(body.track_ref)
            music = (
                services.media.probe_music(body.track_ref, content_hash)
                if services.media
                else Music(track_ref=body.track_ref, content_hash=content_hash, duration_s=0.0)
            )
        project = Project(schema_version=2, project_id=str(uuid4()), created_at=now, updated_at=now,
            app_version=APP_VERSION, media_root=body.media_root, target_duration_s=body.target_duration_s,
            output_resolution=body.output_resolution, audio=AudioMix(music_level=body.music_level, clip_level=body.clip_level),
            music=music, sources=[], clips=[], export=Export())
        saved = services.store.save(project)
        log_store.ensure_standing(saved.project_id)
        session_log.flush_to(log_store, saved.project_id)
        append_log(
            saved.project_id,
            entry("info", "Project created.", code="PROJECT_CREATED"),
        )
        return saved.model_dump()

    @app.get("/api/project/{project_id}")
    def get_project(project_id: str):
        return services.store.load(project_id).model_dump()

    @app.patch("/api/project/{project_id}")
    def patch_project(project_id: str, body: ProjectPatch):
        project = services.store.load(project_id)
        require_current(project, body.updated_at)
        changed = body.model_fields_set - {"updated_at"}
        if not changed:
            raise InvariantError("patch contains no changes")
        before_length = reel_length_s(project, unlinked_source_ids(project))
        old_trim_assist = project.trim_assist_on
        old_speed_assist = project.speed_assist_on
        for field in changed:
            setattr(project, field, getattr(body, field))
        saved = services.store.save(project)
        transitions: list[LogEntry] = []
        after_length = reel_length_s(saved, unlinked_source_ids(saved))
        if "trim_assist_on" in changed and old_trim_assist != saved.trim_assist_on:
            kept = [
                source_name(saved, clip.source_id)
                for clip in sorted(saved.clips, key=lambda item: item.order)
                if clip.origin.segments == "user"
            ]
            verb = "applied" if saved.trim_assist_on else "reverted"
            kept_text = (
                f"{', '.join(kept)} kept your own trim."
                if kept
                else "No clips had your own trim."
            )
            transitions.append(
                entry(
                    "info",
                    f"Trim {verb}. {before_length:.1f}s → {after_length:.1f}s. {kept_text}",
                    code="TRIM_ASSIST_ON" if saved.trim_assist_on else "TRIM_ASSIST_OFF",
                )
            )
        if "speed_assist_on" in changed and old_speed_assist != saved.speed_assist_on:
            kept = [
                source_name(saved, clip.source_id)
                for clip in sorted(saved.clips, key=lambda item: item.order)
                if clip.origin.speed == "user"
            ]
            verb = "applied" if saved.speed_assist_on else "reverted"
            kept_text = (
                f"{', '.join(kept)} kept your own speed."
                if kept
                else "No clips had your own speed."
            )
            transitions.append(
                entry(
                    "info",
                    f"Speed {verb}. {before_length:.1f}s → {after_length:.1f}s. {kept_text}",
                    code="SPEED_ASSIST_ON" if saved.speed_assist_on else "SPEED_ASSIST_OFF",
                )
            )
        append_log(project_id, *transitions)
        return saved.model_dump()

    @app.patch("/api/project/{project_id}/clip/{source_id}")
    def patch_clip(project_id: str, source_id: str, body: ClipPatch):
        project = services.store.load(project_id)
        require_current(project, body.updated_at)
        before = clip_for(project, source_id)
        adjusted_trim = "segment" in body.model_fields_set and before.proposals.segments is not None
        adjusted_speed = "speed_ranges" in body.model_fields_set and before.proposals.speed is not None
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
        saved = services.store.save(project)
        disposition_entries: list[LogEntry] = []
        if adjusted_trim:
            disposition_entries.append(
                entry(
                    "info",
                    f"Adjusted the proposed trim for {source_name(saved, source_id)}.",
                    code="TRIM_ADJUSTED",
                    source_id=source_id,
                )
            )
        if adjusted_speed:
            disposition_entries.append(
                entry(
                    "info",
                    f"Adjusted the proposed speed for {source_name(saved, source_id)}.",
                    code="SPEED_ADJUSTED",
                    source_id=source_id,
                )
            )
        if "segment" in body.model_fields_set:
            trim = effective_trim(saved, clip_for(saved, source_id))
            duration = trim.out_s - trim.in_s
            if duration <= 0:
                disposition_entries.append(
                    entry(
                        "warn",
                        f"{source_name(saved, source_id)} is trimmed out of the reel.",
                        code="TRIMMED_TO_NOTHING",
                        source_id=source_id,
                    )
                )
            elif duration < 1.0:
                disposition_entries.append(
                    entry(
                        "warn",
                        f"{source_name(saved, source_id)} keeps less than one second.",
                        code="SHORT_TRIM",
                        source_id=source_id,
                    )
                )
        if "speed_ranges" in body.model_fields_set:
            for speed_range in effective_speed(saved, clip_for(saved, source_id)):
                if speed_range.rate != 1.0:
                    disposition_entries.append(
                        entry(
                            "warn",
                            f"{source_name(saved, source_id)} runs at {speed_range.rate:g}× from "
                            f"{speed_range.from_s:.1f}s to {speed_range.to_s:.1f}s.",
                            code="SPEED_CHANGED",
                            source_id=source_id,
                        )
                    )
        append_log(project_id, *disposition_entries)
        return saved.model_dump()

    @app.post("/api/project/{project_id}/clip/{source_id}/bin")
    def bin_or_restore(project_id: str, source_id: str, body: ProjectActionBody):
        project = services.store.load(project_id)
        require_current(project, body.updated_at)
        restoring = clip_for(project, source_id).stashed_segment is not None
        saved = services.store.save(toggle_bin(project, source_id))
        append_log(
            project_id,
            entry(
                "info" if restoring else "warn",
                (
                    f"Restored {source_name(saved, source_id)}."
                    if restoring
                    else f"Binned {source_name(saved, source_id)}; its trim is now empty."
                ),
                code="CLIP_RESTORED" if restoring else "CLIP_BINNED",
                source_id=source_id,
            ),
        )
        return saved.model_dump()

    @app.post("/api/project/{project_id}/clip/{source_id}/reject-trim")
    def reject_trim(project_id: str, source_id: str, body: ProjectActionBody):
        project = services.store.load(project_id)
        require_current(project, body.updated_at)
        saved = services.store.save(reject_trim_proposal(project, source_id))
        append_log(
            project_id,
            entry(
                "info",
                f"Rejected the proposed trim for {source_name(saved, source_id)}.",
                code="TRIM_DISMISSED",
                source_id=source_id,
            ),
        )
        return saved.model_dump()

    @app.post("/api/project/{project_id}/relink/{source_id}")
    def relink(project_id: str, source_id: str, body: RelinkBody):
        project = services.store.load(project_id)
        require_current(project, body.updated_at)
        replacement = services.ingest.probe_clip(body.path)
        replacement.source_id = source_id
        replacement.proxy_path = services.ingest.make_proxy(replacement) if replacement.readable else None
        for index, item in enumerate(project.sources):
            if item.source_id == source_id:
                project.sources[index] = replacement
                break
        else:
            raise InvariantError(f"unknown source_id {source_id!r}")
        saved = services.store.save(project)
        append_log(
            project_id,
            entry(
                "info",
                f"Linked {source_name(saved, source_id)}.",
                code="SOURCE_RELINKED",
                source_id=source_id,
            ),
        )
        return saved.model_dump()

    @app.post("/api/project/{project_id}/repair-links")
    def repair_links(project_id: str, body: ProjectActionBody):
        project = services.store.load(project_id)
        require_current(project, body.updated_at)
        root = Path(project.media_root).resolve()
        missing = [item for item in project.sources if not Path(item.path).is_file()]
        matches: dict[str, list[Path]] = {}
        if root.is_dir():
            for candidate in root.rglob("*"):
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                if not resolved.is_relative_to(root):
                    continue
                try:
                    matches.setdefault(_hash(str(resolved)), []).append(resolved)
                except OSError:
                    continue

        repaired = 0
        log_entries: list[LogEntry] = []
        for stale in missing:
            replacement = None
            for candidate in matches.get(stale.content_hash, []):
                try:
                    replacement = services.ingest.probe_clip(str(candidate))
                    break
                except Exception:
                    continue
            if replacement is None:
                log_entries.append(
                    entry(
                        "warn",
                        f"Could not find {Path(stale.path).name} beneath the media folder.",
                        code="SOURCE_UNLINKED",
                        source_id=stale.source_id,
                    )
                )
                continue
            replacement.source_id = stale.source_id
            replacement.proxy_path = services.ingest.make_proxy(replacement) if replacement.readable else None
            for index, item in enumerate(project.sources):
                if item.source_id == stale.source_id:
                    project.sources[index] = replacement
                    repaired += 1
                    break
            log_entries.append(
                entry(
                    "info",
                    f"Repaired the link to {Path(replacement.path).name}.",
                    code="SOURCE_REPAIRED",
                    source_id=stale.source_id,
                )
            )
        saved = services.store.save(project)
        log_entries.append(
            entry(
                "warn" if repaired < len(missing) else "info",
                f"Repaired {repaired} of {len(missing)} missing links.",
                code="LINK_REPAIR_SUMMARY",
            )
        )
        append_log(project_id, *log_entries)
        return saved.model_dump()

    @app.get("/api/project/{project_id}/log")
    def get_log(project_id: str):
        services.store.load(project_id)
        return [item.model_dump() for item in log_store.load(project_id)]

    @app.post("/api/project/{project_id}/log")
    def append_client_log(project_id: str, body: ClientLogBody):
        services.store.load(project_id)
        accepted = entry(
            body.kind,
            body.text,
            code=body.code,
            source_id=body.source_id,
        )
        return log_store.append_one(project_id, accepted).model_dump()

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
            details = [
                entry(
                    "fault",
                    f"Could not read {Path(item.path).name}.",
                    code="SOURCE_UNREADABLE",
                    source_id=item.source_id,
                )
                for item in sources
                if not item.readable
            ]
            readable = sum(1 for item in sources if item.readable)
            details.append(
                entry(
                    "info",
                    f"{len(sources)} files read from {Path(project.media_root).name}. "
                    f"{readable} in the reel, {len(sources) - readable} out.",
                    code="INGEST_SUMMARY",
                )
            )
            append_log(project_id, *details)
        return {
            "job_id": runner.submit(
                work,
                job_failure(project_id, "Import", "IMPORT_FAILED"),
            )
        }

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
            append_log(
                project_id,
                entry(
                    "info",
                    f"Analysed {len(readable)} clips.",
                    code="ANALYSIS_SUMMARY",
                ),
            )
        return {
            "job_id": runner.submit(
                work,
                job_failure(project_id, "Analysis", "ANALYSIS_FAILED"),
            )
        }

    def propose(project_id: str, body: ProposeBody | None, kind: str):
        services.store.load(project_id)
        proposer = services.proposer if kind == "trim" else services.speed_proposer
        if proposer is None or services.analysis is None:
            return envelope("not_implemented", f"{kind.title()} proposals are not available.", "Enable the local proposal service.", 501)
        wanted = set(body.source_ids) if body and body.source_ids else None
        def work(progress: ProgressFn) -> None:
            project = services.store.load(project_id)
            targets = [clip for clip in project.clips if source(project, clip.source_id).readable and (wanted is None or clip.source_id in wanted)]
            details: list[LogEntry] = []
            for index, clip in enumerate(targets):
                item = source(project, clip.source_id)
                analysis = analysis_store.load(project_id, item.source_id) if analysis_store and analysis_store.exists(project_id, item.source_id) else services.analysis.analyze(item)
                if analysis_store: analysis_store.save(project_id, analysis)
                proposal = proposer.propose_trim(item, analysis) if kind == "trim" else proposer.propose_speed(item, analysis)
                if kind == "trim":
                    clip.proposals.segments, clip.origin.segments = proposal, "proposed"
                else:
                    clip.proposals.speed, clip.origin.speed = proposal, "proposed"
                details.extend(
                    entry(
                        "info",
                        reason.human_text,
                        code=reason.code,
                        source_id=item.source_id,
                    )
                    for reason in proposal.reasons
                )
                if kind == "trim":
                    duration = proposal.value.out_s - proposal.value.in_s
                    if duration <= 0:
                        details.append(
                            entry(
                                "warn",
                                f"The proposed trim removes {Path(item.path).name} from the reel.",
                                code="TRIMMED_TO_NOTHING",
                                source_id=item.source_id,
                            )
                        )
                    elif duration < 1.0:
                        details.append(
                            entry(
                                "warn",
                                f"The proposed trim keeps less than one second of {Path(item.path).name}.",
                                code="SHORT_TRIM",
                                source_id=item.source_id,
                            )
                        )
                else:
                    for speed_range in proposal.value:
                        if speed_range.rate != 1.0:
                            details.append(
                                entry(
                                    "warn",
                                    f"{Path(item.path).name} runs at {speed_range.rate:g}× from "
                                    f"{speed_range.from_s:.1f}s to {speed_range.to_s:.1f}s.",
                                    code="SPEED_CHANGED",
                                    source_id=item.source_id,
                                )
                            )
                progress((index + 1) / max(len(targets), 1))
            services.store.save(project)
            details.append(
                entry(
                    "info",
                    f"{kind.title()} proposed on {len(targets)} clips.",
                    code=f"{kind.upper()}_PROPOSAL_SUMMARY",
                )
            )
            append_log(project_id, *details)
        return {
            "job_id": runner.submit(
                work,
                job_failure(project_id, f"{kind.title()} proposal", f"{kind.upper()}_PROPOSAL_FAILED"),
            )
        }

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
            fresh, summary = mark_proposals_accepted(services.store.load(project_id))
            fresh.export.last_render = record.model_copy(update={"qa": report})
            saved = services.store.save(fresh)
            details: list[LogEntry] = []
            unlinked = unlinked_source_ids(saved)
            for clip in saved.clips:
                if not in_reel(saved, clip, unlinked):
                    continue
                for speed_range in effective_speed(saved, clip):
                    if speed_range.rate != 1.0:
                        details.append(
                            entry(
                                "warn",
                                f"{source_name(saved, clip.source_id)} rendered at {speed_range.rate:g}×.",
                                code="SPEED_RENDERED",
                                source_id=clip.source_id,
                            )
                        )
            details.extend(
                [
                    entry("info", summary.trim_line(), code="EXPORT_TRIM_SUMMARY"),
                    entry("info", summary.speed_line(), code="EXPORT_SPEED_SUMMARY"),
                ]
            )
            append_log(project_id, *details)
        return {
            "job_id": runner.submit(
                work,
                job_failure(project_id, "Export", "EXPORT_FAILED"),
            )
        }

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
