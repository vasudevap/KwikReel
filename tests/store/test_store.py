"""WO-118 gates · persistence, optimistic concurrency, and the §3 invariants.

The §4.4 stickiness gate has two halves and both are tested. The **structural**
half — an assist cannot reach a user-owned field because the derivation stops
looking — is in `test_derive.py`. The **backstop** half, a save that tries it
anyway, is here.
"""

from __future__ import annotations

import json

import pytest

from backend.contracts.models import (
    Project,
    ReasonRecord,
    Segment,
    SegmentsProposal,
    SpeedRange,
)
from backend.store import (
    SUPPORTED_SCHEMA_VERSION,
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


def _reason(code: str = "RERUN") -> ReasonRecord:
    return ReasonRecord(
        code=code,
        human_text="re-proposed",
        evidence_refs=["signals.blur[0:1]"],
        score=0.4,
        confidence="med",
    )


def _proposal(segment: Segment, disposition: str) -> SegmentsProposal:
    return SegmentsProposal(
        value=segment,
        at="2026-07-29T09:00:00Z",
        reasons=[_reason()],
        disposition=disposition,
    )


# --- persistence ----------------------------------------------------------

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
    assert saved.created_at == original.created_at


def test_load_missing_project_raises(tmp_path) -> None:
    with pytest.raises(ProjectNotFoundError):
        _store(tmp_path).load("does-not-exist")


def test_optimistic_concurrency_conflict(tmp_path) -> None:
    store = _store(tmp_path)
    s1 = store.save(build_example())
    s2 = store.save(s1)                    # in-sync client: accepted
    assert s2.updated_at != s1.updated_at
    with pytest.raises(ConflictError):
        store.save(s1)                     # s1 is stale -> 409


def test_unknown_schema_version_on_load_raises(tmp_path) -> None:
    store = _store(tmp_path)
    path = tmp_path / "weird" / "project.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
    with pytest.raises(SchemaVersionError):
        store.load("weird")


def test_a_v1_document_is_refused_rather_than_migrated(tmp_path) -> None:
    # v1 described a materially different product. There are no migrations, so a
    # v1 file must fail loudly rather than load with fields quietly dropped.
    assert SUPPORTED_SCHEMA_VERSION == 2
    store = _store(tmp_path)
    path = tmp_path / "legacy" / "project.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "clips": []}), encoding="utf-8")
    with pytest.raises(SchemaVersionError):
        store.load("legacy")


def test_the_retired_v1_fields_appear_nowhere_on_disk(tmp_path) -> None:
    # §3.4: membership is derived. `out_s <= in_s` is how a clip leaves the reel,
    # and there is no boolean anywhere that says so.
    store = _store(tmp_path)
    saved = store.save(build_example())
    on_disk = (tmp_path / saved.project_id / "project.json").read_text(encoding="utf-8")
    document = json.loads(on_disk)

    for retired in ("included", "deleted", "stage_approvals", "audio_modes"):
        assert retired not in on_disk, f"{retired!r} survived into schema v2"

    binned = next(c for c in document["clips"] if c["source_id"] == "s3")
    assert binned["segment"]["out_s"] <= binned["segment"]["in_s"]
    assert set(binned["origin"]) == {"order", "segments", "speed", "audio"}


# --- §4.4 · the origin-protection backstop --------------------------------

def test_the_v1_attack_is_unrepresentable_in_v2(tmp_path) -> None:
    # v1's §4.4 risk was an assist writing a value straight into a clip field.
    # v2 ties `segment` to `origin == "user"`, so that document cannot exist —
    # the guarantee is a shape rule now, not a check someone has to run.
    store = _store(tmp_path)
    s1 = store.save(build_example())

    attack = s1.model_copy(deep=True)
    clip = _clip(attack, "s2")
    clip.segment = Segment(in_s=2.0, out_s=7.0)   # a "machine" trim
    clip.origin.segments = "proposed"
    with pytest.raises(InvariantError):
        store.save(attack)

    speed_attack = s1.model_copy(deep=True)
    clip = _clip(speed_attack, "s2")
    clip.speed_ranges = [SpeedRange(from_s=1.0, to_s=4.0, rate=2.0)]
    clip.origin.speed = "proposed"
    with pytest.raises(InvariantError):
        store.save(speed_attack)


def test_an_assist_may_not_take_a_user_owned_field_back(tmp_path) -> None:
    # What v2 *can* express: leaving the clip field empty and flipping the
    # origin, handing the field back to the derivation with nothing retained to
    # derive from. That is the assist overruling the user, and it is refused.
    store = _store(tmp_path)
    s1 = store.save(build_example())

    reclaim = s1.model_copy(deep=True)
    clip = _clip(reclaim, "s2")          # origin.segments == "user"
    clip.segment = None
    clip.origin.segments = "proposed"
    clip.proposals.segments = None
    with pytest.raises(OriginProtectionError):
        store.save(reclaim)


def test_nothing_proposes_an_order_or_an_audio_setting(tmp_path) -> None:
    # §3.2's `Proposals` carries segments and speed only, so those two origins
    # never read "proposed" — which is also why no assist can reclaim them.
    store = _store(tmp_path)
    for field in ("order", "audio"):
        bad = build_example()
        setattr(_clip(bad, "s2").origin, field, "proposed")
        with pytest.raises(InvariantError):
            store.save(bad)


def test_origin_proposed_requires_a_retained_proposal(tmp_path) -> None:
    store = _store(tmp_path)
    bad = build_example()
    _clip(bad, "s1").proposals.segments = None   # origin.segments stays "proposed"
    with pytest.raises(InvariantError):
        store.save(bad)


def test_an_explicit_rerun_hands_the_field_back_to_the_derivation(tmp_path) -> None:
    # §4.3's re-run key asks for a fresh proposal on one clip. In v2 that means
    # dropping the user's own value and letting the derivation read the new
    # proposal — the reclaim above, but with something retained behind it.
    store = _store(tmp_path)
    s1 = store.save(build_example())

    rerun = s1.model_copy(deep=True)
    clip = _clip(rerun, "s2")
    clip.segment = None
    clip.origin.segments = "proposed"
    clip.proposals.segments = _proposal(Segment(in_s=2.5, out_s=6.5), "pending")
    saved = store.save(rerun)
    assert _clip(saved, "s2").origin.segments == "proposed"
    assert _clip(saved, "s2").segment is None


# --- §3.2 / §3.4 · structural invariants ----------------------------------

def test_dropping_a_clip_is_rejected(tmp_path) -> None:
    store = _store(tmp_path)
    s1 = store.save(build_example())
    dropped = s1.model_copy(deep=True)
    dropped.clips = [c for c in dropped.clips if c.source_id != "s3"]
    with pytest.raises(InvariantError):
        store.save(dropped)


def test_order_must_be_dense_and_unique_across_every_clip(tmp_path) -> None:
    # v1 counted only non-deleted clips. v2 has no `deleted`: a clip that is out
    # of the reel still holds its place, so density spans all four — including
    # the binned s3 and the damaged s4.
    store = _store(tmp_path)
    bad = build_example()
    _clip(bad, "s2").order = 5           # 1, 3, 4, 5
    with pytest.raises(InvariantError):
        store.save(bad)

    duplicate = build_example()
    _clip(duplicate, "s2").order = 1
    with pytest.raises(InvariantError):
        store.save(duplicate)


def test_clip_referencing_unknown_source_is_rejected(tmp_path) -> None:
    store = _store(tmp_path)
    bad = build_example()
    bad.clips[0].source_id = "ghost"
    with pytest.raises(InvariantError):
        store.save(bad)


def test_a_segment_and_its_origin_must_agree(tmp_path) -> None:
    # §3.2: `segment` is the USER's trim, null unless origin says "user". Both
    # directions, because the §3.1 derivation has no fourth case to fall into.
    store = _store(tmp_path)

    orphan_value = build_example()
    _clip(orphan_value, "s1").segment = Segment(in_s=1.0, out_s=2.0)  # origin "proposed"
    with pytest.raises(InvariantError):
        store.save(orphan_value)

    orphan_origin = build_example()
    _clip(orphan_origin, "s1").origin.segments = "user"               # segment None
    with pytest.raises(InvariantError):
        store.save(orphan_origin)


def test_speed_ranges_on_a_clip_must_be_the_users(tmp_path) -> None:
    store = _store(tmp_path)
    bad = build_example()
    _clip(bad, "s1").speed_ranges = [SpeedRange(from_s=1.0, to_s=3.0, rate=1.5)]
    with pytest.raises(InvariantError):
        store.save(bad)


def test_a_user_may_own_the_speed_field_with_no_ramps(tmp_path) -> None:
    # The other direction is legitimate: "I removed the assist's ramps by hand,
    # and no assist may put them back."
    store = _store(tmp_path)
    ok = build_example()
    clip = _clip(ok, "s2")
    clip.speed_ranges = []
    clip.origin.speed = "user"
    assert _clip(store.save(ok), "s2").origin.speed == "user"


def test_malformed_speed_ranges_are_rejected(tmp_path) -> None:
    store = _store(tmp_path)

    zero_rate = build_example()
    _clip(zero_rate, "s2").speed_ranges = [SpeedRange(from_s=1.0, to_s=3.0, rate=0.0)]
    with pytest.raises(InvariantError):
        store.save(zero_rate)

    backwards = build_example()
    _clip(backwards, "s2").speed_ranges = [SpeedRange(from_s=3.0, to_s=1.0, rate=1.5)]
    with pytest.raises(InvariantError):
        store.save(backwards)

    # §3.4's played-duration formula is only well defined for disjoint ranges.
    overlapping = build_example()
    _clip(overlapping, "s2").speed_ranges = [
        SpeedRange(from_s=1.0, to_s=5.0, rate=1.5),
        SpeedRange(from_s=4.0, to_s=8.0, rate=2.0),
    ]
    with pytest.raises(InvariantError):
        store.save(overlapping)


def test_a_proposal_carrying_overlapping_ranges_is_rejected_too(tmp_path) -> None:
    # A proposal's value can become the effective speed, so it faces the same rule.
    store = _store(tmp_path)
    bad = build_example()
    _clip(bad, "s2").proposals.speed.value = [
        SpeedRange(from_s=1.0, to_s=5.0, rate=1.6),
        SpeedRange(from_s=3.0, to_s=9.0, rate=1.8),
    ]
    with pytest.raises(InvariantError):
        store.save(bad)
