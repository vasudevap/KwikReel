"""WO-103 gates · save/load round-trip, optimistic concurrency, and the
ES-001 §4.1 invariants (origin protection, delete-is-a-flag, dense order)."""

from __future__ import annotations

import json

import pytest

from backend.contracts.models import Project, ReasonRecord, Segment, SegmentsProposal
from backend.store import (
    ConflictError,
    FileProjectStore,
    InvariantError,
    OriginProtectionError,
    ProjectNotFoundError,
    SchemaVersionError,
)
from tests.contracts.canonical_example import build_example


def _clip(project: Project, source_id: str):
    return next(c for c in project.clips if c.source_id == source_id)


def _store(tmp_path) -> FileProjectStore:
    return FileProjectStore(tmp_path)


def test_save_then_load_is_byte_equivalent(tmp_path) -> None:
    store = _store(tmp_path)
    saved = store.save(build_example())

    on_disk = (tmp_path / saved.project_id / "project.json").read_text(encoding="utf-8")
    assert on_disk == saved.model_dump_json(indent=2) + "\n"

    reloaded = store.load(saved.project_id)
    assert reloaded == saved
    assert reloaded.model_dump_json(indent=2) + "\n" == on_disk


def test_save_bumps_updated_at(tmp_path) -> None:
    store = _store(tmp_path)
    original = build_example()
    saved = store.save(original)
    assert saved.updated_at != original.updated_at
    assert saved.created_at == original.created_at  # created_at is preserved


def test_load_missing_project_raises(tmp_path) -> None:
    with pytest.raises(ProjectNotFoundError):
        _store(tmp_path).load("does-not-exist")


def test_optimistic_concurrency_conflict(tmp_path) -> None:
    store = _store(tmp_path)
    s1 = store.save(build_example())
    s2 = store.save(s1)  # in-sync client: prior.updated_at == incoming -> ok
    assert s2.updated_at != s1.updated_at
    with pytest.raises(ConflictError):
        store.save(s1)  # s1 is now stale -> 409


def test_machine_write_refuses_to_overwrite_user_field(tmp_path) -> None:
    store = _store(tmp_path)
    s1 = store.save(build_example())

    # The user hand-trims clip s2 (origin -> "user").
    proj = s1.model_copy(deep=True)
    _clip(proj, "s2").segments = [Segment(in_s=1.0, out_s=6.0, speed=[])]
    _clip(proj, "s2").origin.segments = "user"
    s2 = store.save(proj)

    # A machine (origin -> "proposed") tries to overwrite that user value with
    # no accepted proposal behind it: rejected.
    attack = s2.model_copy(deep=True)
    _clip(attack, "s2").segments = [Segment(in_s=2.0, out_s=7.0, speed=[])]
    _clip(attack, "s2").origin.segments = "proposed"
    with pytest.raises(OriginProtectionError):
        store.save(attack)


def test_accepted_proposal_may_set_origin_proposed(tmp_path) -> None:
    # The guard must not block a legitimate accept: origin user -> proposed is
    # allowed when an accepted proposal backs the new value.
    store = _store(tmp_path)
    s1 = store.save(build_example())
    proj = s1.model_copy(deep=True)
    _clip(proj, "s2").segments = [Segment(in_s=1.0, out_s=6.0, speed=[])]
    _clip(proj, "s2").origin.segments = "user"
    s2 = store.save(proj)

    ok = s2.model_copy(deep=True)
    new_seg = [Segment(in_s=2.0, out_s=7.0, speed=[])]
    clip = _clip(ok, "s2")
    clip.segments = new_seg
    clip.origin.segments = "proposed"
    clip.proposals.segments = SegmentsProposal(
        value=new_seg,
        at="2026-07-24T20:00:00Z",
        reasons=[ReasonRecord(code="RERUN", human_text="re-proposed", evidence_refs=["signals.blur[0:1]"], score=0.4, confidence="med")],
        disposition="accepted",
    )
    saved = store.save(ok)  # allowed
    assert _clip(saved, "s2").origin.segments == "proposed"


def test_rerun_pending_proposal_may_overwrite_user_field(tmp_path) -> None:
    # §5.3: an explicit re-run applies a fresh proposal (disposition pending) over a
    # user-edited clip. The guard allows it because the new value matches the proposal.
    store = _store(tmp_path)
    s1 = store.save(build_example())
    proj = s1.model_copy(deep=True)
    _clip(proj, "s2").segments = [Segment(in_s=1.0, out_s=6.0, speed=[])]
    _clip(proj, "s2").origin.segments = "user"
    s2 = store.save(proj)

    rerun = s2.model_copy(deep=True)
    new_seg = [Segment(in_s=2.5, out_s=6.5, speed=[])]
    clip = _clip(rerun, "s2")
    clip.segments = new_seg
    clip.origin.segments = "proposed"
    clip.proposals.segments = SegmentsProposal(
        value=new_seg,
        at="2026-07-24T21:00:00Z",
        reasons=[ReasonRecord(code="RERUN", human_text="re-proposed", evidence_refs=["signals.blur[0:1]"], score=0.5, confidence="med")],
        disposition="pending",
    )
    saved = store.save(rerun)  # allowed — value matches the retained proposal
    assert _clip(saved, "s2").origin.segments == "proposed"


def test_delete_then_restore_is_exact(tmp_path) -> None:
    store = _store(tmp_path)
    original = build_example()
    s1 = store.save(original)

    # Delete the last clip (s3) — non-deleted order stays dense (1..2), no renumber.
    deleted = s1.model_copy(deep=True)
    _clip(deleted, "s3").deleted = True
    s2 = store.save(deleted)

    # Restore it.
    restored = s2.model_copy(deep=True)
    _clip(restored, "s3").deleted = False
    store.save(restored)

    loaded = store.load(original.project_id)
    orig_c3 = _clip(original, "s3")
    got_c3 = _clip(loaded, "s3")
    assert got_c3.segments == orig_c3.segments
    assert got_c3.origin == orig_c3.origin
    assert got_c3.proposals == orig_c3.proposals
    assert got_c3.included == orig_c3.included
    assert got_c3.deleted is False


def test_dropping_a_clip_is_rejected(tmp_path) -> None:
    store = _store(tmp_path)
    s1 = store.save(build_example())
    dropped = s1.model_copy(deep=True)
    dropped.clips = [c for c in dropped.clips if c.source_id != "s3"]  # drop instead of flag
    with pytest.raises(InvariantError):
        store.save(dropped)


def test_order_must_be_dense_and_unique(tmp_path) -> None:
    store = _store(tmp_path)
    bad = build_example()
    _clip(bad, "s2").order = 5  # leaves a gap: 1,3,5
    with pytest.raises(InvariantError):
        store.save(bad)


def test_clip_referencing_unknown_source_is_rejected(tmp_path) -> None:
    store = _store(tmp_path)
    bad = build_example()
    bad.clips[0].source_id = "ghost"
    with pytest.raises(InvariantError):
        store.save(bad)


def test_unknown_schema_version_on_load_raises(tmp_path) -> None:
    store = _store(tmp_path)
    path = tmp_path / "weird" / "project.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    with pytest.raises(SchemaVersionError):
        store.load("weird")
