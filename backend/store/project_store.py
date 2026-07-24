"""File-backed `project.json` store enforcing the ES-001 §4.1 invariants.

One project per directory: `<root>/<project_id>/project.json`. Persistence is
lossless (byte-equivalent round-trip) and every save is guarded:

  * optimistic concurrency on `updated_at` (stale write -> ConflictError -> HTTP 409)
  * a machine write may not overwrite a field whose origin is "user"
    (OriginProtectionError) unless an accepted proposal backs the new value
  * `deleted` is a flag: a clip object is never dropped across a save
  * `order` is dense (1..N) and unique across non-deleted clips
  * unknown `schema_version` on load -> SchemaVersionError (no migrations in M1)

No HTTP concerns here — the API layer (WO-106) maps these errors to responses.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from backend.contracts.models import Clip, Project

SUPPORTED_SCHEMA_VERSION = 1


class StoreError(Exception):
    """Base class for store failures."""


class ProjectNotFoundError(StoreError):
    """No project.json exists for the given id."""


class ConflictError(StoreError):
    """Optimistic-concurrency failure: the incoming updated_at is stale (-> 409)."""


class InvariantError(StoreError):
    """The project violates an ES-001 §4.1 structural invariant."""


class OriginProtectionError(InvariantError):
    """A machine write tried to overwrite a field whose origin is 'user'."""


class SchemaVersionError(StoreError):
    """Unsupported schema_version on load — M1 has no migrations."""


def _now_iso() -> str:
    # Microsecond precision so successive saves always advance updated_at.
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _serialize(project: Project) -> str:
    # Canonical form: exactly what the contract round-trip test asserts.
    return project.model_dump_json(indent=2) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)  # atomic on POSIX
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# Fields that carry an origin marker and a comparable effective value. `speed`
# and `audio` have no independent M1 value/proposal and are left to M3/M2.
def _field_view(clip: Clip):
    return {
        "included": (clip.origin.included, clip.included, clip.proposals.included),
        "order": (clip.origin.order, clip.order, clip.proposals.order),
        "segments": (clip.origin.segments, clip.segments, clip.proposals.segments),
    }


def _check_invariants(project: Project) -> None:
    known_sources = {s.source_id for s in project.sources}
    for clip in project.clips:
        if clip.source_id not in known_sources:
            raise InvariantError(
                f"clip references unknown source_id {clip.source_id!r}"
            )
        # Pydantic already guarantees a disposition on every present proposal.

    orders = sorted(c.order for c in project.clips if not c.deleted)
    if len(set(orders)) != len(orders):
        raise InvariantError(f"order values are not unique across non-deleted clips: {orders}")
    if orders and orders != list(range(1, len(orders) + 1)):
        raise InvariantError(f"order is not dense (must be 1..N across non-deleted clips): {orders}")


def _check_cross_save(prior: Project, incoming: Project) -> None:
    prior_by_src = {c.source_id: c for c in prior.clips}
    incoming_ids = {c.source_id for c in incoming.clips}

    # deleted is a flag: a clip object is never dropped across a save.
    for src in prior_by_src:
        if src not in incoming_ids:
            raise InvariantError(
                f"clip {src!r} was dropped; deletion must set deleted=true, not remove the clip"
            )

    # A machine write ("proposed") may not overwrite a field whose prior origin
    # is "user", unless an accepted proposal for that field backs the new value.
    for clip in incoming.clips:
        pc = prior_by_src.get(clip.source_id)
        if pc is None:
            continue
        prior_view = _field_view(pc)
        for field, (new_origin, new_value, new_proposal) in _field_view(clip).items():
            prior_origin, prior_value, _ = prior_view[field]
            if prior_origin == "user" and new_origin == "proposed" and new_value != prior_value:
                backed = (
                    new_proposal is not None
                    and new_proposal.disposition == "accepted"
                    and new_proposal.value == new_value
                )
                if not backed:
                    raise OriginProtectionError(
                        f"machine write to clip {clip.source_id!r} field {field!r} would "
                        f"overwrite a user-owned value; an explicit re-run + accept is required"
                    )


class FileProjectStore:
    """A `ProjectStore` backed by one JSON file per project under `root`."""

    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root)

    def _path(self, project_id: str) -> Path:
        return self.root / project_id / "project.json"

    def exists(self, project_id: str) -> bool:
        return self._path(project_id).exists()

    def load(self, project_id: str) -> Project:
        path = self._path(project_id)
        if not path.exists():
            raise ProjectNotFoundError(project_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        version = data.get("schema_version")
        if version != SUPPORTED_SCHEMA_VERSION:
            raise SchemaVersionError(f"unsupported schema_version {version!r} (M1 supports {SUPPORTED_SCHEMA_VERSION})")
        return Project.model_validate(data)

    def save(self, project: Project) -> Project:
        _check_invariants(project)

        path = self._path(project.project_id)
        prior: Project | None = None
        if path.exists():
            prior = self.load(project.project_id)
            if prior.updated_at != project.updated_at:
                raise ConflictError(
                    f"stale updated_at: on-disk {prior.updated_at!r} != incoming {project.updated_at!r}"
                )
            _check_cross_save(prior, project)

        saved = project.model_copy(deep=True)
        saved.updated_at = _now_iso()
        if prior is not None and saved.updated_at == prior.updated_at:
            saved.updated_at = _now_iso()  # guarantee monotonic advance

        _atomic_write(path, _serialize(saved))
        return saved
