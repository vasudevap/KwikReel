"""WO-118 · File-backed `project.json` store, schema v2 (`SPEC.md` §3).

One project per directory: `<root>/<project_id>/project.json`, with `log.json`
beside it (§7.3, `log_store.py`). Persistence is lossless — a byte-equivalent
round trip — and every save is guarded:

  * optimistic concurrency on `updated_at` (stale write -> ConflictError -> 409)
  * **an assist never changes a field whose `origin` is `"user"`** (§4.4)
  * a clip object is never dropped across a save
  * `order` is dense (1..N) and unique
  * the §3.2 field invariants that make the §3.1 derivation total
  * unknown `schema_version` on load -> SchemaVersionError (v2 has no migrations)

No HTTP concerns here — WO-123 maps these errors to responses.

## What v2 changed, and why the origin guard is now a backstop

Gone with schema v1: `stage_approvals` (and the finalize-invalidation rule that
went with it), `included`, `deleted`, and `Origin.included`. §3.4 makes reel
membership **derived** — a clip is out when it is trimmed to nothing, unlinked
or damaged — so there is no boolean to protect and no approval to invalidate.

The §4.4 guarantee also changed shape, and the change is worth stating because
it moves where the guarantee lives. In v1 the cross-save guard *was* the
mechanism: the assists wrote clip fields, and the store stopped them writing
over a user's. In v2 they write `proposals.*` and never touch clip fields at
all, and `derive.effective_trim` stops consulting proposals the moment `origin`
says `"user"`. **Stickiness is structural now** (§3.1).

What the store contributes to §4.4 is therefore two invariants rather than one
guard. `segment` and `speed_ranges` are tied to `origin == "user"`, so an
assist-written value is **unrepresentable** — the v1-shaped attack cannot even
be serialised. What remains expressible is an assist flipping the origin to take
a user-owned field *back*, and `_check_cross_save` refuses that. Both halves are
tested: the structural one in `tests/store/test_derive.py`, these below.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from backend.contracts.models import Project

SUPPORTED_SCHEMA_VERSION = 2


class StoreError(Exception):
    """Base class for store failures."""


class ProjectNotFoundError(StoreError):
    """No project.json exists for the given id."""


class ConflictError(StoreError):
    """Optimistic-concurrency failure: the incoming updated_at is stale (-> 409)."""


class InvariantError(StoreError):
    """The project violates a SPEC.md §3 structural invariant."""


class OriginProtectionError(InvariantError):
    """An assist tried to overwrite a field whose origin is 'user' (§4.4)."""


class SchemaVersionError(StoreError):
    """Unsupported schema_version on load — v2 has no migrations."""


def now_iso() -> str:
    """ISO-8601, UTC, microsecond precision so successive saves always advance."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _serialize(project: Project) -> str:
    # Canonical form: exactly what the round-trip gate asserts.
    return project.model_dump_json(indent=2) + "\n"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)  # atomic on POSIX
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


ORIGIN_FIELDS = ("order", "segments", "speed", "audio")

# Only these two are ever proposed: §3.2's `Proposals` carries `segments` and
# `speed` and nothing else. No assist proposes an order or an audio setting.
PROPOSED_FIELDS = ("segments", "speed")


def _check_speed_ranges(source_id: str, label: str, ranges) -> None:
    """§3.2 shape rules, plus the one §3.4's arithmetic needs.

    `rate > 0` and `to_s > from_s` are the contract's own annotations. **Ranges
    within one clip must not overlap**: §3.4's played-duration formula sums
    `overlap / rate` and subtracts the ramped time from the kept time, which is
    only well defined for disjoint ranges — overlapping ones would double-count
    and could report a negative unramped remainder. §4.2's proposer produces
    disjoint ranges by construction (contiguous dull seconds, merged when the
    gap is under 0.5 s), and the Editor has one speed lane per clip, so this
    rejects a malformed document rather than constraining anything the product
    can express.
    """
    ordered = sorted(ranges, key=lambda r: r.from_s)
    previous_to = None
    for rng in ordered:
        if rng.rate <= 0:
            raise InvariantError(
                f"clip {source_id!r} {label} range has rate {rng.rate!r}; SPEC.md §3.2 requires rate > 0"
            )
        if rng.to_s <= rng.from_s:
            raise InvariantError(
                f"clip {source_id!r} {label} range {rng.from_s}..{rng.to_s} is not a forward span"
            )
        if previous_to is not None and rng.from_s < previous_to:
            raise InvariantError(
                f"clip {source_id!r} {label} ranges overlap at {rng.from_s}; "
                f"SPEC.md §3.4's played-duration formula requires disjoint ranges"
            )
        previous_to = rng.to_s


def _check_invariants(project: Project) -> None:
    known_sources = {s.source_id for s in project.sources}
    for clip in project.clips:
        if clip.source_id not in known_sources:
            raise InvariantError(f"clip references unknown source_id {clip.source_id!r}")

        # §3.2: `segment` holds the USER's trim and is null unless origin says so.
        # Enforced both ways, which is what makes `derive.effective_trim` total —
        # there is no "user-owned but no value" case for it to guess at. Binning
        # writes a zero-length segment, so it does not need one.
        if (clip.segment is not None) != (clip.origin.segments == "user"):
            raise InvariantError(
                f"clip {clip.source_id!r}: segment is "
                f"{'set' if clip.segment is not None else 'null'} but origin.segments is "
                f"{clip.origin.segments!r}; SPEC.md §3.2 ties them together"
            )

        # §3.2: `speed_ranges` holds the USER's ramps. One direction only — a
        # user may own the field with no ramps at all (they removed the assist's
        # by hand, and no assist may put them back).
        if clip.speed_ranges and clip.origin.speed != "user":
            raise InvariantError(
                f"clip {clip.source_id!r}: speed_ranges is set but origin.speed is "
                f"{clip.origin.speed!r}; only the user's ramps live on the clip (SPEC.md §3.2)"
            )

        # No assist proposes an order or an audio setting, so those two origins
        # only ever read "default" or "user".
        for field in ("order", "audio"):
            if getattr(clip.origin, field) == "proposed":
                raise InvariantError(
                    f"clip {clip.source_id!r}: origin.{field} is 'proposed', but nothing "
                    f"proposes {field} — SPEC.md §3.2's Proposals carries segments and speed only"
                )

        # "proposed" means a machine touched the field, which it does by leaving
        # a proposal. An origin saying so with nothing retained is incoherent.
        for field in PROPOSED_FIELDS:
            if getattr(clip.origin, field) == "proposed" and getattr(clip.proposals, field) is None:
                raise InvariantError(
                    f"clip {clip.source_id!r}: origin.{field} is 'proposed' with no retained "
                    f"{field} proposal (SPEC.md §3.1 — proposals are what the derivation reads)"
                )

        _check_speed_ranges(clip.source_id, "speed_ranges", clip.speed_ranges)
        if clip.proposals.speed is not None:
            _check_speed_ranges(clip.source_id, "proposed speed", clip.proposals.speed.value)

    # §3.4 retired `deleted`, so `order` is dense across every clip. A clip that
    # is out of the reel still holds its place — removal is trimming to nothing,
    # not renumbering the reel around a gap.
    orders = sorted(c.order for c in project.clips)
    if len(set(orders)) != len(orders):
        raise InvariantError(f"order values are not unique: {orders}")
    if orders and orders != list(range(1, len(orders) + 1)):
        raise InvariantError(f"order is not dense (must be 1..N): {orders}")


def _check_cross_save(prior: Project, incoming: Project) -> None:
    prior_by_src = {c.source_id: c for c in prior.clips}
    incoming_ids = {c.source_id for c in incoming.clips}

    # A clip object is never dropped. §8.3 keeps a clip whose file has gone as
    # **unlinked**, and §3.4 removes one by trimming it to nothing — neither
    # takes it out of the document.
    for src in prior_by_src:
        if src not in incoming_ids:
            raise InvariantError(
                f"clip {src!r} was dropped; a clip leaves the reel by being trimmed to "
                f"nothing (SPEC.md §3.4), never by leaving the document"
            )

    # §4.4 · **an assist may not take a user-owned field back.** In v2 that is
    # the only shape the attempt can have: the assists never write clip fields
    # (§3.1), and the invariants above already tie `segment` and `speed_ranges`
    # to `origin == "user"`, so a machine cannot put a value there. What it can
    # do is flip the origin away from the user — reclaiming the field for the
    # derivation — and that is what this refuses.
    #
    # The reclaim is legitimate only where something is retained to reclaim it
    # for: §4.3's re-run key, and §4.3's restore handing a binned clip back to
    # the derivation it came from.
    #
    # **Two things this deliberately does not test.** It does not require the
    # proposal to be *fresh* (`disposition: "pending"`): that reads as a
    # stronger check and false-rejects a legitimate bin-then-restore on a clip
    # whose proposal has since been accepted at export. And it cannot tell a
    # bulk assist sweep from a per-clip re-run — the two are identical in the
    # document. Neither gap weakens §4.4, because the store is not where §4.4
    # lives: `derive.effective_trim` is, by not consulting a proposal at all
    # once the origin says "user".
    for clip in incoming.clips:
        pc = prior_by_src.get(clip.source_id)
        if pc is None:
            continue
        for field in ORIGIN_FIELDS:
            if getattr(pc.origin, field) != "user" or getattr(clip.origin, field) != "proposed":
                continue
            proposal = getattr(clip.proposals, field) if field in PROPOSED_FIELDS else None
            if proposal is None:
                raise OriginProtectionError(
                    f"clip {clip.source_id!r}: origin.{field} moved from 'user' to 'proposed' "
                    f"with nothing retained behind it; an assist may not take a user-owned "
                    f"field back (SPEC.md §4.4)"
                )


class FileProjectStore:
    """A `ProjectStore` (WO-117 `interfaces.py`) backed by one JSON file per project."""

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
            raise SchemaVersionError(
                f"unsupported schema_version {version!r} (this build supports "
                f"{SUPPORTED_SCHEMA_VERSION}); v1 documents are not migrated"
            )
        return Project.model_validate(data)

    def save(self, project: Project) -> Project:
        path = self._path(project.project_id)
        prior: Project | None = None
        if path.exists():
            prior = self.load(project.project_id)
            if prior.updated_at != project.updated_at:
                raise ConflictError(
                    f"stale updated_at: on-disk {prior.updated_at!r} != incoming {project.updated_at!r}"
                )
            # §4.4 is checked **before** the shape rules on purpose. A reclaim
            # trips both, and the caller is better served by an error that names
            # the rule it broke than by a generic "origin says proposed with
            # nothing retained".
            _check_cross_save(prior, project)

        _check_invariants(project)

        saved = project.model_copy(deep=True)
        saved.updated_at = now_iso()
        if prior is not None and saved.updated_at == prior.updated_at:
            saved.updated_at = now_iso()  # guarantee a monotonic advance

        atomic_write(path, _serialize(saved))
        return saved
